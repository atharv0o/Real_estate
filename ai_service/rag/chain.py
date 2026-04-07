import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from .vectorstore import search

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2,
)

PROMPT = PromptTemplate.from_template("""
You are a real estate intelligence assistant for India.
Use ONLY the property listings below to answer the query.
Be concise. Mention price, location, BHK, and verified status.

LISTINGS:
{context}

USER QUERY: {query}

ANSWER:
""")

def query_properties(user_query: str) -> dict:
    results = search(user_query, k=5)
    if not results:
        return {"answer": "No matching properties found.", "properties": []}
    
    context = "\n".join([
        f"- {p['title']} | {p['location']} | {p['price_label']} | "
        f"Verified: {p.get('algo_txn_id','No')}"
        for p in results
    ])
    
    chain   = PROMPT | llm
    answer  = chain.invoke({"context": context, "query": user_query})
    return {"answer": answer.content, "properties": results}