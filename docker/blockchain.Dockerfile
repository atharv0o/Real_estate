FROM python:3.10-slim

WORKDIR /app

COPY blockchain/requirements.txt /tmp/blockchain-requirements.txt
RUN pip install --no-cache-dir -r /tmp/blockchain-requirements.txt

COPY blockchain /app/blockchain

WORKDIR /app/blockchain

CMD ["python", "api.py"]
