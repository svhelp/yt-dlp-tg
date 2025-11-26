FROM python:3.11-slim

WORKDIR /src

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN rm -f .env && mv .env_production .env

RUN mkdir -p /storage

RUN chmod -R 777 /storage

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
