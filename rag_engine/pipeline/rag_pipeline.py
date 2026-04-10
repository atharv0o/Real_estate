from embeddings.embedder import get_embeddings
from embeddings.vector_store import VectorStore
from retrieval.retriever import retrieve
from generation.llm_client import generate_response
from generation.prompt_templates import build_prompt

# Initialize global store
vector_store = VectorStore()

# Sample data (replace later with DB or pipeline)
sample_docs = [
    "Land prices in Ichalkaranji are increasing rapidly.",
    "Average land cost is 5000 per sq ft in urban areas.",
    "Plots near highways have higher appreciation.",
    "Rural land is cheaper but slower growth.",
]

# Preload embeddings
embeddings = get_embeddings(sample_docs)
vector_store.add(embeddings, sample_docs)


def run_rag(query):
    # Step 1: Retrieve
    docs = retrieve(query, vector_store)

    # Step 2: Build prompt
    prompt = build_prompt(query, docs)

    # Step 3: Generate
    response = generate_response(prompt)

    return response