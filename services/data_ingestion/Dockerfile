FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ ./shared/

# Copy service code
COPY services/data_ingestion/ ./services/data_ingestion/

# Set environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=data_ingestion

# Expose port
EXPOSE 8003

# Run the service
CMD ["python", "-m", "services.data_ingestion.main"]
