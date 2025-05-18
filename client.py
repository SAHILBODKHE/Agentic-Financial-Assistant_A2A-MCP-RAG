# pip install llama-index llama-index-llms-ollama llama-index-tools-mcp langchain-community
import asyncio
import sys
import os
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import ReActAgent
from llama_index.llms.ollama import Ollama
from prompt_templates import BANK_CHATBOT_PROMPT  # You will define this

# Configuration variables
MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:3005/sse")
MODEL_NAME = os.environ.get("LLM_MODEL", "llama3.2")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

async def setup_agent():
    """Setup and return the bank assistant agent"""
    try:
        print(f"🔌 Connecting to MCP server at {MCP_URL}")
        mcp_client = BasicMCPClient(MCP_URL)

        print("🔍 Fetching available banking tools...")
        tools = await McpToolSpec(client=mcp_client).to_tool_list_async()
        print(f"🛠️ Found {len(tools)} tools")

        print(f"🧠 Initializing Ollama with model {MODEL_NAME}...")
        llm = Ollama(model=MODEL_NAME, temperature=TEMPERATURE)

        # system_prompt = BANK_CHATBOT_PROMPT.template.replace("{tools}", "").replace("{tool_names}", "").replace("{input}", "")
        # agent = ReActAgent(
        #     name="BankBot",
        #     llm=llm,
        #     tools=tools,
        #     system_prompt=system_prompt,
        #     temperature=TEMPERATURE
        # )
        system_prompt = BANK_CHATBOT_PROMPT.template.replace("{tools}", "").replace("{tool_names}", "").replace("{input}", "")
        agent = ReActAgent(
            name="BankBot",
            llm=llm,
            tools=tools,
            system_prompt=system_prompt,
            temperature=TEMPERATURE
        )

        return agent
    except Exception as e:
        print(f"❌ Error setting up agent: {e}")
        raise

async def main():
    print("\n🏦 Welcome to the AI Bank Assistant 🏦")
    print("-" * 50)
    print("Ask me anything about your bank accounts!")
    print("Examples:")
    print("  • What's my account balance?")
    print("  • Transfer $200 to John")
    print("  • Show me recent transactions")
    print("\nType 'exit' or 'quit' to end the session.")
    print("-" * 50)

    print("✅ Make sure the bank MCP server is running with:")
    print("mcp-bank-chatbot --connection_type http")

    try:
        agent = await setup_agent()
        print("💼 BankBot is ready to assist you!")

        while True:
            user_query = input("\n🧾 Your request: ")

            if user_query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Thank you for using the Bank Assistant. Goodbye!")
                break

            if user_query.strip():
                print("🕵️ Processing your request...")
                try:
                    response = await agent.run(user_query)
                    print(f"\n📣 {response}")
                except Exception as e:
                    print(f"⚠️ Error processing query: {e}")

    except Exception as e:
        print(f"🚨 Error: {e}")
        print(f"Ensure the bank MCP server is running at {MCP_URL}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
