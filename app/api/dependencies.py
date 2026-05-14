from openai import OpenAI
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Lazy-load OpenAI client as dependency."""
    return OpenAI(api_key=OPENAI_API_KEY)
