# # ------------------ client1.py ------------------
# import os
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from llama_index.tools.mcp import BasicMCPClient
# from fastapi.middleware.cors import CORSMiddleware

# # === Configuration ===
# MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:3009/sse")

# # === FastAPI App ===
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # === Request Model ===
# class Query(BaseModel):
#     query: str
#     user_id: str
#     thread_id: str

# # === Health Check ===
# @app.get("/ping")
# async def ping():
#     return {"status": "MCP client is alive"}

# # === Ask Endpoint ===
# @app.post("/ask")
# async def ask_query(data: Query):
#     print(f"📨 Incoming query: {data.query} (user_id: {data.user_id}, thread_id: {data.thread_id})")

#     try:
#         mcp_client = BasicMCPClient(MCP_URL)

#         # === Make MCP call ===
#         result = await mcp_client.call_tool(
#             "drafter_tool",
#             {
#                 "user_instruction": data.query,
#                 "user_id": data.user_id,
#                 "thread_id": data.thread_id
#             },
#             {
#                 "configurable": {
#                     "user_id": data.user_id,
#                     "thread_id": data.thread_id
#                 }
#             }
#         )

#         # === Normalize result based on version ===
#         if isinstance(result, dict):
#             output_data = result
#         elif hasattr(result, "output") and isinstance(result.output, dict):
#             output_data = result.output
#         elif hasattr(result, "__dict__"):  # Try convert via dict wrapper
#             output_data = dict(result.__dict__)
#         else:
#             raise ValueError("Expected result to be a dictionary or contain output.")

#         return {
#             "response": output_data.get("output"),
#             "status": output_data.get("status"),
#             "user_id": output_data.get("user_id", data.user_id),
#             "thread_id": output_data.get("thread_id", data.thread_id),
#             "version": output_data.get("version")
#         }

#     except Exception as e:
#         print(f"🛑 MCP call failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# # === Run Standalone ===
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=4000, reload=True)
# ------------------ client1.py ------------------
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_index.tools.mcp import BasicMCPClient
from fastapi.middleware.cors import CORSMiddleware

# === Configuration ===
MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:3009/sse")

# === FastAPI App ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Request Model ===
class Query(BaseModel):
    query: str
    user_id: str
    thread_id: str

# === Health Check ===
@app.get("/ping")
async def ping():
    return {"status": "MCP client is alive"}

# === Ask Endpoint ===
import json  # Add this at the top

@app.post("/ask")
async def ask_query(data: Query):
    print(f"📨 Incoming query: {data.query} (user_id: {data.user_id}, thread_id: {data.thread_id})")

    try:
        mcp_client = BasicMCPClient(MCP_URL)

        result = await mcp_client.call_tool(
            "drafter_tool",
            {
                "user_instruction": data.query,
                "user_id": data.user_id,
                "thread_id": data.thread_id
            },
            {
                "configurable": {
                    "user_id": data.user_id,
                    "thread_id": data.thread_id
                }
            }
        )

        # ✅ Fix: parse .content[0].text as JSON
        if hasattr(result, "content") and result.content:
            content_text = result.content[0].text
            output_data = json.loads(content_text)
        else:
            raise ValueError(f"Expected result.content to contain a valid text response: {result}")

        return {
            "response": output_data.get("output"),
            "status": output_data.get("status"),
            "user_id": data.user_id,
            "thread_id": data.thread_id,
            "version": output_data.get("version")
        }

    except Exception as e:
        print(f"🛑 MCP call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")



# === Run Standalone ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000, reload=True)
