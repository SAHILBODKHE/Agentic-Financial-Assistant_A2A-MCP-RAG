# ------------------ drafter1.py ------------------
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from fastapi.concurrency import run_in_threadpool
from mcp.server.fastmcp import FastMCP

# === MCP server initialization ===
mcp = FastMCP("DrafterService", port=3009)

# === Global content holder ===
document_content = ""

# === LangGraph State ===
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# === Tools ===
@tool
def update(content: str) -> str:
    """Update the document with the provided content."""
    global document_content
    document_content = content
    return (
        f"✅ Document updated. Current content:\n{document_content}\n\n"
        f"💡 You can now say things like:\n- 'edit the tone'\n- 'save as draft.txt'"
    )

@tool
def save(filename: str) -> str:
    """Save the current document to a text file."""
    global document_content
    if not filename.endswith(".txt"):
        filename += ".txt"
    try:
        with open(filename, "w") as f:
            f.write(document_content)
        return f"💾 Document saved successfully as '{filename}'."
    except Exception as e:
        return f"❌ Failed to save document: {str(e)}"


# Tool list
tools = [update, save]

# Chat model
model = ChatOllama(
    model="llama3.2",
    temperature=0.7,
    base_url="http://localhost:11434"
).bind_tools(tools)

# Agent logic
def our_agent(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(content=f"""
You are Drafter, a helpful assistant for writing and editing documents.

- Use 'update' to write or revise content. Always include full content.
- Use 'save' if the user wants to store the document.
- Always respond using tools.
- Do not respond directly with text — only use tool calls.
- The current document is shown below.

Current document:
{document_content}
""")

    user_message = state["messages"][-1]
    messages = [system_prompt] + list(state["messages"])
    response = model.invoke(messages)
    return {"messages": state["messages"] + [user_message, response]}

# Conditional flow control
def should_continue(state: AgentState) -> str:
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage):
            if "updated" in msg.content.lower() or "saved" in msg.content.lower():
                return "end"
    return "continue"

# Build graph
graph = StateGraph(AgentState)
graph.add_node("agent", our_agent)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("agent")
graph.add_edge("agent", "tools")
graph.add_conditional_edges("tools", should_continue, {"continue": "agent", "end": END})
app = graph.compile()

# Run one session
def run_drafter_session(user_input: str, config: dict) -> dict:
    state = {"messages": [HumanMessage(content=user_input)]}
    result = ""
    is_done = False
    for step in app.stream(state, config=config, stream_mode="values"):
        for msg in step.get("messages", []):
            if isinstance(msg, ToolMessage):
                result = msg.content
                if "saved" in result.lower() or "updated" in result.lower():
                    is_done = True
    return {
        "output": result or "No output generated.",
        "status": "done" if is_done else "waiting"
    }

# MCP-compatible tool
@mcp.tool()
async def drafter_tool(user_instruction: str, config: dict = None) -> dict:
    """
    MCP-compatible tool to run one round of the Drafter assistant.
    """
    try:
        if not isinstance(user_instruction, str) or not user_instruction.strip():
            return {
                "output": "❌ 'user_instruction' must be a non-empty string.",
                "status": "error"
            }

        config = config or {"configurable": {"thread_id": "default"}}
        return await run_in_threadpool(run_drafter_session, user_instruction, config)

    except Exception as e:
        return {
            "output": f"❌ Internal error in drafter_tool: {str(e)}",
            "status": "error"
        }


# Main entrypoint
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection_type", type=str, default="sse", choices=["http", "stdio", "sse"])
    args = parser.parse_args()

    print(f"🚀 DrafterService running on port 3009 via {args.connection_type}")
    mcp.run(args.connection_type)

