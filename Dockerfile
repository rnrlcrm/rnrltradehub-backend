# Use the official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 (required by Cloud Run)
EXPOSE 8080

# Command to run the app with uvicorn
# Use 0.0.0.0 to bind to all interfaces (required for Cloud Run)
# Use PORT environment variable (Cloud Run sets this to 8080)
CMD exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
