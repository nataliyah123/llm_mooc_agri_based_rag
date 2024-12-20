FROM python:3.9-slim

WORKDIR /app
COPY services/classification_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/classification_service/app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
