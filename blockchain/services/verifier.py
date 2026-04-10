import os
import json
import hashlib
from dotenv import load_dotenv

from algosdk import transaction, mnemonic
from algosdk.v2client import algod

# Load environment variables
load_dotenv()

# -------------------------------
# 🔹 Algorand Client Setup
# -------------------------------
ALGOD_ADDRESS = os.getenv("ALGORAND_NODE_URL")
ALGOD_TOKEN = os.getenv("ALGORAND_NODE_TOKEN")
MNEMONIC = os.getenv("ALGORAND_MNEMONIC")

def get_algod_client():
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)


def get_private_key():
    return mnemonic.to_private_key(MNEMONIC)


def get_address(private_key):
    return transaction.account.address_from_private_key(private_key)


# -------------------------------
# 🔹 HASH FUNCTION
# -------------------------------
def generate_hash(data: dict):
    """
    Generate SHA256 hash of property data
    """
    data_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()


# -------------------------------
# 🔹 SEND TO BLOCKCHAIN
# -------------------------------
def send_to_blockchain(hash_value: str):
    """
    Store hash on Algorand blockchain (note field)
    """
    try:
        algod_client = get_algod_client()

        private_key = get_private_key()
        sender_address = get_address(private_key)

        params = algod_client.suggested_params()

        txn = transaction.PaymentTxn(
            sender=sender_address,
            sp=params,
            receiver=sender_address,  # self transfer
            amt=0,
            note=hash_value.encode()
        )

        signed_txn = txn.sign(private_key)

        tx_id = algod_client.send_transaction(signed_txn)

        return tx_id

    except Exception as e:
        return f"BLOCKCHAIN_ERROR: {str(e)}"


# -------------------------------
# 🔹 MAIN VERIFY FUNCTION
# -------------------------------
def verify_property(data: dict):
    """
    Full verification pipeline
    """
    hash_value = generate_hash(data)

    tx_id = send_to_blockchain(hash_value)

    return {
        "verified": not str(tx_id).startswith("BLOCKCHAIN_ERROR"),
        "hash": hash_value,
        "tx_id": tx_id
    }