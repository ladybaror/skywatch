# Stage 1: Build dependencies in temporary stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Prevent Python from writing .pyc files & buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
    

# Create virtual environment & install requirements
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY  app/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.11-slim AS runner

WORKDIR /app

# Create a non-root user securely
RUN id appuser >/dev/null 2>&1 || useradd -m appuser

# Copy virtual environment from builder stage with correct ownership
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy worker application source code with correct ownership
COPY --chown=appuser:appuser app/worker/ .

# Switch to the non-root user
USER appuser

# Run the worker script/process
CMD ["python", "worker.py"]