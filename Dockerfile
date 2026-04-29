FROM python:3.11-slim

# Prevents Python from writing .pyc files and enables unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./config.py ./config.py
COPY ./database.py ./database.py
COPY ./main.py ./main.py
COPY ./routers ./routers
COPY ./simulator ./simulator
COPY ./opcua ./opcua
COPY ./failure ./failure
COPY ./websocket ./websocket
COPY ./persistence ./persistence
COPY ./alerts ./alerts
COPY ./sql ./sql
COPY ./app ./app
COPY ./env_check.py ./env_check.py

CMD ["sh", "-c", "uvicorn main:app --host ${API_HOST} --port ${API_PORT}"]
