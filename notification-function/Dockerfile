FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt

COPY app ./app

RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "app.consumer"]