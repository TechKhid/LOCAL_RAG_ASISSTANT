from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False
)

def reset_index(index_name):
    if client.indices.exists(index=index_name):
        print(f"Deleting existing index '{index_name}'...")
        client.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted.")
    else:
        print(f"Index '{index_name}' does not exist.")

# if __name__ == "__main__":
#     reset_index("pdf-rag")
