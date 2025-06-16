# ------------------ mcp_client_api.py ------------------
import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import ReActAgent
from llama_index.llms.ollama import Ollama
from prompt_templates import BANK_CHATBOT_PROMPT
from fastapi.middleware.cors import CORSMiddleware

# Configuration
MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:3009/sse")
MODEL_NAME = os.environ.get("LLM_MODEL", "llama3.2")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = None

# Request body
class Query(BaseModel):
    query: str
    thread_id: str  # New field

@app.on_event("startup")
async def initialize_agent():
    global agent
    try:
        print(f"🔌 Connecting to MCP server at {MCP_URL}")
        mcp_client = BasicMCPClient(MCP_URL)

        print("🔍 Fetching available tools...")
        tools = await McpToolSpec(client=mcp_client).to_tool_list_async()
        print(f"🛠️ Found {len(tools)} tools")

        print(f"🧠 Initializing Ollama with model '{MODEL_NAME}'...")
        llm = Ollama(model=MODEL_NAME, temperature=TEMPERATURE, stream=False)

        # Prompt with placeholder injection (if needed)
        tool_names = ", ".join([tool.metadata.name for tool in tools])
        system_prompt = BANK_CHATBOT_PROMPT.template \
            .replace("{tool_names}", tool_names) \
            .replace("{input}", "")

        agent = ReActAgent(
            name="BankBot",
            llm=llm,
            tools=tools,
            temperature=TEMPERATURE,
            stream=False
        )

        print("✅ Agent initialized.")
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        raise

@app.get("/ping")
async def ping():
    return {"status": "BankBot is alive"}

@app.post("/ask")
async def ask_query(data: Query):
    print(f"📨 Incoming query: {data.query} (thread_id: {data.thread_id})")
    try:
        mcp_client = BasicMCPClient(MCP_URL)

        response = await mcp_client.call_tool(
            "drafter_tool",
            {"user_instruction": data.query},
            {"configurable": {"thread_id": data.thread_id}}
        )

        print(f"🧾 MCP tool response: {response}")
        print(f"🔎 Dir: {dir(response)}")

        return {"response": str(response)}

    except Exception as e:
        print(f"🛑 Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")



# Run standalone
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000, reload=True)
