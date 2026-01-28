from sentence_transformers import SentenceTransformer

# Load model once at module level
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str):
    """
    Generate a 384-dimensional embedding for the given text.
    """
    return embedder.encode(text).tolist()
