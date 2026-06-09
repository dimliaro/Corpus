# ── Build stage: install dependencies ────────────────────────────────────────
FROM python:3.12-slim AS builder

# Bring in uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy only dependency manifests first — this layer is cached unless they change
COPY pyproject.toml uv.lock ./

# Install all production deps into a local venv; skip the project package itself
RUN uv sync --frozen --no-dev --no-cache --no-install-project

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy the pre-built venv from the builder (keeps the final image lean)
COPY --from=builder /app/.venv /app/.venv

# Copy application source and frontend
COPY src/       ./src/
COPY frontend/  ./frontend/

# Put the venv on PATH so uvicorn / all imports resolve without activating
ENV PATH="/app/.venv/bin:$PATH"

# The API is launched from src/ so relative imports (search, embedding, …)
# and the ../frontend path in rag_api.py both resolve correctly
WORKDIR /app/src

EXPOSE 8085

# Env vars are injected at runtime (--env-file .env  or  docker-compose)
# — never bake secrets into the image
CMD ["uvicorn", "rag_api:app", "--host", "0.0.0.0", "--port", "8085"]
