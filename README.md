# Local RAG Assistant 🤖

A powerful, local-first Retrieval-Augmented Generation (RAG) system using OpenSearch for vector storage and LM Studio for local LLM inference.

## 🏗️ Architecture

![Architecture](assets/architecture_diagram.jpg)

The system follows a standard RAG pipeline:

1. **Ingestion**: PDFs are loaded, chunked using `RecursiveCharacterTextSplitter`, and embedded using `all-MiniLM-L6-v2`.
2. **Storage**: Chunks and embeddings are stored in an OpenSearch k-NN index.
3. **Retrieval**: User queries are embedded and used to find the most relevant chunks in OpenSearch.
4. **Generation**: The retrieved context is injected into a system prompt and sent to a local LLM via an OpenAI-compatible API.

## 📂 Project Structure

```text
RAG_T/
├── app.py                # Main Streamlit Application
├── src/                  # Core modules
│   ├── embeddings.py     # Embedding logic
│   ├── ingestion.py      # PDF processing and indexing
│   ├── llm_client.py     # LLM interaction utility
│   ├── rag_engine.py      # RAG orchestrator
│   └── vector_store.py   # OpenSearch interactions
├── prompts/              # System prompt templates
├── tests/                # Automated/Manual test scripts
├── scripts/              # Diagnostic and maintenance tools
└── assets/               # Documentation assets
```

## 🚀 Getting Started

### Prerequisites

- **OpenSearch**: Running locally on port 9200.
- **LM Studio**: Or any OpenAI-compatible server running on port 1234.
- **Python 3.9+**

### Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

   ```bash
   pip install streamlit openai opensearch-py sentence-transformers pymupdf langchain-text-splitters
   ```

### Running the App

```bash
streamlit run app.py
```

### Ingestion

You can upload and index PDFs directly through the Streamlit UI sidebar.

## 🛠️ Development & Diagnostics

- **Run Tests**: `python tests/test_rag_engine.py`
- **Check Mapping**: `python scripts/diag_opensearch.py`
- **Reset Indices**: `python scripts/reset_os_indices.py`

## 📊 Performance Tracking

The system tracks search latency and LLM token usage for every query, providing transparency into the RAG process.
