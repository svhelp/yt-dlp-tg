FROM python:3.11-slim

WORKDIR /src

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN rm -f .env && mv .env_production .env

RUN mkdir -p /storage

RUN chmod -R 777 /storage

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
