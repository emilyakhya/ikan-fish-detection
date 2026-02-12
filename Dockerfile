# IKAN Fish Detection Flask Application Dockerfile
# Optimized for DigitalOcean App Platform deployment

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements_web.txt /app/
COPY yolov5/requirements.txt /app/yolov5_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements_web.txt && \
    pip install --no-cache-dir -r yolov5_requirements.txt

# Copy application files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/uploads /app/results

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV PORT=8080

# Expose port (DigitalOcean App Platform uses PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health')" || exit 1

# Run the application
CMD python app.py