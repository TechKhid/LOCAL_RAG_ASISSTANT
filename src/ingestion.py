from typing import Callable, Optional
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.embeddings import get_embedding
from src.vector_store import create_vector_index, index_chunks

ProgressCallback = Callable[[dict], None]

def emit_progress(progress_callback: Optional[ProgressCallback], **payload) -> None:
    if progress_callback is not None:
        progress_callback(payload)

def iter_pdf_page_text(file_path: str):
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        for page_number, page in enumerate(doc, start=1):
            yield page_number, total_pages, page.get_text()
    finally:
        doc.close()

def load_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    for _, _, page_text in iter_pdf_page_text(file_path):
        text += page_text + "\n"
    return text

def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150):
    """Split text into manageable chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)

def ingest_pdf(
    file_path: str,
    index_name: str,
    source_label: str = None,
    progress_callback: Optional[ProgressCallback] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    batch_size: int = 24,
):
    """
    End-to-end ingestion that streams page-by-page instead of materializing the
    entire document text in memory.
    """
    if source_label is None:
        source_label = file_path

    print(f"[*] Processing: {source_label}")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks_indexed = 0
    has_chunks = False
    index_ready = False

    for page_number, total_pages, page_text in iter_pdf_page_text(file_path):
        emit_progress(
            progress_callback,
            stage="extracting",
            page_number=page_number,
            total_pages=total_pages,
            chunks_indexed=chunks_indexed,
            source_label=source_label,
        )
        if not page_text.strip():
            continue

        page_chunks = [
            chunk for chunk in splitter.split_text(page_text)
            if chunk.strip()
        ]
        if not page_chunks:
            continue

        has_chunks = True
        for start in range(0, len(page_chunks), batch_size):
            batch_chunks = page_chunks[start:start + batch_size]
            emit_progress(
                progress_callback,
                stage="embedding",
                page_number=page_number,
                total_pages=total_pages,
                batch_size=len(batch_chunks),
                chunks_indexed=chunks_indexed,
                source_label=source_label,
            )
            embeddings = [get_embedding(chunk) for chunk in batch_chunks]

            if not index_ready:
                create_vector_index(index_name, dimension=len(embeddings[0]))
                index_ready = True

            emit_progress(
                progress_callback,
                stage="indexing",
                page_number=page_number,
                total_pages=total_pages,
                batch_size=len(batch_chunks),
                chunks_indexed=chunks_indexed,
                source_label=source_label,
            )
            index_chunks(batch_chunks, embeddings, source_label, index_name)
            chunks_indexed += len(batch_chunks)

    if not has_chunks:
        raise ValueError("No text chunks were generated from the PDF.")

    print("[+] Ingestion complete.")
    emit_progress(
        progress_callback,
        stage="completed",
        page_number=0,
        total_pages=0,
        chunks_indexed=chunks_indexed,
        source_label=source_label,
    )
