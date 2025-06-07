import requests

def ask_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:latest",  # ← your exact model name from `ollama list`
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        data = response.json()
        if "response" in data:
            return data["response"]
        else:
            print("⚠️ Unexpected response format from Ollama:", data)
            return "Ollama didn't return a valid response."
    except Exception as e:
        print("🔥 Error communicating with Ollama:", str(e))
        return "Failed to connect to Ollama or model not running."
