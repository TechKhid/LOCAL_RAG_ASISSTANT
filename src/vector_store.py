from opensearchpy import OpenSearch
from src.embeddings import get_embedding

# OpenSearch Client Connection
client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False
)

# Default Index Configuration for k-NN
DEFAULT_CONFIG = {
    "settings": {
        "index": {
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 384
            },
            "source": {"type": "keyword"}
        }
    }
}

def create_vector_index(index_name: str, config: dict = None):
    """
    Create a new k-NN index if it doesn't already exist.
    """
    if config is None:
        config = DEFAULT_CONFIG
        
    if not client.indices.exists(index=index_name):
        print(f"Index '{index_name}' does not exist. Creating...")
        client.indices.create(index=index_name, body=config)
        print(f"Index '{index_name}' created.")
    else:
        print(f"Index '{index_name}' already exists.")

def index_chunks(chunks, embeddings, source, index_name):
    """
    Upload chunks and their embeddings to the specified index.
    """
    for i, (text, embed) in enumerate(zip(chunks, embeddings)):
        client.index(
            index=index_name,
            body={
                "text": text,
                "embedding": embed,
                "source": source
            }
        )

def get_search_stats(response):
    """
    Extract search metadata from OpenSearch response.
    """
    return {
        "took": response.get('took', 0),
        "total_hits": response.get('hits', {}).get('total', {}).get('value', 0)
    }

def print_search_results(hits, stats=None):
    """
    Utility function to print search results in a readable format.
    """
    if stats:
        print(f"Search latency: {stats['took']} ms")
        print(f"Number of results: {len(hits)}")
    print("-" * 60)
    
    for i, hit in enumerate(hits):
        score = hit['_score']
        source = hit['_source'].get('source', 'Unknown')
        text = hit['_source'].get('text', '')
        
        print(f"Result {i+1} | Relevance Score: {score:.4f}")
        print(f"Source: {source}")
        print(f"Content: {text}") 
        print("-" * 60)

def vector_search(query: str, index_name: str, k: int = 5):
    """
    Perform a vector search and return hits and the raw response.
    """
    query_embedding = get_embedding(query)
    response = client.search(
        index=index_name,
        body={
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": k
                    }
                }
            }
        }
    )
    return response['hits']['hits'], response
