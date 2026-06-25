# syntax=docker/dockerfile:1
# BuildKit required for cache mounts (DOCKER_BUILDKIT=1 or Docker Desktop default).

FROM python:3.14-slim AS builder

WORKDIR /app

# Reuse official uv binary — avoids pip download on every cold build.
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Layer 1: deps — only rebuilds when lock/manifest change.
COPY app/pyproject.toml app/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Layer 2: project — rebuilds on code changes; deps stay cached above.
COPY app/ ./

# Overwrite Git LFS pointers with the actual model binary from Hugging Face Hub if missing or invalid
RUN python -c " \
import os, urllib.request; \
d = 'models/onnx/baai-bge-small'; \
os.makedirs(d, exist_ok=True); \
m_path = os.path.join(d, 'model.onnx'); \
t_path = os.path.join(d, 'tokenizer.json'); \
if not os.path.exists(m_path) or os.path.getsize(m_path) < 1024 * 1024: \
    print('Downloading model.onnx...'); \
    urllib.request.urlretrieve('https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/onnx/model.onnx', m_path); \
if not os.path.exists(t_path) or os.path.getsize(t_path) < 1000: \
    print('Downloading tokenizer.json...'); \
    urllib.request.urlretrieve('https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/tokenizer.json', t_path);"

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.14-slim AS runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /app /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
