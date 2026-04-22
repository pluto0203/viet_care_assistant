FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[prod]" 2>/dev/null || pip install --no-cache-dir -e .

# App source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.app_main:app", "--host", "0.0.0.0", "--port", "8000"]
