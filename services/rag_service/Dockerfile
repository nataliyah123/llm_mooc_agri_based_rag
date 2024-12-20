FROM python:3.9-slim

WORKDIR /app
COPY services/rag_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/rag_service/app.py .
COPY utils/message_batching.py ./utils/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
