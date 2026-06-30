FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "public_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
