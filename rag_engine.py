from typing import List, Dict, Tuple
import json
from pathlib import Path
from openai import OpenAI
from llm_client import LLMUtil
from opensearch_vector_index_setup import vector_search, client as os_client

class RAGEngine(LLMUtil):
    def __init__(self, llm_client_base_url: str, prompt_path: str):
        openai_client = OpenAI(base_url=llm_client_base_url)
        super().__init__(openai_client, prompt_path)
        
    def _format_context(self, hits: List[Dict]) -> str:
        context_parts = []
        for hit in hits:
            text = hit['_source'].get('text', '')
            source = hit['_source'].get('source', 'Unknown')
            context_parts.append(f"Source: {source}\nContent: {text}")
        return "\n\n---\n\n".join(context_parts)

    def query(self, user_query: str, index_name: str, k: int = 5) -> Tuple[str, str, List[Dict]]:
        # 1. Search OpenSearch using reusable function
        from opensearch_vector_index_setup import vector_search, get_search_stats
        
        print(f"[*] Searching OpenSearch index '{index_name}' for: '{user_query}'")
        hits, raw_response = vector_search(user_query, index_name, k=k)
        
        stats = get_search_stats(raw_response)
        print(f"[+] Found {len(hits)} relevant chunks. Latency: {stats['took']}ms")
        
        context = self._format_context(hits)
        
        # 2. Inject context into prompt
        # We use a combined input for chat
        augmented_query = f"Question: {user_query}\n\nContext:\n{context}"
        
        # 3. Get LLM response using inherited chat method
        print("[*] Generating response from local LLM...")
        reply, usage_stats = self.chat(augmented_query)
        print("[+] Response generated successfully.")
        
        return reply, usage_stats, hits, stats

    
