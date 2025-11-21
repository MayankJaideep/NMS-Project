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
COPY services/api/ ./services/api/

# Set environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=api

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
