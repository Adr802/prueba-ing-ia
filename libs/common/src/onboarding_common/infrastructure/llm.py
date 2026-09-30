import os

from langchain_groq import ChatGroq


def groq_chat_model() -> ChatGroq:
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0,
        timeout=20,
        max_retries=1,
    )
