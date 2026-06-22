FROM python:3.15.0b2-alpine

WORKDIR /app

COPY data/ data/
COPY replay.py ./

RUN pip install --no-cache-dir aiohttp

CMD ["python", "replay.py"]
