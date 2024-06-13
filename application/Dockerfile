# Use the official Python image from the Docker Hub
FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Install necessary tools and SQLite
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files into the container
COPY . /app

# Expose the port on which the Flask app will run
EXPOSE 5000

LABEL version="1.0.1"
# TODO: Add a Volume for persistence across boots
LABEL permissions='\
{\
  "ExposedPorts": {\
    "5000/tcp": {}\
  },\
  "HostConfig": {\
    "Binds":["/root/.config:/root/.config"],\
    "PortBindings": {\
      "5000/tcp": [\
        {\
          "HostPort": ""\
        }\
      ]\
    }\
  }\
}'
LABEL authors='[\
    {\
        "name": "Varun Surti",\
        "email": "varunrsurti@gmail.com"\
    }\
]'
LABEL company='{\
        "about": "",\
        "name": "IXAR",\
        "email": "varunrsurti@gmail.com"\
    }'
LABEL type="cone-penetrometer"
LABEL readme='https://github.com/bharatind12/CP/blob/main/README.md'
LABEL links='{\
        "website": "https://github.com/bharatind12/CP/tree/main/application",\
        "support": "https://github.com/bharatind12/CP/tree/main/application"\
    }'
LABEL requirements="core >= 1.1"


# Specify the command to run on container startup
CMD ["python", "main.py"]
