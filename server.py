from mcp.server.fastmcp import FastMCP
from retriever import get_relevant_documents
from llama_model import ask_ollama
mcp = FastMCP("BankChatService", port=3007)  # pass port here

@mcp.tool()
async def check_balance(account_id: str) -> dict:
    return {"account_id": account_id, "balance": "$5,000"}

@mcp.tool()
async def transfer_funds(from_account: str, to_account: str, amount: float) -> dict:
    return {"status": "success", "message": f"Transferred ${amount} to {to_account}"}

@mcp.tool()
async def transaction_history(account_id: str, start_date: str, end_date: str) -> dict:
    return {"transactions": [
        {"date": "2025-05-01", "amount": "-$100", "desc": "Grocery"},
        {"date": "2025-17-05", "amount": "+$500", "desc": "Salary"},
    ]}

@mcp.tool()
async def insurance_question(query):
    docs = get_relevant_documents(query)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    prompt = f"""
    You are a helpful insurance assistant. Use the context below to answer the user's question based strictly on

    Context:
    {context}

    Question: {query}
    Answer:
    """
    response = ask_ollama(prompt.strip())
    print("\n💬 Answer:", response)
    return response

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Bank Chatbot Server")
    parser.add_argument(
        "--connection_type",
        type=str,
        default="sse",
        choices=["http", "stdio", "sse"],
    )
    args = parser.parse_args()

    print(f"Starting Bank Chatbot Service on port 3007 with {args.connection_type} connection")

    mcp.run(args.connection_type)  # no host or port here
