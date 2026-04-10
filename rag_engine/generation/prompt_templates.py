def build_prompt(query, context_docs):
    context = "\n".join(context_docs)

    prompt = f"""
You are a real estate AI assistant.

Context:
{context}

Question:
{query}

Give concise insights about land prices, trends, and recommendations.
"""
    return prompt