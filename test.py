from opensearch_vector_index_setup import create_vector_index

index_name = "pdf-rag-testing"
config = {
            "settings":{
                "index":{
                    "knn":True
                }
            },
            "mappings":{
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

create_vector_index(index_name, config)
