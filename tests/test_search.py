import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vector_store import vector_search, print_search_results, get_search_stats

if __name__ == "__main__":
    query = "What is Samuel Mensah's experience with AI?"
    index_name = "test-ingestion-index"
    
    print(f"Searching for: '{query}'")
    hits, response = vector_search(query, index_name, k=5)
    stats = get_search_stats(response)
    print_search_results(hits, stats)
