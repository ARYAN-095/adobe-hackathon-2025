# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# --- CORRECTED INSTALLATION STEP ---
# 1. First, install the CPU-only version of torch.
# 2. Then, install the rest of the requirements. pip will see torch is
#    already installed and will not download it again.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container
COPY main.py .

# Define the command to run the application
ENTRYPOINT ["python", "main.py"]