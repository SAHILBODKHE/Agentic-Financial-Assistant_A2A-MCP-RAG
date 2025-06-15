from retriever import get_relevant_documents
from llama_model import ask_ollama
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, AIMessage
from fastapi.concurrency import run_in_threadpool

from mcp.server.fastmcp import FastMCP
from drafter1 import run_drafter_session  # 🆕 Import the drafter tool
from drafter1 import drafter_tool, DrafterToolInput

# ✅ Define the graph state schema
class State(TypedDict):
    messages: Annotated[list, add_messages]

# ✅ Initialize LangGraph builder
graph_builder = StateGraph(State)

# ✅ Initialize ChatOllama LLM
llm = ChatOllama(
    model="llama3",
    temperature=0.7,
    base_url="http://localhost:11434",
)

# ✅ MCP instance
mcp = FastMCP("BankChatService", port=3007)

# @mcp.tool()
# async def email_drafter_tool(user_instruction: str) -> dict:
#     result = await run_in_threadpool(run_drafter_session, user_instruction)
#     return {"result": result}



@mcp.tool()
async def drafter_tool(input: DrafterToolInput) -> dict:
    """
    Handles one turn of document editing via Drafter agent.
    """
    try:
        instruction = input["user_instruction"]
        result = await run_in_threadpool(run_drafter_session, instruction)
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}






# # ✅ Banking tools
# @mcp.tool()
# async def check_balance(account_id: str) -> dict:
#     return {"account_id": account_id, "balance": "$5,000"}

# @mcp.tool()
# async def transfer_funds(from_account: str, to_account: str, amount: float) -> dict:
#     return {"status": "success", "message": f"Transferred ${amount} to {to_account}"}

# @mcp.tool()
# async def transaction_history(account_id: str, start_date: str, end_date: str) -> dict:
#     return {
#         "transactions": [
#             {"date": "2025-05-01", "amount": "-$100", "desc": "Grocery"},
#             {"date": "2025-17-05", "amount": "+$500", "desc": "Salary"},
#         ]
#     }

# # ✅ LangGraph node for insurance Q&A
# def insurance_question(state: State) -> State:
#     latest_msg = state["messages"][-1]
#     latest_input = latest_msg.content

#     docs = get_relevant_documents(latest_input)
#     context = "\n\n".join([doc.page_content for doc in docs])

#     prompt = f"""
# You are a helpful insurance assistant. Use the context below to answer the user's question strictly based on it.

# Context:
# {context}

# Question: {latest_input}
# Answer:
# """.strip()

#     response = ask_ollama(prompt)
#     return {"messages": state["messages"] + [AIMessage(content=response)]}

# # ✅ LangGraph node for summarization
# def summarizer(state: State) -> State:
#     latest_msg = state["messages"][-1]
#     context = latest_msg.content
#     user_message = state["messages"][0].content

#     prompt = f"""
# You are an intelligent assistant which summarizes the most optimized information into points given the 
# Context:
# {context}
# and user question: {user_message}
# Answer:
# """.strip()

#     response = ask_ollama(prompt)
#     return {"messages": state["messages"] + [AIMessage(content=response)]}

# # ✅ Add nodes to LangGraph
# graph_builder.add_node("infobot", insurance_question)
# graph_builder.add_node("summarybot", summarizer)
# graph_builder.add_edge(START, "infobot")
# graph_builder.add_edge("infobot", "summarybot")
# graph = graph_builder.compile()

# # ✅ Stream updates for LangGraph insurance Q&A
# def stream_graph_updates(user_input: str):
#     print("Assistant:", end=" ", flush=True)
#     final_msg = []
#     for event in graph.stream({"messages": [HumanMessage(content=user_input)]}):
#         for value in event.values():
#             msg = value["messages"][-1].content
#             print(msg, end="", flush=True)
#             final_msg.append(msg)
#     print(f"\n Final Message: {final_msg[-1]}")
#     return final_msg[-1]

# # ✅ Insurance Q&A tool
# @mcp.tool()
# async def insurance_questions(query: str):
#     result = await run_in_threadpool(stream_graph_updates, query)
#     return {"answer": result}



# ✅ Start the MCP service
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Bank Chatbot Service")
    parser.add_argument(
        "--connection_type",
        type=str,
        default="sse",
        choices=["http", "stdio", "sse"],
    )
    args = parser.parse_args()

    print(f"Starting Bank Chatbot Service on port 3007 with {args.connection_type} connection")
    mcp.run(args.connection_type)
