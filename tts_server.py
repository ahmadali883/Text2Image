import grpc
from concurrent import futures
import time
import torch
import numpy as np

# Generated gRPC files
import tts_pb2
import tts_pb2_grpc

# Tortoise TTS imports
try:
    from tortoise.api import TextToSpeech
    from tortoise.utils.audio import load_voice
except ImportError:
    print("Error: Tortoise TTS library not found.")
    print("Ensure Tortoise TTS is installed correctly (check original repo).")
    exit()

# --- Server Configuration ---
_ONE_DAY_IN_SECONDS = 60 * 60 * 24
SERVER_ADDRESS = 'localhost:50051'
TORTOISE_SAMPLE_RATE = 24000 # Tortoise standard output SR
# --------------------------

print("Initializing Tortoise TTS model...")
# Load the model when the server starts. This might take time and memory.
# Ensure PyTorch uses CPU if no compatible GPU detected or desired.
# use_deepspeed=False because we removed it / it's not suitable for CPU/Windows
try:
    tts_model = TextToSpeech(use_deepspeed=False, kv_cache=True)
    print("Tortoise TTS model initialized successfully.")
except Exception as e:
    print(f"Failed to initialize Tortoise TTS model: {e}")
    exit()

# --- Implement the gRPC Service ---
class TTSServiceServicer(tts_pb2_grpc.TTSServiceServicer):
    def Synthesize(self, request, context):
        print(f"Received request: voice='{request.voice}', preset='{request.preset}'")
        print(f"Text: '{request.text[:50]}...'") # Log truncated text

        start_time = time.time()
        try:
            # Load voice data
            if request.voice == 'random':
                voice_samples, conditioning_latents = None, None
            else:
                try:
                    # Attempt to load the specific voice
                    voice_samples, conditioning_latents = load_voice(request.voice)
                except KeyError:
                    msg = f"Voice '{request.voice}' not found."
                    print(f"Error: {msg}")
                    context.set_details(msg)
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    return tts_pb2.SynthesizeResponse()
                except Exception as e_load:
                     msg = f"Failed loading voice '{request.voice}': {e_load}"
                     print(f"Error: {msg}")
                     context.set_details(msg)
                     context.set_code(grpc.StatusCode.INTERNAL)
                     return tts_pb2.SynthesizeResponse()

            # Generate speech using Tortoise
            gen = tts_model.tts_with_preset(
                text=request.text,
                voice_samples=voice_samples,
                conditioning_latents=conditioning_latents,
                preset=request.preset,
                k=1 # Generate only one candidate
            )

            # Ensure output tensor is on CPU and get raw bytes
            # Tortoise output is typically float32
            if isinstance(gen, tuple):
                speech_tensor = gen[0].squeeze(0).cpu()
            else:
                speech_tensor = gen.squeeze(0).cpu()

            audio_bytes = speech_tensor.numpy().astype(np.float32).tobytes()
            processing_time = time.time() - start_time
            print(f"Synthesized audio in {processing_time:.2f} seconds.")

            return tts_pb2.SynthesizeResponse(
                audio_content=audio_bytes,
                sample_rate=TORTOISE_SAMPLE_RATE
            )

        except Exception as e_synth:
            msg = f"Error during synthesis: {e_synth}"
            print(f"Error: {msg}")
            context.set_details(msg)
            context.set_code(grpc.StatusCode.INTERNAL)
            return tts_pb2.SynthesizeResponse()

# --- Start the Server ---
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2)) # Limit workers due to CPU load
    tts_pb2_grpc.add_TTSServiceServicer_to_server(TTSServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print(f"Starting gRPC server listening on {SERVER_ADDRESS}")
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        print("Stopping server...")
        server.stop(0)

if __name__ == '__main__':
    serve()