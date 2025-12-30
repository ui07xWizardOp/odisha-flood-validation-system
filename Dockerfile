# =============================================================================
# Odisha Flood Validation System - Dockerfile
# =============================================================================
# Multi-stage build for FastAPI application
#
# Build: docker build -t flood-validation-api .
# Run:   docker run -p 8000:8000 flood-validation-api
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base Python image with system dependencies
# -----------------------------------------------------------------------------
FROM python:3.10-slim-bookworm AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    # GDAL and geospatial dependencies
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    # PostgreSQL client
    libpq-dev \
    # Build tools
    gcc \
    g++ \
    # Utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_CONFIG=/usr/bin/gdal-config \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# -----------------------------------------------------------------------------
# Stage 2: Builder - Install Python dependencies
# -----------------------------------------------------------------------------
FROM base AS builder

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --target=/app/dependencies -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: Production image
# -----------------------------------------------------------------------------
FROM base AS production

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app/dependencies /app/dependencies
ENV PYTHONPATH="/app/dependencies:${PYTHONPATH}"

# Copy application code
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup config/ /app/config/

# Create data directories
RUN mkdir -p /app/data/processed /app/data/raw /app/logs && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# Stage 4: Development image (alternative)
# -----------------------------------------------------------------------------
FROM production AS development

USER root

# Install development tools
RUN pip install --target=/app/dependencies \
    pytest pytest-cov pytest-asyncio \
    black isort flake8 mypy \
    jupyterlab ipykernel

USER appuser

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
