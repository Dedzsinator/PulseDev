# Multi-stage build for PulseDev CCM API
FROM python:3.12-slim AS builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    # Install dependencies one by one to handle failures gracefully
    pip install fastapi uvicorn[standard] sqlalchemy asyncpg redis pydantic pydantic-settings && \
    pip install python-multipart python-jose[cryptography] passlib[bcrypt] && \
    pip install prometheus-client structlog cryptography gitpython psutil && \
    pip install websockets aiofiles jinja2 python-dotenv && \
    pip install pytest pytest-asyncio httpx faker && \
    # Install scientific computing packages (optional)
    pip install numpy scipy pandas requests tqdm anthropic || echo "Some optional packages failed - continuing"

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
