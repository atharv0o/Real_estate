import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "ai_service"))

from dotenv import load_dotenv
load_dotenv("ai_service/.env")

from rag.vectorstore import add_property
from blockchain.algorand import anchor

DATA_FILE = Path("ai_service/data/properties.json")

def run():
    props = json.loads(DATA_FILE.read_text())
    for i, prop in enumerate(props):
        print(f"[{i+1}/{len(props)}] Ingesting {prop['id']}...")
        
        # 1. Embed into FAISS
        add_property(prop)
        
        # 2. Anchor to Algorand
        txid = anchor(prop["id"], {
            "price": prop["price"],
            "location": prop["location"],
            "scraped_at": prop["scraped_at"]
        })
        prop["algo_txn_id"] = txid
        print(f"   Anchored: {txid}")
    
    # Save txn IDs back to JSON
    DATA_FILE.write_text(json.dumps(props, indent=2))
    print("Done. FAISS index and Algorand anchors updated.")

if __name__ == "__main__":
    run()