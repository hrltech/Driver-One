FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render utiliza a variável de ambiente PORT dinamicamente
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
