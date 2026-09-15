FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt

COPY app ./app

CMD ["python", "-m", "app.consumer"]