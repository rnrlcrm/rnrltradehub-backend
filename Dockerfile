# Use the official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn

# Expose port 8080 (required by Cloud Run)
EXPOSE 8080

# Command to run the app
CMD ["python", "main.py"]
