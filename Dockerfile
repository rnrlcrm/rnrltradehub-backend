# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Cloud Run sets PORT=8080 automatically
ENV PORT=8080

# Expose same port
EXPOSE 8080

# Start FastAPI using uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
