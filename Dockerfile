FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libjpeg-dev \
        libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY src/ .

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser

# Create database directory and set permissions
RUN mkdir -p /app/db_data && chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"] 