# Dockerfile for Cloud Run deployment
# Multi-stage build for production

FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY .env.example .

# Set PATH to include user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
