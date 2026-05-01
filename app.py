import streamlit as st
from src.rag_engine import RAGEngine
from src.ingestion import ingest_pdf
from src.config import DEFAULT_INDEX_NAME, LLM_BASE_URL
import gc
import os
import tempfile

UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024


def save_uploaded_file(uploaded_file) -> str:
    """
    Persist the uploaded PDF to a temp file without creating a second full-size
    in-memory copy.
    """
    uploaded_file.seek(0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        while chunk := uploaded_file.read(UPLOAD_CHUNK_SIZE):
            tmp_file.write(chunk)
        return tmp_file.name

# Page Config
st.set_page_config(page_title="Local RAG Assistant", page_icon="🤖", layout="wide")

if "upload_notice" not in st.session_state:
    st.session_state.upload_notice = None

# Initialize RAG Engine
@st.cache_resource
def get_rag_engine():
    # Use path relative to root
    prompt_path = os.path.join("prompts", "rag_v1.json")
    return RAGEngine(LLM_BASE_URL, prompt_path)

engine = get_rag_engine()

# Sidebar - Settings & Upload
with st.sidebar:
    st.title("⚙️ Settings")
    index_name = st.text_input("OpenSearch Index", value=DEFAULT_INDEX_NAME)
    top_k = st.slider("Number of Chunks (k)", 1, 10, 5)
    
    st.divider()
    st.title("📄 Upload Documents")
    st.caption("Max PDF upload size: 2 GB")

    if st.session_state.upload_notice:
        st.success(st.session_state.upload_notice)
        st.session_state.upload_notice = None

    with st.form("pdf_upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader("Upload a PDF for RAG", type="pdf")
        if uploaded_file is not None:
            st.caption(
                f"Selected: {uploaded_file.name} "
                f"({uploaded_file.size / (1024 * 1024):.1f} MB)"
            )
        submit_upload = st.form_submit_button("🚀 Index PDF")

    if uploaded_file is not None and submit_upload:
        with st.status("Indexing document...", expanded=True) as status:
            tmp_path = None
            try:
                tmp_path = save_uploaded_file(uploaded_file)

                st.write(f"Ingesting file: {uploaded_file.name}")
                # Call ingestion with original filename as source label
                ingest_pdf(tmp_path, index_name, source_label=uploaded_file.name)

                status.update(label="✅ Indexing Complete!", state="complete", expanded=False)
                st.session_state.upload_notice = (
                    f"File '{uploaded_file.name}' added to index '{index_name}'."
                )
                del uploaded_file
                gc.collect()
                st.rerun()
            except Exception as e:
                status.update(label="❌ Indexing Failed", state="error")
                st.error(f"Error during ingestion: {str(e)}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    st.divider()
    st.markdown("### About")
    st.info("This is a local RAG system using OpenSearch and a local LLM.")

# Main UI
st.title("🤖 Local RAG Assistant")
st.markdown("Query your local documents with ease.")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask something about your docs..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching and thinking..."):
            try:
                # Updated call returns stats too
                reply, usage_stats, sources, search_stats = engine.query(prompt, index_name, k=top_k)
                
                # Show search stats briefly
                st.caption(f"⏱️ Search Latency: {search_stats['took']}ms | 📚 Chunks Found: {len(sources)}")
                
                st.markdown(reply)
                
                # Show sources in an expander
                with st.expander("🔍 View Sources"):
                    for i, hit in enumerate(sources):
                        st.markdown(f"**Source {i+1}:** {hit['_source'].get('source', 'Unknown')}")
                        st.text(hit['_source'].get('text', ''))
                        st.markdown(f"**Score:** {hit['_score']:.4f}")
                        st.divider()
                
                # Show usage stats in sidebar or bottom
                st.session_state.last_stats = usage_stats
                st.session_state.search_stats = search_stats
                
                # Add assistant message to history
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Display Stats in sidebar
if "last_stats" in st.session_state:
    with st.sidebar:
        st.markdown("### 📊 Performance Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Search (ms)", st.session_state.search_stats['took'] if "search_stats" in st.session_state else "N/A")
        with col2:
            st.metric("Chunks", len(sources) if "sources" in locals() else "N/A")
        
        st.markdown("**LLM Usage:**")
        st.code(st.session_state.last_stats)
