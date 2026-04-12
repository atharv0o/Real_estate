FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt /tmp/backend-requirements.txt
COPY rag_engine/requirements.txt /tmp/rag-requirements.txt
COPY data_pipeline/requirements.txt /tmp/pipeline-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt -r /tmp/rag-requirements.txt -r /tmp/pipeline-requirements.txt

COPY . /app

ENV PYTHONPATH=/app:/app/backend:/app/rag_engine

CMD ["python", "data_pipeline/scheduler.py"]
