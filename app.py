import streamlit as st
from src.rag_engine import RAGEngine
from src.ingestion import ingest_pdf
import os
import tempfile

# Page Config
st.set_page_config(page_title="Local RAG Assistant", page_icon="🤖", layout="wide")

# Initialize RAG Engine
@st.cache_resource
def get_rag_engine():
    # Use path relative to root
    prompt_path = os.path.join("prompts", "rag_v1.json")
    return RAGEngine("http://localhost:1234/v1", prompt_path)

engine = get_rag_engine()

# Sidebar - Settings & Upload
with st.sidebar:
    st.title("⚙️ Settings")
    index_name = st.text_input("OpenSearch Index", value="pdf-rag")
    top_k = st.slider("Number of Chunks (k)", 1, 10, 5)
    
    st.divider()
    st.title("📄 Upload Documents")
    uploaded_file = st.file_uploader("Upload a PDF for RAG", type="pdf")
    
    if uploaded_file is not None:
        if st.button("🚀 Index PDF"):
            with st.status("Indexing document...", expanded=True) as status:
                try:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    st.write(f"Ingesting file: {uploaded_file.name}")
                    # Call ingestion with original filename as source label
                    ingest_pdf(tmp_path, index_name, source_label=uploaded_file.name)
                    
                    # Clean up
                    os.unlink(tmp_path)
                    
                    status.update(label="✅ Indexing Complete!", state="complete", expanded=False)
                    st.success(f"File '{uploaded_file.name}' added to index '{index_name}'!")
                except Exception as e:
                    status.update(label="❌ Indexing Failed", state="error")
                    st.error(f"Error during ingestion: {str(e)}")

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
