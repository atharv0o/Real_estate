import requests

BLOCKCHAIN_URL = "http://127.0.0.1:8002/verify"

def verify_property(data):
    try:
        res = requests.post(BLOCKCHAIN_URL, json=data)
        return res.json()
    except Exception as e:
        return {
            "verified": False,
            "error": str(e)
        }