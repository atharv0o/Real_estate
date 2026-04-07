import faiss, json, numpy as np
from pathlib import Path
from .embedder import embed_texts

INDEX_DIR  = Path(__file__).parent.parent / "data" / "faiss_index"
INDEX_PATH = INDEX_DIR / "index.faiss"
META_PATH  = INDEX_DIR / "meta.json"

# Create folder if it doesn't exist
INDEX_DIR.mkdir(parents=True, exist_ok=True)

_index = None
_meta  = []

def load_index():
    global _index, _meta
    if INDEX_PATH.exists():
        _index = faiss.read_index(str(INDEX_PATH))
        _meta  = json.loads(META_PATH.read_text())

def search(query: str, k: int = 5) -> list[dict]:
    if _index is None or _index.ntotal == 0:
        return []
    vec = np.array(embed_texts([query]), dtype="float32")
    _, idxs = _index.search(vec, k)
    return [_meta[i] for i in idxs[0] if i < len(_meta)]

def add_property(prop: dict):
    # Call this during ingestion
    global _index, _meta
    text = f"{prop['title']} {prop['location']} {prop['type']} {prop['price_label']}"
    vec  = np.array(embed_texts([text]), dtype="float32")
    if _index is None:
        _index = faiss.IndexFlatL2(vec.shape[1])
    _index.add(vec)
    _meta.append(prop)
    faiss.write_index(_index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(_meta, indent=2))