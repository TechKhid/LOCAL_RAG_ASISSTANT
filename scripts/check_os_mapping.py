import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vector_store import client

def check_mapping(index_name):
    try:
        mapping = client.indices.get_mapping(index=index_name)
        print(json.dumps(mapping, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Checking mappings for indices...")
    for idx in ["pdf-rag", "pdf-rag-testing"]:
        print(f"\n--- {idx} ---")
        check_mapping(idx)
