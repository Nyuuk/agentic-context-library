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

# Expose port for health check
EXPOSE 8000

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Health check (TCP port check - FastMCP HTTP transport)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -sf -H "Authorization: Bearer $MCP_API_KEY" http://localhost:8000/mcp -o /dev/null || exit 1

# Entrypoint
CMD ["python", "server.py"]
