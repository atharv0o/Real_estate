FROM python:3.10-slim

WORKDIR /app

COPY rag_engine/requirements.txt /tmp/rag-requirements.txt
RUN pip install --no-cache-dir -r /tmp/rag-requirements.txt

COPY . /app

ENV PYTHONPATH=/app:/app/rag_engine
WORKDIR /app/rag_engine

CMD ["uvicorn", "rag_api:app", "--host", "0.0.0.0", "--port", "8001"]
