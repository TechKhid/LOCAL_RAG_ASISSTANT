import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_engine import RAGEngine

def test_query():
    prompt_path = os.path.join("prompts", "rag_v1.json")
    engine = RAGEngine("http://localhost:1234/v1", prompt_path)
    
    query = "What is Samuel's experience?"
    index_name = "test-ingestion-index"
    
    print(f"Testing RAG query: '{query}'")
    reply, stats, sources, search_stats = engine.query(query, index_name)
    
    print(f"\nAssistant: {reply}")
    print(f"Stats: {stats}")
    print(f"Search Stats: {search_stats}")

if __name__ == "__main__":
    test_query()
