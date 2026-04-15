def build_prompt(query, context_docs, location: str | None = None, property_context: str | None = None):
    context = "\n".join(context_docs)
    location_text = location or "unspecified location"
    property_context_text = property_context or "No property-specific context was provided."

    prompt = f"""
You are a real estate AI assistant.

Generate insights ONLY for the given location: {location_text}
DO NOT use default or cached city.

Property-specific context:
{property_context_text}

Retrieved context:
{context}

Question:
{query}

Give concise insights about land prices, trends, and recommendations for the given location only.
"""
    return prompt
