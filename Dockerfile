FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY src ./src
COPY sample-data ./sample-data
COPY scripts ./scripts

RUN uv sync --no-dev

ENV PYTHONPATH=/app/src

CMD ["uv", "run", "uvicorn", "realtime_commerce_analytics.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
