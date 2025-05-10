# 1. Base Image: Use an official Python 3.10 image
FROM python:3.10-slim

# 2. Install system dependencies (git is no longer needed here for cloning Tortoise)
#    build-essential might still be useful for compiling some Python packages.
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# 3. Set up Working Directory
WORKDIR /app

# 4. Copy your pre-modified Tortoise TTS local directory into the image
#    Assumes 'tortoise-tts' directory is in the same context as the Dockerfile
COPY tortoise-tts/ /app/tortoise-tts/

# 5. Install Tortoise TTS and its Dependencies from your local, modified copy
#    Install requirements from the (now pre-modified) requirements.txt
RUN pip install --no-cache-dir -r /app/tortoise-tts/requirements.txt
#    Install Tortoise TTS itself using pip from the local directory
RUN cd /app/tortoise-tts && pip install --no-cache-dir .

# 6. Copy your project-specific files into the Docker image
COPY app.py .
COPY tts_server.py .
COPY tts.proto .
COPY requirements.txt ./project_requirements.txt 
# Your project's requirements (for Gradio, etc.)

# 7. Install Project-Specific Dependencies from your project's requirements.txt
RUN pip install --no-cache-dir -r ./project_requirements.txt

# 8. Compile Protobuf Definition
#    Installs grpcio-tools if not already in your project_requirements.txt
RUN pip install --no-cache-dir grpcio-tools && \
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. tts.proto

# 9. Expose Ports
EXPOSE 7860 
# For Gradio UI

EXPOSE 50051 
# For gRPC server

# 10. Set Environment Variables
ENV PYTHONUNBUFFERED=1

# 11. Define the command to run your application
CMD ["python", "tts_server.py"]