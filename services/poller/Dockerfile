FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libsnmp-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ ./shared/

# Copy service code
COPY services/poller/ ./services/poller/

# Set environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=poller

# Expose port
EXPOSE 8002

# Run the service
CMD ["python", "-m", "services.poller.main"]
