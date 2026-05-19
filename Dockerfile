FROM python:3.15-slim

WORKDIR /app

COPY data/ data/
COPY replay.py ./

RUN pip install --no-cache-dir aiohttp

CMD ["python", "replay.py"]
