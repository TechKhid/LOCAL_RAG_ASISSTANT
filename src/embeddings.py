from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL_NAME

# Load model once at module level
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

def get_embedding(text: str):
    """
    Generate a 384-dimensional embedding for the given text.
    """
    return embedder.encode(text).tolist()
