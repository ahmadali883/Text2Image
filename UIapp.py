import gradio as gr
import grpc
import numpy as np
import time
import io
import soundfile as sf # Using soundfile is generally better for float audio

# Import generated gRPC files
import tts_pb2
import tts_pb2_grpc

# --- Client/UI Configuration ---
GRPC_SERVER_ADDRESS = 'localhost:50051'
VOICES = ['random', 'tom', 'freeman', 'train_atkins', 'train_daws', 'train_dotrice', 'train_dreams', 'train_empire', 'train_grace', 'train_kennard', 'train_lescault', 'train_mouse'] # Add more from tortoise/voices if needed
PRESETS = ['ultra_fast', 'fast', 'standard', 'high_quality']
DEFAULT_PRESET = 'fast' # Important for CPU
# -----------------------------

# --- gRPC Client Function ---
def generate_speech_grpc(text, voice, preset):
    print(f"Sending request to gRPC server: voice='{voice}', preset='{preset}'")
    print(f"Text: '{text[:50]}...'")

    if not text:
        return None, "Error: Text input cannot be empty."

    try:
        # Establish connection and create stub
        with grpc.insecure_channel(GRPC_SERVER_ADDRESS) as channel:
            stub = tts_pb2_grpc.TTSServiceStub(channel)

            # Create request
            request = tts_pb2.SynthesizeRequest(text=text, voice=voice, preset=preset)

            # Make the gRPC call (this will block until server responds - potentially long time on CPU)
            start_time = time.time()
            print("Waiting for server response...")
            response = stub.Synthesize(request, timeout=2400) # Generous timeout (20 mins) for CPU
            end_time = time.time()
            print(f"Received response from server in {end_time - start_time:.2f} seconds.")

            if response and response.audio_content:
                # Convert bytes back to numpy array (assuming float32)
                audio_np = np.frombuffer(response.audio_content, dtype=np.float32)
                sample_rate = response.sample_rate
                print(f"Received audio: {len(audio_np)} samples at {sample_rate} Hz.")
                # Return tuple for Gradio Audio component: (sample_rate, numpy_array)
                return (sample_rate, audio_np), "Success"
            else:
                print("Error: Received empty response or audio content.")
                # Attempt to get error details if possible (depends on server implementation)
                # For simplicity, just return a generic error
                return None, "Error: Failed to generate audio on server (empty response)."

    except grpc.RpcError as e:
        print(f"gRPC Error: {e.code()} - {e.details()}")
        return None, f"Error communicating with server: {e.details()}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, f"An unexpected error occurred: {str(e)}"

# --- Create Gradio Interface ---
with gr.Blocks() as demo:
    gr.Markdown("# Tortoise TTS via gRPC")
    gr.Markdown("Enter text, choose a voice and preset, then click Generate. **Note: CPU generation is VERY slow.**")

    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(label="Text to Synthesize", lines=4)
        with gr.Column(scale=1):
            voice_dropdown = gr.Dropdown(choices=VOICES, value='tom', label="Voice")
            preset_radio = gr.Radio(choices=PRESETS, value=DEFAULT_PRESET, label="Preset (fast recommended for CPU)")
            generate_button = gr.Button("Generate Audio")

    with gr.Row():
         status_output = gr.Textbox(label="Status", interactive=False)

    with gr.Row():
        audio_output = gr.Audio(label="Generated Audio", type="numpy") # type="numpy" expects (sr, ndarray)

    generate_button.click(
        fn=generate_speech_grpc,
        inputs=[text_input, voice_dropdown, preset_radio],
        outputs=[audio_output, status_output] # Output audio first, then status message
    )

# --- Launch the UI ---
if __name__ == "__main__":
    print(f"Attempting to launch Gradio UI...")
    # Share=False for local use, set share=True to get a public link (if needed)
    demo.launch(server_name="0.0.0.0") # Listen on all interfaces if you want to access from another device on your network