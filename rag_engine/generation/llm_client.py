from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ Groq LLM via OpenAI-compatible API
llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0.2,
)

def generate_response(prompt: str):
    response = llm.invoke(prompt)
    return response.content