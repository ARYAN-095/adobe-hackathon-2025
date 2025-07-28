# Use a specific architecture to avoid cross-platform issues (especially on M1/M2 chips) [cite: 57]
FROM --platform=linux/amd64 python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (optional: add poppler-utils if PDFs require it)
# RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

# Copy only requirements and install early for layer caching
COPY Challenge_1a/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your main app code
COPY Challenge_1a/main.py .

# Optional: copy any additional modules if needed
# COPY round1a/utils.py .

# Set default command — optional but good practice
CMD ["python", "main.py"]