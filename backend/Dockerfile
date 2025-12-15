FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for moviepy and edge-tts
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create static directories
RUN mkdir -p static/audio static/videos static/previews

# Expose port
EXPOSE 8000

# Default command (overridden in docker-compose for dev)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]