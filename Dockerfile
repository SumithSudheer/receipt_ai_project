# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Poppler
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose API port
EXPOSE 8000

# Start server (replace uvicorn with gunicorn if Django)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
