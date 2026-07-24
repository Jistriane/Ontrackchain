FROM python:3.11-slim

WORKDIR /app

COPY apps/case-management/src /app/src

ENV PYTHONPATH=/app/src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir fastapi uvicorn pydantic

EXPOSE 8006

CMD ["uvicorn", "case_management.main:app", "--host", "0.0.0.0", "--port", "8006"]
