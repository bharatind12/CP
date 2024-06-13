FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Install MongoDB and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    gnupg \
    && curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add - \
    && echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/debian buster/mongodb-org/4.4 main" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    mongodb-org \
    && rm -rf /var/lib/apt/lists/*

# Copy the application files into the container
COPY . /app

# Install the Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose the port
EXPOSE 5000

# Add MongoDB data directory
RUN mkdir -p /data/db

# Set environment variables for MongoDB
ENV MONGO_DB_PATH /data/db
ENV MONGO_LOG_PATH /var/log/mongodb/mongod.log

# Start MongoDB and the application
CMD mongod --dbpath $MONGO_DB_PATH --logpath $MONGO_LOG_PATH --fork && python /app/main.py
