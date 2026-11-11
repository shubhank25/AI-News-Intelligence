
# Purpose: Build a Docker image for running the AI News Intelligence FastAPI backend.

FROM python:3.14-slim

# Set the working directory inside the container.
WORKDIR /app

# Prevent Python from writing bytecode and enable real-time logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies first for better Docker layer caching.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend application code.
COPY app/ ./app/

# Create directories for application data and logs.
RUN mkdir -p data logs

# Expose the FastAPI port.
EXPOSE 8000

# Start the FastAPI application.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
