# Use Python 3.11
FROM python:3.11-slim

# Install system dependencies (Tesseract and PDF tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Run the app (Using 0.0.0.0 so it's accessible externally)
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "7860"]
