from opensearchpy import OpenSearch
import json

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False
)

def check_mapping(index_name):
    try:
        mapping = client.indices.get_mapping(index=index_name)
        print(json.dumps(mapping, indent=2))
    except Exception as e:
        print(f"Error: {e}")

# if __name__ == "__main__":
#     print("Mapping for pdf-rag:")
#     check_mapping("pdf-rag")
#     print("\nMapping for pdf-rag-testing:")
#     check_mapping("pdf-rag-testing")
