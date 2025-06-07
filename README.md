# Bankbot
Run LLAMA using :

ollama run llama3.2

python server.py --connection_type sse

uvicorn client:app --port 4000
