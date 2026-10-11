
# Use Python 3.13 as the runtime
FROM python:3.13-slim

# Prevent unnecessary Python cache files
# and display application logs immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install backend dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy our FastAPI application
COPY app ./app

# Document the application port
EXPOSE 8000

# Start FastAPI inside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
