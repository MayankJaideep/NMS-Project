FROM python:3.11-slim
WORKDIR /app
COPY provisioner.py /app/provisioner.py
RUN pip install --no-cache-dir requests
CMD ["python", "provisioner.py"]
