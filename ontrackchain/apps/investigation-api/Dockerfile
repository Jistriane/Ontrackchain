FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY fixtures /app/fixtures

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir .

EXPOSE 8001

CMD ["uvicorn", "investigation_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
