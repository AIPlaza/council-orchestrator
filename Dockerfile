FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV MCP_BACKEND=mock

ENTRYPOINT ["python3", "server.py"]
