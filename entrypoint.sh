#!/bin/bash

# Start the gRPC server in the background
echo "Starting gRPC server in background..."
python tts_server.py &

# Wait a few seconds for the server to potentially start up
sleep 5

# Start the Gradio UI app in the foreground
echo "Starting Gradio UI..."
# Use --server_port to ensure it uses the exposed port
# Use --server_name 0.0.0.0 to make it accessible from outside the container
python app.py --server_name 0.0.0.0 --server_port 7860

# Optional: Add cleanup if needed when Gradio exits, though background process might just terminate
