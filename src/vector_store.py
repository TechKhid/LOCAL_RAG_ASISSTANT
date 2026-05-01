from opensearchpy import OpenSearch
from src.config import get_opensearch_client_config
from src.embeddings import get_embedding

# OpenSearch Client Connection
client = OpenSearch(**get_opensearch_client_config())

def build_index_config(dimension: int) -> dict:
    return {
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
                    "dimension": dimension
                },
                "source": {"type": "keyword"}
            }
        }
    }

def create_vector_index(index_name: str, dimension: int, config: dict = None):
    """
    Create a new k-NN index if it doesn't already exist.
    """
    if config is None:
        config = build_index_config(dimension)
        
    if not client.indices.exists(index=index_name):
        print(f"Index '{index_name}' does not exist. Creating...")
        client.indices.create(index=index_name, body=config)
        print(f"Index '{index_name}' created.")
    else:
        mapping = client.indices.get_mapping(index=index_name)
        existing_dimension = (
            mapping.get(index_name, {})
            .get("mappings", {})
            .get("properties", {})
            .get("embedding", {})
            .get("dimension")
        )
        if existing_dimension is not None and existing_dimension != dimension:
            raise ValueError(
                f"Index '{index_name}' already exists with embedding dimension "
                f"{existing_dimension}, but the current embedding model produces "
                f"{dimension}-dimensional vectors. Reset the index or use a "
                f"matching embedding model."
            )
        print(f"Index '{index_name}' already exists.")

def index_chunks(chunks, embeddings, source, index_name):
    """
    Upload chunks and their embeddings to the specified index.
    """
    for text, embed in zip(chunks, embeddings):
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

def get_index_summary(index_name: str) -> dict:
    if not client.indices.exists(index=index_name):
        return {
            "exists": False,
            "index_name": index_name,
            "document_count": 0,
            "source_count": 0,
            "sources": [],
        }

    count = client.count(index=index_name)["count"]
    response = client.search(
        index=index_name,
        body={
            "size": 0,
            "aggs": {
                "sources": {
                    "terms": {
                        "field": "source",
                        "size": 25
                    }
                }
            }
        }
    )
    buckets = response.get("aggregations", {}).get("sources", {}).get("buckets", [])

    return {
        "exists": True,
        "index_name": index_name,
        "document_count": count,
        "source_count": len(buckets),
        "sources": [
            {
                "name": bucket["key"],
                "chunk_count": bucket["doc_count"],
            }
            for bucket in buckets
        ],
    }
