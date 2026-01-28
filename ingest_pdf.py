import os
from pdf_load_chunking import load_pdf, chunk_text
from text_embedding import get_embedding
from opensearch_vector_index_setup import create_vector_index, index_chunks

def ingest(file_path, index_name, source_label=None):
    if source_label is None:
        source_label = file_path
        
    print(f"Loading {file_path}...")
    text = load_pdf(file_path)
    
    print("Chunking text...")
    chunks = chunk_text(text)
    
    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = [get_embedding(chunk) for chunk in chunks]
    
    create_vector_index(index_name)
    
    print("Indexing chunks...")
    index_chunks(chunks, embeddings, source_label, index_name)
    print("Ingestion complete.")


# if __name__ == "__main__": 
#     # Use a sample PDF if it exists, otherwise use a placeholder or prompt
#     sample_pdf = r"Samuel Mensah - AI_ML Engineer CV.pdf" # Using one found in find_by_name
#     if os.path.exists(sample_pdf):
#         ingest(sample_pdf, "pdf-rag-testing")
#     else:
#         print(f"File {sample_pdf} not found. Please provide a valid PDF path.")
