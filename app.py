import torch
import torchaudio
import os
import time

try:
    # Imports for the original Tortoise TTS library
    from tortoise.api import TextToSpeech
    from tortoise.utils.audio import load_audio, load_voice, load_voices
except ImportError:
    print("Error: Tortoise TTS library not found.")
    print("Please ensure you have installed it correctly by following the instructions")
    print("in the original Tortoise TTS repository (https://github.com/neonbjb/tortoise-tts).")
    exit()

# --- Configuration ---
text_to_speak = "Hello, this is a test using Tortoise TTS on the CPU. It might take a very long time."
# Use a built-in voice preset like 'random', 'tom', 'freeman', etc.
# 'random' generates a unique voice each time.
# Using a specific voice requires its samples (downloaded automatically).
voice_to_use = 'tom'
# Presets: 'ultra_fast', 'fast', 'standard', 'high_quality'
# Use 'ultra_fast' or 'fast' for CPU, 'standard' or 'high_quality' are impractically slow.
preset = "ultra_fast"
output_filename = "tortoise_cpu_output.wav"
# ---------------------

print("Initializing TextToSpeech...")
# This will automatically use CPU if CUDA is not available or if PyTorch is CPU-only.
# It will attempt to download models on the first run.
try:
    tts = TextToSpeech(use_deepspeed=False, kv_cache=True) # DeepSpeed is GPU-only
except Exception as e:
    print(f"Error initializing TextToSpeech: {e}")
    print("This might be due to missing models or installation issues.")
    exit()

print(f"Using voice: {voice_to_use}")
# Load voice samples (if not 'random'). This also downloads voice samples on first use.
# `load_voice` returns samples and conditioning latents specific to that voice.
try:
    if voice_to_use != 'random':
        voice_samples, conditioning_latents = load_voice(voice_to_use)
    else:
        # For 'random', we don't need specific samples/latents beforehand
        voice_samples, conditioning_latents = None, None
except KeyError:
    print(f"Error: Voice '{voice_to_use}' not found.")
    print(f"Ensure the voice exists in the 'tortoise/voices/' directory or use 'random'.")
    exit()
except Exception as e:
    print(f"Error loading voice '{voice_to_use}': {e}")
    exit()


print(f"Generating speech using '{preset}' preset (this will be slow on CPU)...")
start_time = time.time()

# Generate speech
# For random voice: tts.tts(...) or tts.tts_with_preset(..., voice_samples=None, conditioning_latents=None)
# For specific voice: use the loaded voice_samples and conditioning_latents
try:
    gen = tts.tts_with_preset(
        text=text_to_speak,
        voice_samples=voice_samples,
        conditioning_latents=conditioning_latents,
        preset=preset,
        # Optional: You might need to explicitly provide k=1 for single output when using specific voices
        k=1 if voice_to_use != 'random' else 1 # Default is 1 for tts_with_preset anyway
    )

    # Ensure output is on CPU before saving
    if isinstance(gen, tuple): # If multiple candidates were generated (less likely with k=1)
       speech_output = gen[0].squeeze(0).cpu()
    else:
       speech_output = gen.squeeze(0).cpu()

except Exception as e:
    print(f"Error during speech generation: {e}")
    exit()

end_time = time.time()
print(f"Speech generated in {end_time - start_time:.2f} seconds.")

# Save the audio
# Tortoise generates audio at 24000 Hz
sampling_rate = 24000
print(f"Saving audio to {output_filename} (Sample Rate: {sampling_rate} Hz)")
torchaudio.save(output_filename, speech_output, sampling_rate)

print("Done.")