import requests

def call_rag(query):
    res = requests.post(
        "http://localhost:8001/rag-query",
        json={"query": query}
    )
    return res.json()