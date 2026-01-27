import streamlit as st
from rag_engine import RAGEngine
import os

# Page Config
st.set_page_config(page_title="Local RAG Assistant", page_icon="🤖", layout="wide")

# Initialize RAG Engine
@st.cache_resource
def get_rag_engine():
    return RAGEngine("http://localhost:1234/v1", r"prompts\rag_v1.json")

engine = get_rag_engine()

# Sidebar - Settings
with st.sidebar:
    st.title("⚙️ Settings")
    index_name = st.text_input("OpenSearch Index", value="pdf-rag-testing")
    top_k = st.slider("Number of Chunks (k)", 1, 10, 5)
    
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
                reply, stats, sources = engine.query(prompt, index_name, k=top_k)
                
                st.markdown(reply)
                
                # Show sources in an expander
                with st.expander("🔍 View Sources"):
                    for i, hit in enumerate(sources):
                        st.markdown(f"**Source {i+1}:** {hit['_source'].get('source', 'Unknown')}")
                        st.text(hit['_source'].get('text', ''))
                        st.markdown(f"**Score:** {hit['_score']:.4f}")
                        st.divider()
                
                # Show usage stats in sidebar or bottom
                st.session_state.last_stats = stats
                
                # Add assistant message to history
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Display Stats at the bottom
if "last_stats" in st.session_state:
    with st.sidebar:
        st.markdown("### 📊 Last Query Stats")
        st.code(st.session_state.last_stats)
