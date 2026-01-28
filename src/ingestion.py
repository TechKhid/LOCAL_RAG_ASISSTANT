import os
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.embeddings import get_embedding
from src.vector_store import create_vector_index, index_chunks

def load_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text

def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150):
    """Split text into manageable chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)

def ingest_pdf(file_path: str, index_name: str, source_label: str = None):
    """
    End-to-end ingestion: Load -> Chunk -> Embed -> Index.
    """
    if source_label is None:
        source_label = file_path
        
    print(f"[*] Processing: {source_label}")
    text = load_pdf(file_path)
    chunks = chunk_text(text)
    
    print(f"[*] Generating embeddings for {len(chunks)} chunks...")
    embeddings = [get_embedding(chunk) for chunk in chunks]
    
    create_vector_index(index_name)
    
    print(f"[*] Indexing into OpenSearch index: {index_name}")
    index_chunks(chunks, embeddings, source_label, index_name)
    print("[+] Ingestion complete.")
