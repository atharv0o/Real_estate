FROM python:3.10-slim

WORKDIR /app/data_pipeline

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app/data_pipeline

CMD ["python", "bootstrap.py"]
