# ── Stage 1: Builder ──────────────────────────────────────────
# Install dependencies here. This stage has pip and build tools.
# None of that makes it into the final image.
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

# --no-cache-dir: don't bloat the layer with pip's cache
# --user: installs to ~/.local so we can copy just that dir to the runner
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runner ───────────────────────────────────────────
# Lean runtime image. No pip. No build tools. No root.
FROM python:3.12-slim AS runner

# Create a non-root system user.
# If this container is ever compromised, the attacker gets a low-priv
# user with no shell and no home directory — not root.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 1001 --no-create-home appuser

WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy only the files the app actually needs at runtime
COPY app.py .
COPY templates/ ./templates/

# Hand off ownership and switch to non-root before the process starts
RUN chown -R appuser:appuser /app
USER appuser

# Python needs to find packages installed to ~/.local/bin
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

# --workers 2: two worker processes (appropriate for 256 Fargate CPU units)
# --timeout 30: kill any worker that hangs for 30 seconds
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "app:app"]
