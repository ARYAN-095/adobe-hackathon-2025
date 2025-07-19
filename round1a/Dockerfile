# Explicitly specify the platform for full compatibility [cite: 57]
FROM --platform=linux/amd64 python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency file and install them
COPY round1a/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python script into the container
COPY round1a/main.py .

# The container will be run with the docker run command specified in the docs[cite: 67],
# so a CMD is not strictly required but is good practice.