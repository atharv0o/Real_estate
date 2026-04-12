from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ Groq LLM via OpenAI-compatible API
llm = None


def _get_llm():
    global llm
    if llm is not None:
        return llm

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    llm = ChatOpenAI(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.2,
    )
    return llm


def generate_response(prompt: str):
    client = _get_llm()
    if client is None:
        return "RAG context is available, but GROQ_API_KEY is missing so generation is running in fallback mode."
    response = client.invoke(prompt)
    return response.content
