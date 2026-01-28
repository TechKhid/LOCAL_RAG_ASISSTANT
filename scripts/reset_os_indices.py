import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vector_store import client

def reset_index(index_name):
    if client.indices.exists(index=index_name):
        print(f"Deleting existing index '{index_name}'...")
        client.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted.")
    else:
        print(f"Index '{index_name}' does not exist.")

if __name__ == "__main__":
    reset_index("pdf-rag")
    reset_index("pdf-rag-testing")
