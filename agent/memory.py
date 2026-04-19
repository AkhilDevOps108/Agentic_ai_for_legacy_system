"""Conversation memory for the agent — keeps a sliding window of interactions."""

from langchain_classic.memory import ConversationBufferWindowMemory

from config.settings import settings


def create_memory() -> ConversationBufferWindowMemory:
    """Create a short-term conversation memory (last k interactions)."""
    return ConversationBufferWindowMemory(
        k=settings.memory_window_size,
        return_messages=True,
        memory_key="chat_history",
        input_key="input",
        output_key="output",
    )
