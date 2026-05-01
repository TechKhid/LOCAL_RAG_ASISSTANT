from functools import lru_cache
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from src.config import (
    EMBEDDING_BASE_URL,
    EMBEDDING_MODEL_NAME,
    use_remote_embeddings,
)


@lru_cache(maxsize=1)
def get_sentence_transformer() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


@lru_cache(maxsize=1)
def get_embedding_client() -> OpenAI:
    return OpenAI(base_url=EMBEDDING_BASE_URL, api_key="local-not-required")


def get_embedding(text: str) -> list[float]:
    """
    Generate an embedding using either a local sentence-transformers model
    or an OpenAI-compatible embeddings endpoint such as LM Studio.
    """
    if use_remote_embeddings():
        response = get_embedding_client().embeddings.create(
            model=EMBEDDING_MODEL_NAME,
            input=text,
        )
        return response.data[0].embedding

    return get_sentence_transformer().encode(text).tolist()
