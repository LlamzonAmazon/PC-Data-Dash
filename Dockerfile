FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Copy data folder (for standalone clean_data.py)
COPY data/ ./data/

# Copy ND-GAIN ZIP file (required for ND-GAIN client)
COPY data/external/ ./data/external/

# Create data directories (if needed)
RUN mkdir -p data/raw data/interim data/processed

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python3", "-m", "src.clean.clean_data"]