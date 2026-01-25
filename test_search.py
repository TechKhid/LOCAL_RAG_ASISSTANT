from opensearch_vector_index_setup import vector_search

if __name__ == "__main__":
    query = "What is Samuel Mensah's experience with AI?"
    index_name = "pdf-rag-testing"
    
    print(f"Searching for: '{query}'")
    vector_search(query, index_name, k=5)
