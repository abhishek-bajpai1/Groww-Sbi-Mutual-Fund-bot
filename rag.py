import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from prompts import SYSTEM_PROMPT, REFUSAL_RESPONSE
from dotenv import load_dotenv

load_dotenv()

class RAGAssistant:
    def __init__(self, db_path="vectorstore/faiss_index"):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self.vectorstore = FAISS.load_local(
            db_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

    def get_answer(self, query: str) -> dict:
        """ Retrieves context and generates a structured answer. """
        # Search for top 3 relevant chunks
        docs = self.vectorstore.similarity_search(query, k=3)

        if not docs:
            return {
                "answer": "Information not available in official sources.",
                "source": "N/A",
                "scheme": "N/A",
                "last_updated": "Jan 2025"
            }

        context = "\n\n".join([
            f"Source: {d.metadata.get('source_url', 'N/A')}\nContent: {d.page_content}"
            for d in docs
        ])
        primary_source = docs[0].metadata.get('source_url', 'N/A')
        scheme_name = docs[0].metadata.get('scheme_name', 'General SBI MF Information')

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"}
        ]

        response = self.llm.invoke(messages)

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
    pass
