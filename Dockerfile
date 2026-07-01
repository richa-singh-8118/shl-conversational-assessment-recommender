# Use official python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    USE_TF=NO \
    USE_TORCH=YES \
    PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app/

# Build catalog and FAISS index during image creation (bakes index into image)
RUN python catalog/scraper.py && python build_index.py

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start FastAPI — PORT is injected by cloud platform at runtime
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
