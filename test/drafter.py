# drafter.py
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from fastapi.concurrency import run_in_threadpool
from mcp.server.fastmcp import FastMCP
import os, uuid, json
from datetime import datetime

# === MCP Server ===
mcp = FastMCP("DrafterService", port=3009)

# === Versioned Storage ===
BASE_DIR = "my_dir"
os.makedirs(BASE_DIR, exist_ok=True)

def user_path(user_id: str):
    path = os.path.join(BASE_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path

def current_file(user_id: str, thread_id: str):
    return os.path.join(user_path(user_id), f"{thread_id}_current.json")

def version_file(user_id: str, thread_id: str, version_id: str):
    return os.path.join(user_path(user_id), f"{thread_id}_{version_id}.json")

def save_version(user_id: str, thread_id: str, content: str) -> str:
    version_id = datetime.now().strftime("v%Y%m%d_%H%M%S")
    file_path = version_file(user_id, thread_id, version_id)
    data = {
        "content": content,
        "created_at": datetime.now().isoformat(),
        "version_id": version_id,
        "user_id": user_id,
        "thread_id": thread_id
    }
    with open(file_path, "w") as f:
        json.dump(data, f)
    with open(current_file(user_id, thread_id), "w") as f:
        json.dump({"current": file_path}, f)
    return version_id

def load_current(user_id: str, thread_id: str):
    path = current_file(user_id, thread_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        pointer = json.load(f)["current"]
    if os.path.exists(pointer):
        with open(pointer) as vf:
            return json.load(vf)
    return None

def list_versions(user_id: str, thread_id: str):
    return sorted([
        f for f in os.listdir(user_path(user_id))
        if f.startswith(thread_id + "_v") and f.endswith(".json")
    ])

def restore_version(user_id: str, thread_id: str, version_id: str):
    path = version_file(user_id, thread_id, version_id)
    if os.path.exists(path):
        with open(current_file(user_id, thread_id), "w") as f:
            json.dump({"current": path}, f)
        return True
    return False

# === LangGraph State ===
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# === Tools ===
@tool
def update(content: str, user_id: str, thread_id: str) -> str:
    """Update the user's draft and create a new version."""
    version_id = save_version(user_id, thread_id, content)
    return f"✅ Draft updated as {version_id}.\n\n{content}"

@tool
def save(filename: str, user_id: str, thread_id: str) -> str:
    """Save the latest version to a .txt file."""
    current = load_current(user_id, thread_id)
    if not current:
        return "❌ No draft found."
    if not filename.endswith(".txt"):
        filename += ".txt"
    with open(filename, "w") as f:
        f.write(current["content"])
    return f"💾 Saved as '{filename}'"

@tool
def get_draft(user_id: str, thread_id: str) -> str:
    """Return the current draft content."""
    current = load_current(user_id, thread_id)
    if current:
        return f"📄 Current version: {current['version_id']}\n\n{current['content']}"
    return "❌ No current draft found."

@tool
def revert(user_id: str, thread_id: str, version_id: str) -> str:
    """Restore a specific version by ID."""
    success = restore_version(user_id, thread_id, version_id)
    return f"✅ Restored version {version_id}." if success else f"❌ Version {version_id} not found."

@tool
def history(user_id: str, thread_id: str) -> str:
    """List all previous versions."""
    return "\n".join(list_versions(user_id, thread_id))

# === Model & Agent ===
tools = [update, save, get_draft, revert, history]
model = ChatOllama(model="llama3.2", base_url="http://localhost:11434").bind_tools(tools)

def agent_logic(state: AgentState, config: dict) -> AgentState:
    user_id = config["configurable"].get("user_id", "anonymous")
    thread_id = config["configurable"].get("thread_id", str(uuid.uuid4()))
    current = load_current(user_id, thread_id)
    content = current["content"] if current else ""

    system = SystemMessage(content=f"""
You are a document drafting assistant.

Instructions:
- Always use 'update' to revise content.
- Use 'save' to store the file.
- Use 'get_draft' to show the draft.
- Use 'revert' to restore a previous version.
- Use 'history' to show saved versions.

Current Draft:
{content}
""")

    user_msg = state["messages"][-1]
    response = model.invoke([system, user_msg])
    return {"messages": [response]}

# === LangGraph ===
graph = StateGraph(AgentState)
graph.add_node("agent", agent_logic)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("agent")
graph.add_edge("agent", "tools")
graph.add_edge("tools", END)
app = graph.compile()

# === Runner ===
def run_drafter(user_input: str, user_id: str, thread_id: str):
    state = {"messages": [HumanMessage(content=user_input)]}
    config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}
    for step in app.stream(state, config=config, stream_mode="values"):
        for msg in step.get("messages", []):
            if isinstance(msg, ToolMessage):
                current = load_current(user_id, thread_id)
                return {
                    "output": msg.content,
                    "status": "done",
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "version": current["version_id"] if current else None
                }
    return {"output": "No response generated", "status": "error"}

@mcp.tool()
async def drafter_tool(user_instruction: str, user_id: str, thread_id: str):
    return await run_in_threadpool(run_drafter, user_instruction, user_id, thread_id)

if __name__ == "__main__":
    mcp.run("sse")