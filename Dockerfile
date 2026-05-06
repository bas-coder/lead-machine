FROM python:3.10-slim

# Install Chromium browser and driver for Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your script files to the server
COPY . .

# Run the engine
CMD ["python", "-u", "run.py"]
