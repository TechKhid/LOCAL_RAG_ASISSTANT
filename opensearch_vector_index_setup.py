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

# index_name = "pdf-rag"
# config = {
#             "settings":{
#                 "index":{
#                     "knn":True
#                 }
#             },
#             "mappings":{
#                 "properties": {
#                     "text": {
#                         "type": "knn_vector",
#                         "dimension": 384
#                     },
#                     "source": {"type": "keyword"}
#                 }
#             }
#         }



def create_vector_index(index_name, config):
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name,
                            body= config
                            )



def index_chunks(chunks, embedding, source, index_name):
    for i, (text, embed) in enumerate(zip(chunks, embedding)):
        client.index(
            index=index_name,
            id=i,
            body={
                "text": text,
                "embedding": embed,
                "source": source
            }
        )