from embeddings.embedder import get_embeddings

def retrieve(query, vector_store):
    query_embedding = get_embeddings([query])[0]
    results = vector_store.search(query_embedding)
    return results