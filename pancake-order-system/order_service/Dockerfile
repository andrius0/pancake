# Dockerfile for Order Service 
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY shared ./src/shared
CMD ["python", "src/main.py"] 