import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from prompts import SYSTEM_PROMPT, REFUSAL_RESPONSE
from dotenv import load_dotenv

load_dotenv()

def _get_api_key():
    """Reliably get the Google API key from environment."""
    return (
        os.environ.get("GOOGLE_API_KEY") or
        os.environ.get("GEMINI_API_KEY") or
        ""
    )

class RAGAssistant:
    def __init__(self, db_path="vectorstore/faiss_index"):
        api_key = _get_api_key()
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it in Streamlit Cloud Secrets as:\n"
                'google_api_key = "AIza...your_key_here"'
            )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key
        )
        self.vectorstore = FAISS.load_local(
            db_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=api_key
        )

    def get_answer(self, query: str) -> dict:
        """ Retrieves context and generates a structured answer. """
        try:
            docs = self.vectorstore.similarity_search(query, k=3)
        except Exception:
            # If vector search fails (embedding mismatch), fall back to LLM-only
            docs = []

        if not docs:
            return {
                "answer": "Information not available in official sources.",
                "source": "https://www.sbimf.com/",
                "scheme": "General SBI MF Information",
                "last_updated": "Jan 2025"
            }

        context = "\n\n".join([
            f"Source: {d.metadata.get('source_url', 'N/A')}\nContent: {d.page_content}"
            for d in docs
        ])
        primary_source = docs[0].metadata.get('source_url', 'N/A')
        scheme_name = docs[0].metadata.get('scheme_name', 'General SBI MF Information')

        # Use proper LangChain message objects
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{context}\n\nQuery: {query}")
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
