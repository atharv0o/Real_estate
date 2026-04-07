import os, hashlib, json
from algosdk import transaction, mnemonic, account
from algosdk.v2client import algod

NODE_URL   = os.getenv("ALGORAND_NODE_URL", "https://testnet-api.algonode.cloud")
NODE_TOKEN = os.getenv("ALGORAND_NODE_TOKEN", "")
MNEMONIC   = os.getenv("ALGORAND_MNEMONIC")

def _client():
    return algod.AlgodClient(NODE_TOKEN, NODE_URL)

def _sender():
    pk = mnemonic.to_private_key(MNEMONIC)
    addr = account.address_from_private_key(pk)
    return pk, addr

def anchor(property_id: str, data: dict) -> str:
    """Write property hash to Algorand. Returns txn ID."""
    client = _client()
    pk, addr = _sender()
    
    payload = json.dumps({"id": property_id, **data}, sort_keys=True)
    data_hash = hashlib.sha256(payload.encode()).hexdigest()
    note = f"PROPSIGHT:{property_id}:{data_hash}".encode()
    
    params = client.suggested_params()
    txn    = transaction.PaymentTxn(addr, params, addr, 0, note=note)
    signed = txn.sign(pk)
    txid   = client.send_transaction(signed)
    transaction.wait_for_confirmation(client, txid, 4)
    return txid

def verify(txn_id: str) -> dict:
    """Fetch txn from Algorand and return verified timestamp."""
    client = _client()
    info   = client.pending_transaction_info(txn_id)
    note   = bytes(info["txn"]["txn"].get("note", [])).decode("utf-8", errors="ignore")
    return {
        "txn_id": txn_id,
        "note": note,
        "confirmed_round": info.get("confirmed-round"),
        "explorer_url": f"https://testnet.algoexplorer.io/tx/{txn_id}"
    }