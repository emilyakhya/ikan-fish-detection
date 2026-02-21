# IKAN Fish Detection Flask Application Dockerfile
# Optimized for DigitalOcean App Platform deployment

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Clone YOLOv5 repository (do this early for better caching)
RUN git clone --depth 1 --branch v7.0 https://github.com/ultralytics/yolov5.git /app/yolov5 && \
    rm -rf /app/yolov5/.git

# Copy only requirements files first (for better layer caching)
COPY requirements_web.txt /app/

# Install Python dependencies (cache this layer separately)
# Install web requirements first (lighter), then YOLOv5 requirements
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements_web.txt && \
    pip install --no-cache-dir -r /app/yolov5/requirements.txt

# Note: Model weights (yolov5s.pt) will be downloaded at runtime if not present
# This saves build time and allows the app to start faster

# Copy application files (do this last to maximize cache hits)
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/uploads /app/results

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV PORT=8080

# Expose port (DigitalOcean App Platform uses PORT env var)
EXPOSE 8080

# Health check (increased start period to allow model download)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health')" || exit 1

# Create startup script to download model if needed
RUN echo '#!/bin/bash\n\
if [ ! -f /app/yolov5s.pt ]; then\n\
    echo "Downloading yolov5s.pt model weights..."\n\
    curl -L -o /app/yolov5s.pt https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt || echo "Model will be auto-downloaded by YOLOv5"\n\
fi\n\
exec python app.py' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]