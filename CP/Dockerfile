FROM python:3.9-slim-bullseye

# Install Rust and Cargo
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl gcc g++ make && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y supervisor

# Copy the application code
COPY app /app

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
# Install Python dependencies
# RUN pip install fastapi uvicorn sqlalchemy loguru pydantic

RUN python /app/setup.py install

# Expose the port
EXPOSE 5000/tcp
EXPOSE 5001/tcp
EXPOSE 5002/tcp
# Metadata and entry point
LABEL version="1.0.1"
# TODO: Add a Volume for persistence across boots
LABEL permissions='\
{\
  "ExposedPorts": {\
    "5000/tcp": {}\
    "5001/tcp": {}\
    "5002/tcp": {}\
  },\
  "HostConfig": {\
    "Binds":[\
    "/root/.config:/root/.config",\
    "/dev/cone_penetrometer:/dev/cone_penetrometer"\
     ],\
    "PortBindings": {\
      "5000/tcp": [\
        {\
          "HostPort": ""\
        }\
      ],\
    "PortBindings": {\
      "5001/tcp": [\
        {\
          "HostPort": ""\
        }\
      ],\
      "PortBindings": {\
      "5002/tcp": [\
        {\
          "HostPort": ""\
        }\
      ],\
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
        "name": "IXAR Robotics",\
        "email": "varunrsurti@gmail.com"\
    }'
LABEL type="Cone-Penetrometer"
LABEL readme='https://raw.githubusercontent.com/Williangalvani/BlueOS-examples/{tag}/example4-vue-backend/Readme.md'
LABEL links='{\
        "website": "https://github.com/Williangalvani/BlueOS-examples/",\
        "support": "https://github.com/Williangalvani/BlueOS-examples/"\
    }'
LABEL requirements="core >= 1.1"

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
# CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 5000 & uvicorn app.sensor_service:app --host 0.0.0.0 --port 5001 & uvicorn app.command_service:app --host 0.0.0.0 --port 5002"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]