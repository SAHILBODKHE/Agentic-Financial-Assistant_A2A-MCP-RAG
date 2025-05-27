# Bankbot
Run LLAMA using :
ollama run llama3.2
uvicorn mcp_server.main:app --reload --port 8000
python3 client.py
