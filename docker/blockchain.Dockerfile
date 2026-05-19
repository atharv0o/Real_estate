FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/blockchain

COPY blockchain/requirements.txt /tmp/blockchain-requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /tmp/blockchain-requirements.txt

COPY blockchain /app/blockchain

WORKDIR /app/blockchain

EXPOSE 8002

CMD ["python", "api.py"]
