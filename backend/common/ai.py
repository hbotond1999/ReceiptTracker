import os

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

def get_llm_model(temperature: int = 0) -> BaseChatModel:
    """
    Args:
        temperature: The temperature setting for the model that affects the randomness of responses. Defaults to 0.

    Returns:
        An instance of BaseChatModel specific to the LLM provider.
    """


    return ChatOpenAI(model=os.getenv("AI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"), temperature=temperature)