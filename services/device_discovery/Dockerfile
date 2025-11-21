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
COPY services/device_discovery/ ./services/device_discovery/

# Set environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=device_discovery

# Expose port
EXPOSE 8001

# Run the service
CMD ["python", "-m", "services.device_discovery.main"]
