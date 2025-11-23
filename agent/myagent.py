import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero, groq
from livekit.agents import ChatContext, ChatMessage
from sentence_transformers import SentenceTransformer
import faiss
import asyncio
from functools import partial

load_dotenv()

logger = logging.getLogger("local-agent")
logger.setLevel(logging.INFO)

# load a small embedding model once
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# load all your docs
docs = []
docs_dir = os.path.join(os.path.dirname(__file__), "docs")
if os.path.exists(docs_dir):
    for fn in os.listdir(docs_dir):
        with open(os.path.join(docs_dir, fn), encoding="utf-8") as f:
            docs.append(f.read())

# embed and build FAISS index
if docs:
    embs = embed_model.encode(docs, show_progress_bar=False)
    dim = embs.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embs)
else:
    dim = embed_model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dim)
    logger.warning("No documents found in docs directory. RAG will return empty context.")

async def rag_lookup(query: str) -> str:
    """
    Perform a Retrieval-Augmented Generation (RAG) lookup for a given query.

    Args:
        query (str): The search query to find relevant documents for.

    Returns:
        str: A string containing concatenated relevant document snippets separated by separators,
             or an empty string if no documents are found.
    """
    loop = asyncio.get_running_loop()

    q_emb = await loop.run_in_executor(None, lambda: embed_model.encode([query]))
    D, I = await loop.run_in_executor(None, lambda: index.search(q_emb, min(3, index.ntotal)))

    ctx = ""
    if index.ntotal > 0:
        ctx = "\n\n---\n\n".join(docs[i] for i in I[0])

    print(f"RAG content: {ctx}")

    return ctx

class LocalAgent(Agent):
    """
    A custom Voice Agent class that integrates STT, LLM, TTS, and VAD services.

    This agent handles voice interactions, logging metrics for each component,
    and performing RAG lookups to enhance user queries.
    """
    def __init__(self) -> None:
        """
        Initialize the LocalAgent with specific service configurations.

        Sets up:
        - STT: OpenAI compatible (Whisper)
        - LLM: OpenAI compatible (Ollama)
        - TTS: Groq compatible (Kokoro)
        - VAD: Silero

        Also registers event listeners for metric collection.
        """
        stt = openai.STT(base_url="http://whisper:80/v1", model="Systran/faster-whisper-small")
        llm = openai.LLM(base_url="http://ollama:11434/v1", model="gemma3:4b", timeout=30)
        tts = groq.TTS(base_url="http://kokoro:8880/v1", model="kokoro", voice="af_nova")
        vad_inst = silero.VAD.load()
        super().__init__(
            instructions="""
                You are a helpful agent.
                Never ever use emojis. Everything you say should be in plain text, since it will be spoken out loud.
                Keep your responses short and concise. Never more than a sentence or two.
            """,
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad_inst
        )

        def llm_metrics_wrapper(metrics):
            import asyncio
            asyncio.create_task(self.on_llm_metrics_collected(metrics))
        llm.on("metrics_collected", llm_metrics_wrapper)

        def stt_metrics_wrapper(metrics):
            import asyncio
            asyncio.create_task(self.on_stt_metrics_collected(metrics))
        stt.on("metrics_collected", stt_metrics_wrapper)

        def eou_metrics_wrapper(metrics):
            import asyncio
            asyncio.create_task(self.on_eou_metrics_collected(metrics))
        stt.on("eou_metrics_collected", eou_metrics_wrapper)

        def tts_metrics_wrapper(metrics):
            import asyncio
            asyncio.create_task(self.on_tts_metrics_collected(metrics))
        tts.on("metrics_collected", tts_metrics_wrapper)

        def vad_metrics_wrapper(event):
            import asyncio
            asyncio.create_task(self.on_vad_event(event))
        vad_inst.on("metrics_collected", vad_metrics_wrapper)

    async def on_llm_metrics_collected(self, metrics):
        """
        Handle and log LLM metrics.

        Args:
            metrics: The metrics object containing details about the LLM request
                     (token usage, duration, timestamps, etc.).
        """
        logger.info(f"LLM Metrics: {{" +
            f"'type': {metrics.type}, " +
            f"'label': {metrics.label}, " +
            f"'request_id': {metrics.request_id}, " +
            f"'timestamp': {metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None}, " +
            f"'duration': {metrics.duration}, " +
            f"'ttft': {getattr(metrics, 'ttft', None)}, " +
            f"'cancelled': {getattr(metrics, 'cancelled', None)}, " +
            f"'completion_tokens': {getattr(metrics, 'completion_tokens', None)}, " +
            f"'prompt_tokens': {getattr(metrics, 'prompt_tokens', None)}, " +
            f"'total_tokens': {getattr(metrics, 'total_tokens', None)}, " +
            f"'tokens_per_second': {getattr(metrics, 'tokens_per_second', None)}" +
            "}")

    async def on_stt_metrics_collected(self, metrics):
        """
        Handle and log STT metrics.

        Args:
            metrics: The metrics object containing details about the STT request
                     (duration, speech_id, error status, etc.).
        """
        logger.info(f"STT Metrics: {{" +
            f"'type': {metrics.type}, " +
            f"'label': {metrics.label}, " +
            f"'request_id': {metrics.request_id}, " +
            f"'timestamp': {metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None}, " +
            f"'duration': {metrics.duration}, " +
            f"'speech_id': {getattr(metrics, 'speech_id', None)}, " +
            f"'error': {str(getattr(metrics, 'error', None)) if getattr(metrics, 'error', None) else None}, " +
            f"'streamed': {getattr(metrics, 'streamed', None)}, " +
            f"'audio_duration': {getattr(metrics, 'audio_duration', None)}" +
            "}")

    async def on_eou_metrics_collected(self, metrics):
        """
        Handle and log End of Utterance (EOU) metrics.

        Args:
            metrics: The metrics object containing details about EOU detection
                     (delays, timestamps, etc.).
        """
        logger.info(f"EOU Metrics: {{" +
            f"'type': {metrics.type}, " +
            f"'label': {metrics.label}, " +
            f"'timestamp': {metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None}, " +
            f"'end_of_utterance_delay': {getattr(metrics, 'end_of_utterance_delay', None)}, " +
            f"'transcription_delay': {getattr(metrics, 'transcription_delay', None)}, " +
            f"'speech_id': {getattr(metrics, 'speech_id', None)}, " +
            f"'error': {str(getattr(metrics, 'error', None)) if getattr(metrics, 'error', None) else None}" +
            "}")

    async def on_tts_metrics_collected(self, metrics):
        """
        Handle and log TTS metrics.

        Args:
            metrics: The metrics object containing details about the TTS request
                     (ttfb, duration, audio duration, character count, etc.).
        """
        logger.info(f"TTS Metrics: {{" +
            f"'type': {metrics.type}, " +
            f"'label': {metrics.label}, " +
            f"'request_id': {metrics.request_id}, " +
            f"'timestamp': {metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None}, " +
            f"'ttfb': {getattr(metrics, 'ttfb', None)}, " +
            f"'duration': {metrics.duration}, " +
            f"'audio_duration': {getattr(metrics, 'audio_duration', None)}, " +
            f"'cancelled': {getattr(metrics, 'cancelled', None)}, " +
            f"'characters_count': {getattr(metrics, 'characters_count', None)}, " +
            f"'streamed': {getattr(metrics, 'streamed', None)}, " +
            f"'speech_id': {getattr(metrics, 'speech_id', None)}, " +
            f"'error': {str(getattr(metrics, 'error', None)) if getattr(metrics, 'error', None) else None}" +
            "}")

    async def on_vad_event(self, event):
        """
        Handle VAD (Voice Activity Detection) events.

        Args:
            event: The VAD event object.
        """
        None

    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage,
    ) -> None:
        """
        Callback triggered when a user finishes a turn (speaks a message).

        This method performs a RAG lookup based on the user's message and,
        if relevant content is found, injects it into the chat context
        as additional information for the agent to use in its response.

        Args:
            turn_ctx (ChatContext): The context of the current chat turn.
            new_message (ChatMessage): The message that the user just completed.
        """
        rag_content = await rag_lookup(new_message.text_content)
        if rag_content:
            turn_ctx.add_message(
                role="user",
                content=f"Additional information relevant to the user's next message: {rag_content}"
            )
            logger.info(f"Added RAG content to chat context: {rag_content}")

async def entrypoint(ctx: JobContext):
    """
    The main entrypoint for the worker job.

    Connects to the job context, creates an AgentSession, and starts the LocalAgent.

    Args:
        ctx (JobContext): The context for the current job, provided by LiveKit.
    """
    await ctx.connect()

    session = AgentSession()

    await session.start(
        agent=LocalAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, job_memory_warn_mb=1500))
