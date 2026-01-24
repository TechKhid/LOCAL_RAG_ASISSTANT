from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{
        "host": "localhost", 
        "port": 9200
        }],
    http_compress=True,
    use_ssl=False,
    verify_certs=False
)

index_name = "pdf-rag"


if not client.indices.exists(index=index_name):
    client.indices.create(index=index_name,
                          body={
                              "settings":{
                                  "index":{
                                      "knn":True
                                  }
                              },
                              "mappings":{
                                  "properties": {
                                      "text": {
                                          "type": "knn_vector",
                                          "dimension": 384
                                      },
                                      "source": {"type": "keyword"}
                                  }
                              }
                          }
                        )