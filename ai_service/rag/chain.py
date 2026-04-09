import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from .vectorstore import search

# DeepSeek via OpenAI-compatible API
llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",  # current Groq model
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0.2,
)

PROMPT = PromptTemplate.from_template("""
You are a real estate assistant for India.
Use the property listings below to answer the query.
If listings don't exactly match, suggest the closest available options.

LISTINGS:
{context}

USER QUERY: {query}

ANSWER:
""")

def query_properties(user_query: str) -> dict:
    results = search(user_query, k=5)

    if not results:
        return {
            "answer": "No matching properties found.",
            "properties": []
        }

    context = "\n".join([
        f"- {p['title']} | {p['location']} | {p['price_label']} | "
        f"Verified: {p.get('algo_txn_id', 'No')}"
        for p in results
    ])

    chain = PROMPT | llm
    answer = chain.invoke({
        "context": context,
        "query": user_query
    })

    return {
        "answer": answer.content,
        "properties": results
    }