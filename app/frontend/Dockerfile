# Stage 1: Build dependencies in temporary stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Prevent Python from writing .pyc files & buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create virtual environment & install requirements
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY app/frontend/app.py .

# Create a non-root user for security best practices
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose target Flask port
EXPOSE 5000

# Health check instructions for Docker
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/healthz')" || exit 1

# Run with Gunicorn (2 worker processes)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]