FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . /app

# Install required packages for building Python packages and serial communication
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies using setup.py
RUN pip install .

# Expose port 5000 for the Flask application
EXPOSE 5000/tcp

# Metadata
LABEL version="1.0.1"
LABEL authors='[{"name": "Varun", "email": "varunrsurti@gmail.com"}]'
LABEL company='{"about": "", "name": "IXAR Robotics", "email": "varunrsurti@gmail.com"}'
LABEL type="cone-penetrometer"
LABEL requirements="core >= 1.1"

# Set the entry point to run the Flask application
ENTRYPOINT ["python", "/app/main.py"]
