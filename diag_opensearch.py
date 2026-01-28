from opensearch_vector_index_setup import client
import json

try:
    print("--- Cluster Info ---")
    print(json.dumps(client.info(), indent=2))
    
    print("\n--- Plugins ---")
    # Using low-level transport for plugins check
    plugins = client.transport.perform_request("GET", "/_cat/plugins?v&s=component&h=name,component,version,description")
    print(plugins)
    
    for index in ["pdf-rag-testing", "pdf-rag"]:
        print(f"\n--- {index} ---")
        if client.indices.exists(index=index):
            settings = client.indices.get_settings(index=index)
            print("Settings:")
            print(json.dumps(settings, indent=2))
            
            mapping = client.indices.get_mapping(index=index)
            print("Mapping:")
            print(json.dumps(mapping, indent=2))
        else:
            print("Index does not exist.")

except Exception as e:
    print(f"Error: {e}")
