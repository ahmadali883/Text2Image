# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set environment variables to prevent interactive prompts during build
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install necessary system dependencies
# git for cloning, ffmpeg for librosa, libsndfile1 for soundfile, build-essential for compiling
# Adding libaio-dev just in case any dependency *indirectly* needs it for async_io, though deepspeed is removed
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    libsndfile1 \
    build-essential \
    libaio-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# --- Tortoise TTS Installation ---

# 1. Install specific compatible versions of conflicting packages FIRST
#    transformers==4.31.0 requires tokenizers >=0.11.1, !=0.11.3, <0.14
RUN pip install --no-cache-dir "transformers==4.31.0" "tokenizers==0.13.3"

# 2. Install other direct Tortoise dependencies (excluding deepspeed and already installed ones)
#    Based on tortoise-tts/requirements.txt, excluding deepspeed, transformers, tokenizers
RUN pip install --no-cache-dir \
    tqdm \
    rotary_embedding_torch \
    inflect \
    progressbar \
    einops==0.4.1 \
    unidecode \
    scipy \
    librosa==0.9.1 \
    ffmpeg-python \
    numba \
    torchaudio \
    threadpoolctl \
    appdirs \
    pydantic==1.9.1

# 3. Install Tortoise TTS directly from GitHub using pip
#    This should respect the already installed dependencies
#    Note: We are NOT cloning or running setup.py manually
RUN pip install --no-cache-dir git+https://github.com/neonbjb/tortoise-tts.git

# --- Application Setup ---
# Copy the project-specific requirements file
COPY requirements.txt .

# Install project-specific dependencies (Gradio, gRPC, etc.)
# This should respect the already installed versions
RUN pip install --no-cache-dir -r requirements.txt

# Copy the gRPC proto file and compile it
COPY tts.proto .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. tts.proto

# Copy the application source code and entrypoint script
COPY tts_server.py .
COPY app.py .
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose the ports the gRPC server and Gradio app will use
EXPOSE 50051
EXPOSE 7860

# Set the entrypoint script to run when the container starts
ENTRYPOINT ["./entrypoint.sh"]

# Optional: Add healthcheck if needed
# HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
#   CMD curl --fail http://localhost:7860 || exit 1
