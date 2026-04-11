import requests

RAG_URL = "http://127.0.0.1:8001/rag-query"

def ask_ai(query):
    try:
        res = requests.post(RAG_URL, json={"query": query})
        return res.json()
    except Exception as e:
        return {"error": str(e)}