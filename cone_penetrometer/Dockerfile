FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY app /app

# Install required packages for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies
RUN python /app/setup.py install

EXPOSE 5000/tcp

LABEL version="1.0.1"
# TODO: Add a Volume for persistence across boots
LABEL permissions='\
{\
  "ExposedPorts": {\
    "5000/tcp": {}\
  },\
  "HostConfig": {\
    "Privileged": true,\
    "NetworkMode":"host",\
    "Binds":["/root/.config:/root/.config",""],\
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
        "name": "Varun",\
        "email": "varunrsurti@gmail.com"\
    }\
]'
LABEL company='{\
        "about": "",\
        "name": "IXAR Robotics",\
        "email": "varunrsurti@gmail.com"\
    }'
LABEL type="cone-penetrometer"
# LABEL readme='https://raw.githubusercontent.com/Williangalvani/BlueOS-examples/{tag}/example4-vue-backend/Readme.md'
LABEL links='{\
        "website": "https://dynamaxsolutions.github.io/Dynamax/Resumes/VarunResume.html",\
    }'
LABEL requirements="core >= 1.1"

ENTRYPOINT ["python", "/app/main.py"]
