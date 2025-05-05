# Gradio UI for Tortoise TTS via gRPC

## Description

This project provides a simple web interface using Gradio to interact with the Tortoise Text-to-Speech (TTS) model. Instead of running the model directly within the Gradio app, it communicates with a separate backend gRPC server that handles the actual TTS inference using the original Tortoise TTS implementation (`neonbjb/tortoise-tts`).

This setup separates the user interface from the potentially resource-intensive TTS model, allowing them to run on different processes (or even different machines, though this setup assumes localhost).

**Note:** This configuration uses the CPU for Tortoise TTS inference, which is **extremely slow**. Generation times can range from several minutes to much longer depending on the text length and preset. GPU usage is highly recommended for practical use of Tortoise TTS.

## Architecture

The project consists of two main components:

1.  **gRPC Server (`tts_server.py`):**
    * Loads the Tortoise TTS model on startup.
    * Listens for incoming gRPC requests.
    * Implements a `Synthesize` method that takes text, voice, and preset parameters.
    * Performs TTS inference using the Tortoise library.
    * Returns the generated audio data as bytes.
2.  **Gradio UI (`app.py`):**
    * Provides a web interface with fields for text input, voice selection, and preset selection.
    * Acts as a gRPC client.
    * When the user clicks "Generate", it sends a request to the gRPC server.
    * Receives the audio data response and displays it using a Gradio Audio component.
3.  **gRPC Definition (`tts.proto`):**
    * Defines the service contract, request message, and response message used for communication between the server and client.

## Prerequisites

* **Python:** Version 3.10 is required (as used during setup).
* **Git:** Required for cloning the Tortoise TTS repository.
* **Tortoise TTS Hardware Requirements:** While this setup runs on CPU, the original Tortoise TTS project strongly recommends an NVIDIA GPU (with ~6GB+ VRAM) for reasonable inference times. CPU inference will be **very slow**.
* **(Windows Optional but Recommended for Tortoise):** Conda/Miniconda can sometimes help manage Tortoise dependencies more easily than pure pip on Windows.

## Setup & Installation

1.  **Clone this Project:**
    ```bash
    # If you haven't already, put app.py, tts_server.py, tts.proto
    # in a dedicated project folder.
    cd path/to/your/TTS_Project_Folder
    ```

2.  **Clone Original Tortoise TTS:**
    * Clone the repository from neonbjb (James Betker). It contains the core TTS code.
    ```bash
    git clone [https://github.com/neonbjb/tortoise-tts.git](https://github.com/neonbjb/tortoise-tts.git)
    ```
    * *Important:* Before installing Tortoise requirements, you need to modify its `requirements.txt` file if you are targeting CPU-only on Windows.
        * Navigate into the cloned tortoise directory: `cd tortoise-tts`
        * Open `requirements.txt` in a text editor.
        * Find the line `deepspeed==0.8.3` (or similar) and **delete** or **comment it out** (add `#` at the beginning). This dependency fails to install on Windows without specific Linux libraries and isn't needed for CPU inference.
        * Save the modified `requirements.txt`.
        * Navigate back to your main project directory: `cd ..`

3.  **Create Python 3.10 Virtual Environment:**
    ```bash
    # Ensure Python 3.10 is accessible (e.g., via `py -3.10` or as default `python`)
    py -3.10 -m venv .venv
    ```

4.  **Activate Virtual Environment:**
    * **Windows CMD:** `.venv\Scripts\activate.bat`
    * **Windows PowerShell:** `.venv\Scripts\Activate.ps1` (You might need to adjust execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)
    * **(Linux/macOS):** `source .venv/bin/activate`
    * Your terminal prompt should now start with `(.venv)`.

5.  **Install Tortoise TTS and its Dependencies:**
    * Navigate into the cloned Tortoise directory:
        ```bash
        cd tortoise-tts
        ```
    * Install its requirements (using the modified file):
        ```bash
        pip install -r requirements.txt
        ```
    * Install the Tortoise library itself:
        ```bash
        python setup.py install
        ```
    * Navigate back to your main project directory:
        ```bash
        cd ..
        ```

6.  **Install Project-Specific Dependencies:**
    * Create a `requirements.txt` file in your main project directory (`TTS_Project_Folder`) with the following content:
        ```txt
        gradio==3.50.2
        grpcio
        grpcio-tools
        soundfile
        numpy
        # Note: torch, torchaudio, transformers, etc., are installed
        # as dependencies of Tortoise TTS in the previous step.
        ```
    * Install these dependencies:
        ```bash
        pip install -r requirements.txt
        ```

7.  **Compile Protobuf Definition:**
    * Make sure you are in your main project directory (`TTS_Project_Folder`) where `tts.proto` is located.
    * Run the gRPC compilation command:
        ```bash
        python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. tts.proto
        ```
    * This will create `tts_pb2.py` and `tts_pb2_grpc.py`.

## Running the Application

You need to run the server and the UI app in separate terminals. Make sure the virtual environment is activated in **both** terminals.

1.  **Start the gRPC Server:**
    * Open a terminal, navigate to your project folder, and activate the environment (`.venv\Scripts\activate`).
    * Run the server script:
        ```bash
        python tts_server.py
        ```
    * Wait for the output indicating the Tortoise model has initialized and the server is listening (e.g., `Starting gRPC server listening on [::]:50051`). This step might take some time and consume significant RAM as it loads the model.

2.  **Start the Gradio UI:**
    * Open a **second** terminal, navigate to your project folder, and activate the **same** environment (`.venv\Scripts\activate`).
    * Run the Gradio app script:
        ```bash
        python app.py
        ```
    * Look for the output line like `Running on local URL: http://0.0.0.0:7860`.
    * Open your web browser and navigate to `http://localhost:7860` or `http://127.0.0.1:7860`.

3.  **Use the UI:**
    * Enter text, select a voice and preset (use 'fast' or 'ultra_fast' for CPU).
    * Click "Generate Audio".
    * **Be patient!** The UI might seem unresponsive while the backend server processes the request on the CPU. Check the server terminal for progress logs. The generated audio will appear once complete.

## Known Issues & Limitations

* **CPU Performance:** Inference using Tortoise TTS on a CPU is **extremely slow**. Expect long waits for audio generation.
* **UI Responsiveness:** The Gradio UI uses a synchronous gRPC call in this example. This means the UI will freeze while waiting for the server to generate the audio. For better responsiveness, asynchronous handling (e.g., using `asyncio` with Gradio and gRPC) would be needed but adds complexity.
* **Model Downloads:** Tortoise downloads large model files (~5GB+) on the first run or when a new voice is used for the first time. Ensure sufficient disk space and internet connection.
* **Tortoise Installation:** Setting up the original Tortoise TTS can sometimes be tricky due to its dependencies. Refer to the official `neonbjb/tortoise-tts` repository if you encounter issues during its installation step.

## File Structure (Example)