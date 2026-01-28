import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion import ingest_pdf

def test_ingestion():
    # Use the CV found in the workspace root
    sample_pdf = "Samuel Mensah - AI_ML Engineer CV.pdf"
    index_name = "test-ingestion-index"
    
    if os.path.exists(sample_pdf):
        print(f"[*] Testing ingestion with: {sample_pdf}")
        try:
            ingest_pdf(sample_pdf, index_name)
            print(f"[+] Successfully created and populated index: {index_name}")
        except Exception as e:
            print(f"[!] Ingestion failed: {str(e)}")
    else:
        print(f"[!] Sample PDF not found: {sample_pdf}")
        print("Please ensure the PDF is in the root directory or update the script path.")

if __name__ == "__main__":
    test_ingestion()
