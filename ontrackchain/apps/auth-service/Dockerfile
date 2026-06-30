FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir .

EXPOSE 9000

CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "9000"]
