import os
from dotenv import load_dotenv
from algosdk.v2client import algod

load_dotenv()

ALGOD_ADDRESS = os.getenv("ALGORAND_NODE_URL")
ALGOD_TOKEN = os.getenv("ALGORAND_NODE_TOKEN")

def get_algod_client():
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)