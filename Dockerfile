# Stage 1: Builder 
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Final 
FROM python:3.11-slim

WORKDIR /app

# Instala apenas as bibliotecas necessárias para rodar o MySQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

# Copia o código fonte para dentro do container
COPY ./src /app/src

# Cria um usuário não-root para segurança 
RUN useradd -m appuser && chown -R appuser /app
USER appuser

WORKDIR /app/src

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
