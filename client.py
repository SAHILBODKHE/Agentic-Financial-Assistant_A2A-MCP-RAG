import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import ReActAgent
from llama_index.llms.ollama import Ollama
from prompt_templates import BANK_CHATBOT_PROMPT

# Configuration
MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:3007/sse")
MODEL_NAME = os.environ.get("LLM_MODEL", "llama3.2")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

# FastAPI app
app = FastAPI()
agent = None

class Query(BaseModel):
    query: str

@app.on_event("startup")
async def initialize_agent():
    global agent
    try:
        print(f"🔌 Connecting to MCP server at {MCP_URL}")
        mcp_client = BasicMCPClient(MCP_URL)

        print("🔍 Fetching available banking tools...")
        tools = await McpToolSpec(client=mcp_client).to_tool_list_async()
        print(f"🛠️ Found {len(tools)} tools")

        print(f"🧠 Initializing Ollama with model '{MODEL_NAME}'...")
        llm = Ollama(model=MODEL_NAME, temperature=TEMPERATURE, stream=False)

        # Inject tool names into the prompt
        tool_names = ", ".join([tool.metadata.name for tool in tools])
        system_prompt = BANK_CHATBOT_PROMPT.template \
            .replace("{tool_names}", tool_names) \
            .replace("{input}", "")  # {input} will be passed at runtime

        agent = ReActAgent(
            name="BankBot",
            llm=llm,
            tools=tools,
            system_prompt=system_prompt,
            temperature=TEMPERATURE,
            stream=False
        )
        print("✅ BankBot agent initialized.")
    except Exception as e:
        print(f"❌ Error during agent setup: {e}")
        raise

@app.get("/ping")
async def ping():
    return {"status": "BankBot is alive"}

@app.post("/ask")
async def ask_query(data: Query):
    print(f"📨 Incoming query: {data.query}")
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        trimmed_input = data.query.strip()[:1000]
        response = await agent.run(trimmed_input)

        # 🧼 Step: Clean up internal thoughts if any
        final = str(response).strip()
        if final.lower().startswith("thought:") or "thought:" in final.lower():
            # Simple heuristic cleanup
            import re
            clean_msg = re.sub(r"(?i)thought:.*?(observation:)?", "", final)
            clean_msg = clean_msg.strip().lstrip(":").strip()
            if not clean_msg:
                clean_msg = "✅ Your account balance is ready. Please check your dashboard."
            return {"response": clean_msg}

        return {"response": final}

    except Exception as e:
        print(f"🛑 Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000, reload=True)
