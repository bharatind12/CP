# FROM python:3.9-slim-bullseye

# COPY app /app
# RUN pip install fastapi uvicorn sqlalchemy loguru pydantic

# EXPOSE 5000/tcp

# LABEL version="1.0.1"
# # TODO: Add a Volume for persistence across boots
# LABEL permissions='\
# {\
#   "ExposedPorts": {\
#     "5000/tcp": {}\
#   },\
#   "HostConfig": {\
#     "Binds":["/root/.config:/root/.config"],\
#     "PortBindings": {\
#       "5000/tcp": [\
#         {\
#           "HostPort": ""\
#         }\
#       ]\
#     }\
#   }\
# }'
# LABEL authors='[\
#     {\
#         "name": "Varun Surti",\
#         "email": "willian@bluerobotics.com"\
#     }\
# ]'
# LABEL company='{\
#         "about": "",\
#         "name": "Blue Robotics",\
#         "email": "support@bluerobotics.com"\
#     }'
# LABEL type="example"
# LABEL readme='https://raw.githubusercontent.com/Williangalvani/BlueOS-examples/{tag}/example4-vue-backend/Readme.md'
# LABEL links='{\
#         "website": "https://github.com/Williangalvani/BlueOS-examples/",\
#         "support": "https://github.com/Williangalvani/BlueOS-examples/"\
#     }'
# LABEL requirements="core >= 1.1"

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]






FROM python:3.9-slim-bullseye

# Install Rust and Cargo
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl gcc g++ make && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY app /app

# Install Python dependencies
# RUN pip install fastapi uvicorn sqlalchemy loguru pydantic

RUN python /app/setup.py install

# Expose the port
EXPOSE 5000/tcp

# Metadata and entry point
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
        "email": "willian@bluerobotics.com"\
    }\
]'
LABEL company='{\
        "about": "",\
        "name": "Blue Robotics",\
        "email": "support@bluerobotics.com"\
    }'
LABEL type="example"
LABEL readme='https://raw.githubusercontent.com/Williangalvani/BlueOS-examples/{tag}/example4-vue-backend/Readme.md'
LABEL links='{\
        "website": "https://github.com/Williangalvani/BlueOS-examples/",\
        "support": "https://github.com/Williangalvani/BlueOS-examples/"\
    }'
LABEL requirements="core >= 1.1"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]