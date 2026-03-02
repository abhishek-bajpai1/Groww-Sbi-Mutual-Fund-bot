import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from prompts import SYSTEM_PROMPT, REFUSAL_RESPONSE
from dotenv import load_dotenv

load_dotenv()

class RAGAssistant:
    def __init__(self, db_path="vectorstore"):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self.vectorstore = Chroma(persist_directory=db_path, embedding_function=self.embeddings)
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

    def get_answer(self, query: str) -> dict:
        """ Retrieves context and generates a structured answer. """
        # Search for top 3 relevant chunks
        docs = self.vectorstore.similarity_search(query, k=3)
        
        if not docs:
            return {
                "answer": "Information not available in official sources.",
                "source": "N/A",
                "scheme": "N/A"
            }

        context = "\n\n".join([f"Source: {d.metadata.get('source_url', 'N/A')}\nContent: {d.page_content}" for d in docs])
        primary_source = docs[0].metadata.get('source_url', 'N/A')
        scheme_name = docs[0].metadata.get('scheme_name', 'General SBI MF Information')
        
        # Combine context with user query
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"}
        ]
        
        response = self.llm.invoke(messages)
        
        # Ensure answer is a string (handle multi-part content)
        answer = response.content
        if isinstance(answer, list):
            answer = "".join([str(p.get("text", p)) if isinstance(p, dict) else str(p) for p in answer])

        return {
            "answer": answer,
            "source": primary_source,
            "scheme": scheme_name,
            "last_updated": "Jan 2025"
        }

if __name__ == "__main__":
    # Test query (requires vectorstore and API key)
    # rag = RAGAssistant()
    # print(rag.get_answer("What is the expense ratio for SBI Large Cap?"))
    pass
