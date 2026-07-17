# ─────────────────────────────────────────────────────────────────────────────
# Multi-stage Dockerfile for FastAPI RAG Agent Backend
#
# WHY multi-stage?
# ────────────────
# Stage 1 ("builder") installs all build-time dependencies (compilers,
# headers) needed by packages like numpy, faiss-cpu, etc.
# Stage 2 ("runtime") copies ONLY the installed Python packages and
# app code — no compilers, no pip cache, no .git history.
#
# Result: the runtime image is 300-400 MB instead of 1+ GB.
#
# WHY non-root user?
# ──────────────────
# Principle of least privilege. If the container is compromised (e.g.,
# via a dependency vulnerability), the attacker runs as `appuser` with
# no sudo access — they can't install packages, modify system files,
# or escalate to the host.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for compiled packages (faiss-cpu, numpy, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first → Docker layer caching means if
# requirements.txt hasn't changed, pip install is skipped entirely.
COPY requirements.txt .

# Install into a virtualenv so we can copy it cleanly to the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy the virtualenv from the builder (no compilers in this image)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY backend/ ./backend/
COPY env.example .

# Create directories for data persistence
RUN mkdir -p /app/vector_store /app/uploads /app/data

# Create non-root user
# WHY 1000:1000? It's the conventional first non-root UID/GID on Linux,
# and matches the default user on many host systems — this avoids
# permission issues with bind-mounted volumes.
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose the API port
EXPOSE 9999

# Health check — Docker/orchestrators use this to know if the container
# is actually serving requests, not just running a process.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9999/health')" || exit 1

# Run with uvicorn
# --host 0.0.0.0 is required inside Docker (default 127.0.0.1 would
# only accept connections from inside the container itself).
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "9999"]
