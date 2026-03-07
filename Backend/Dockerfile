# # Production-grade Dockerfile for CoreIQ RAG Service (ragd4)
# # Multi-stage build for optimized image size

# # ============= Stage 1: Builder =============
# FROM python:3.11-slim-bookworm AS builder

# # Set working directory
# WORKDIR /build

# # Install build dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     g++ \
#     libpq-dev \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Copy requirements first for better layer caching
# COPY requirements.txt .

# # Create virtual environment and install dependencies
# RUN python -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"

# # Install Python dependencies
# RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
#     pip install --no-cache-dir -r requirements.txt

# # Download NLTK data during build
# RUN python -c "import nltk; nltk.download('punkt', download_dir='/opt/nltk_data'); nltk.download('stopwords', download_dir='/opt/nltk_data')"

# # ============= Stage 2: Runtime =============
# FROM python:3.11-slim-bookworm

# # Set labels for image metadata
# LABEL maintainer="CoreIQ Team"
# LABEL version="4.0.0"
# LABEL description="CoreIQ RAG Service with asyncpg"

# # Create non-root user for security
# RUN groupadd -r raguser && useradd -r -g raguser raguser

# # Set working directory
# WORKDIR /app

# # Install runtime dependencies only
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq5 \
#     curl \
#     gosu \
#     && rm -rf /var/lib/apt/lists/*

# # Copy virtual environment from builder
# COPY --from=builder /opt/venv /opt/venv
# COPY --from=builder /opt/nltk_data /opt/nltk_data

# # Set environment variables
# ENV PATH="/opt/venv/bin:$PATH" \
#     PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1 \
#     FLASK_APP=app.py \
#     NLTK_DATA=/opt/nltk_data \
#     PYTHONPATH=/app

# # Copy application code
# COPY --chown=raguser:raguser . .

# # Create necessary directories with correct permissions
# RUN mkdir -p /app/data/vector_stores/global \
#     /app/data/bm25/global \
#     /app/uploads \
#     && chown -R raguser:raguser /app/data /app/uploads

# # Create entrypoint script that fixes volume permissions at runtime
# RUN printf '#!/bin/bash\nset -e\n\n# Fix ownership of mounted volumes (runs as root)\nchown -R raguser:raguser /app/data /app/uploads\n\n# Drop to raguser and exec the CMD\nexec gosu raguser "$@"\n' > /app/entrypoint.sh \
#     && chmod +x /app/entrypoint.sh

# # Expose port
# EXPOSE 5000

# # Health check
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD curl -f http://localhost:5000/health || exit 1

# # Run entrypoint as root so it can fix permissions, then drops to raguser
# ENTRYPOINT ["/app/entrypoint.sh"]
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]


# Production-grade Dockerfile for CoreIQ RAG Service (ragd4)
# Multi-stage build for optimized image size

# ============= Stage 1: Builder =============
FROM python:3.11-slim-bookworm AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data during build
RUN python -c "import nltk; nltk.download('punkt', download_dir='/opt/nltk_data'); nltk.download('stopwords', download_dir='/opt/nltk_data')"

# Pre-download the reranker model during build so it's cached in the image
ENV HF_HOME=/opt/hf_cache
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# ============= Stage 2: Runtime =============
FROM python:3.11-slim-bookworm

# Set labels for image metadata
LABEL maintainer="CoreIQ Team"
LABEL version="4.0.0"
LABEL description="CoreIQ RAG Service with asyncpg"

# Create non-root user for security (with home directory)
RUN groupadd -r raguser && useradd -r -g raguser -m raguser

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/nltk_data /opt/nltk_data
COPY --from=builder /opt/hf_cache /opt/hf_cache

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    NLTK_DATA=/opt/nltk_data \
    HF_HOME=/opt/hf_cache \
    TRANSFORMERS_CACHE=/opt/hf_cache \
    SENTENCE_TRANSFORMERS_HOME=/opt/hf_cache \
    PYTHONPATH=/app

# Copy application code
COPY --chown=raguser:raguser . .

# Create necessary directories with correct permissions
RUN mkdir -p /app/data/vector_stores/global \
    /app/data/bm25/global \
    /app/uploads \
    && chown -R raguser:raguser /app/data /app/uploads /opt/hf_cache

# Create entrypoint script that fixes volume permissions at runtime
RUN printf '#!/bin/bash\nset -e\n\n# Fix ownership of mounted volumes (runs as root)\nchown -R raguser:raguser /app/data /app/uploads\n\n# Drop to raguser and exec the CMD\nexec gosu raguser "$@"\n' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run entrypoint as root so it can fix permissions, then drops to raguser
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]