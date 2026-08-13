FROM python:3.11-slim

# Install system dependencies (git is required for EvoForge's agent to clone/commit)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy application source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV EVOFORGE_DATA_DIR=/app/data

# Ensure data directory exists
RUN mkdir -p /app/data

# Expose the API port
EXPOSE 8000

# Start the EvoForge FastAPI control plane
CMD ["sh", "-c", "uv run python -m evoforge.main serve --host 0.0.0.0 --port ${PORT:-8000}"]
