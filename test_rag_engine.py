from rag_engine import RAGEngine

engine = RAGEngine("http://localhost:1234/v1", r"prompts\rag_v1.json")
reply, stats, sources = engine.query("What is Samuel's experience?", "pdf-rag-testing")
print(f"Reply: {reply}")
print(f"Stats: {stats}")