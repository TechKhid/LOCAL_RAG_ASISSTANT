from opensearch_vector_index_setup import client
import json

try:
    print("--- Cluster Info ---")
    print(json.dumps(client.info(), indent=2))
    
    print("\n--- Plugins ---")
    # Using low-level transport for plugins check
    plugins = client.transport.perform_request("GET", "/_cat/plugins?v&s=component&h=name,component,version,description")
    print(plugins)
    
    print("\n--- Index Settings (pdf-rag-testing) ---")
    settings = client.indices.get_settings(index="pdf-rag-testing")
    print(json.dumps(settings, indent=2))
    
    print("\n--- Index Mapping (pdf-rag-testing) ---")
    mapping = client.indices.get_mapping(index="pdf-rag-testing")
    print(json.dumps(mapping, indent=2))

except Exception as e:
    print(f"Error: {e}")
