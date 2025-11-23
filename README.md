<div align="center">
  <img src="./voice-assistant-frontend/.github/assets/app-icon.png" alt="App Icon" width="80" />
  <h1>🧠 Local Voice Agent</h1>
  <p>A full-stack, Dockerized AI voice assistant with speech, text, and voice synthesis powered by <a href="https://livekit.io?utm_source=demo">LiveKit</a>.</p>
</div>

[Demo Video](https://github.com/user-attachments/assets/67a76e94-aacb-4087-b09c-d4e46d8e695e)

## 🧩 Overview

This repository contains a complete, self-hosted solution for running a real-time AI voice assistant on your local machine. It orchestrates multiple services to provide low-latency speech-to-text, large language model processing, and text-to-speech synthesis, all integrated via the LiveKit real-time infrastructure.

Key technologies include:
- 🎙️ **LiveKit Agents** for orchestrating STT ↔ LLM ↔ TTS pipelines.
- 🧠 **Ollama** for running local LLMs (configured for `gemma3:4b` by default).
- 🗣️ **Kokoro** for high-quality, local TTS voice synthesis.
- 👂 **Whisper (via VoxBox)** for accurate, local speech-to-text transcription.
- 🔍 **RAG (Retrieval-Augmented Generation)** powered by Sentence Transformers and FAISS for context-aware responses.
- 💬 **Next.js + Tailwind** frontend UI for a polished user experience.
- 🐳 **Docker Compose** for easy deployment and networking of all services.

## 🏁 Quick Start

The easiest way to get up and running is using the provided test script, which handles container cleanup, building, and launching.

### Prerequisites
- **Docker** and **Docker Compose** installed and running.
- **Git** to clone the repository.
- Recommended Hardware: 12GB+ RAM (since multiple AI models run locally). No dedicated GPU is strictly required as models are CPU-optimized, but it helps.

### Setup & Run

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Run the startup script:**
    ```bash
    ./test.sh
    ```

    This script will:
    - Stop and remove any existing containers related to this project.
    - Build the Docker images for the agent, frontend, and other services.
    - Start the entire stack using `docker-compose`.

3.  **Access the Assistant:**
    Once the services are running, open your browser and navigate to:
    [http://localhost:3000](http://localhost:3000)

    Click "Start a conversation" to begin talking to your local AI agent!

## 📦 Architecture

The system is composed of several Docker containers communicating over a shared network:

| Service | Description | Port (Internal) |
| :--- | :--- | :--- |
| `livekit` | The WebRTC signaling server that manages real-time audio/video connections. | 7880 |
| `agent` | Custom Python application (`myagent.py`) using LiveKit SDK to manage the conversation flow. | - |
| `whisper` | Hosting the Whisper model for Speech-to-Text (STT). | 80 |
| `ollama` | Hosting the LLM (e.g., Gemma) for text generation. | 11434 |
| `kokoro` | Hosting the Kokoro model for Text-to-Speech (TTS). | 8880 |
| `frontend` | Next.js web application for the user interface. | 3000 |

## 🧠 Agent Implementation & RAG

The core logic resides in [`agent/myagent.py`](./agent/myagent.py).

### Pipeline
The agent constructs a pipeline connecting:
1.  **STT**: `openai.STT` client points to the local `whisper` service.
2.  **LLM**: `openai.LLM` client points to the local `ollama` service.
3.  **TTS**: `groq.TTS` client points to the local `kokoro` service.
4.  **VAD**: `silero.VAD` handles Voice Activity Detection to know when you stop speaking.

### Retrieval-Augmented Generation (RAG)
To give the agent knowledge beyond its training data:
- Place text files (`.txt`) in the `agent/docs/` directory.
- On startup, the agent loads these files.
- It creates embeddings using `SentenceTransformer("all-MiniLM-L6-v2")`.
- A `FAISS` index is built for fast similarity searching.
- When you speak, the agent queries this index and injects relevant context into the prompt before the LLM generates a response.

## 🔐 Environment Variables

Configuration is managed via `.env` files.

- **Root `.env`**: Global settings.
- **`agent/.env`**: Specific to the Python agent (API keys, URLs).
- **`voice-assistant-frontend/.env.example`**: Template for the frontend.

Key variables include service URLs (e.g., `http://ollama:11434/v1`) and LiveKit credentials. For local development, the defaults provided in the repo usually work out of the box.

## 🧪 Testing & Development

If you are modifying the code:

### Backend (Agent)
Edit `agent/myagent.py`. To apply changes, restart the agent container:
```bash
docker-compose restart agent
```

### Frontend
Edit files in `voice-assistant-frontend/`. Changes in Next.js dev mode (if running locally outside Docker) are instant. If running via Docker, rebuild:
```bash
docker-compose build frontend
docker-compose up -d frontend
```

### Full Restart
To tear down everything and rebuild:
```bash
docker-compose down -v --remove-orphans
docker-compose up --build
```

## 🧰 Project Structure

```
.
├── agent/                      # Python agent code
│   ├── docs/                   # Documents for RAG
│   ├── myagent.py              # Main agent logic
│   └── Dockerfile              # Agent container setup
├── ollama/                     # LLM service configuration
├── whisper/                    # STT service configuration
├── livekit/                    # LiveKit server configuration
├── voice-assistant-frontend/   # Next.js React application
│   ├── app/                    # App router pages and layouts
│   ├── components/             # React UI components
│   └── hooks/                  # Custom React hooks
└── docker-compose.yml          # Service orchestration
```

## 📷 Screenshots

![UI Screenshot](./voice-assistant-frontend/.github/assets/frontend-screenshot.jpeg)

## 🛠️ Requirements

- **Docker Desktop** (or Engine + Compose)
- **Resources**: ~12GB RAM recommended.
  - *Note:* The initial build and model download (Ollama, Whisper, Kokoro) might take some time depending on your internet connection.

## 🙌 Credits

- Powered by [LiveKit](https://livekit.io/) and [LiveKit Agents](https://docs.livekit.io/agents/).
- Local LLM inference by [Ollama](https://ollama.com/).
- Text-to-Speech by [Kokoro](https://github.com/remsky/kokoro).
