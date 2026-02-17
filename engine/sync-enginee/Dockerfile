FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# Install system dependencies with cache
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    curl \
    git

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Entrypoint
CMD ["python", "sync.py"]
