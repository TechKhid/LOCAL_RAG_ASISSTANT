import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text
  
def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    return splitter.split_text(text)