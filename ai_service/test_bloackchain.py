from dotenv import load_dotenv; load_dotenv()
from blockchain.algorand import anchor
txid = anchor('test-001', {'price': 5000000, 'city': 'Pune'})
print('SUCCESS — txn ID:', txid)