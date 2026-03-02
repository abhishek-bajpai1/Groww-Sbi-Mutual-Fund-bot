from rag import RAGAssistant
import os
from dotenv import load_dotenv

load_dotenv()

rag = RAGAssistant()
query = "What is the expense ratio of SBI Large Cap Fund?"
docs = rag.vectorstore.similarity_search(query, k=5)

print(f"Query: {query}")
print(f"Retrieved {len(docs)} documents.")

for i, doc in enumerate(docs):
    print(f"\n--- Chunk {i+1} ---")
    print(f"Source: {doc.metadata.get('source_url')}")
    print(f"Scheme: {doc.metadata.get('scheme_name')}")
    print(f"Content Snippet: {doc.page_content[:200]}...")
