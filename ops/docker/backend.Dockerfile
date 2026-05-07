FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

WORKDIR /workspace

CMD ["uvicorn", "quant_evo_nextgen.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
