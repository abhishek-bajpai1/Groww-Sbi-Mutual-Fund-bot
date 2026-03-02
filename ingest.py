import os
import csv
import json
import requests
from bs4 import BeautifulSoup
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

class DataIngestor:
    def __init__(self, sources_file="sources.csv", db_path="vectorstore/faiss_index"):
        self.sources_file = sources_file
        self.db_path = db_path
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    def scrape_url(self, url):
        """ Scrapes text content from a URL. """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator=' ')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def ingest(self):
        """ Reads sources, scrapes/downloads, and stores in FAISS index. """
        documents = []

        with open(self.sources_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                url = row['source_url']
                print(f"Processing: {row['scheme_name']} ({url})")

                if url.lower().endswith('.pdf'):
                    try:
                        loader = PyPDFLoader(url)
                        pdf_docs = loader.load()
                        for d in pdf_docs:
                            d.metadata.update({
                                "scheme_name": row['scheme_name'],
                                "source_url": url,
                                "document_type": row['document_type'],
                                "last_updated": "Jan 2025"
                            })
                        chunks = self.text_splitter.split_documents(pdf_docs)
                        documents.extend(chunks)
                    except Exception as e:
                        print(f"Error processing PDF {url}: {e}")
                else:
                    content = self.scrape_url(url)
                    if content:
                        doc = Document(
                            page_content=content,
                            metadata={
                                "scheme_name": row['scheme_name'],
                                "source_url": url,
                                "document_type": row['document_type'],
                                "last_updated": "Jan 2025"
                            }
                        )
                        chunks = self.text_splitter.split_documents([doc])
                        documents.extend(chunks)

        # Process structured JSON data
        json_path = "data/processed/scheme_data.json"
        if os.path.exists(json_path):
            print(f"Processing structured data from {json_path}...")
            with open(json_path, 'r') as f:
                schemes = json.load(f)
                for s in schemes:
                    content = (
                        f"Scheme: {s['scheme_name']}\n"
                        f"Category: {s['category']}\n"
                        f"Expense Ratio Regular: {s['expense_ratio']['regular']}\n"
                        f"Expense Ratio Direct: {s['expense_ratio']['direct']}\n"
                        f"Exit Load: {s['exit_load']}\n"
                        f"Source: {s['source_url']}"
                    )
                    doc = Document(
                        page_content=content,
                        metadata={
                            "scheme_name": s['scheme_name'],
                            "source_url": s['source_url'],
                            "document_type": "Structured Data",
                            "last_updated": s['last_updated']
                        }
                    )
                    documents.append(doc)

        # Also ingest all deep-dive JSON files
        detail_files = {
            "SBI Flexicap Fund": "data/processed/sbi_flexicap_details.json",
            "SBI Large Cap Fund": "data/processed/sbi_large_cap_details.json",
            "SBI ELSS Tax Saver Fund": "data/processed/sbi_elss_details.json",
            "SBI Nifty Index Fund": "data/processed/sbi_nifty_index_details.json",
        }
        for scheme_name, filepath in detail_files.items():
            if os.path.exists(filepath):
                print(f"Processing {scheme_name} details from {filepath}...")
                with open(filepath, 'r') as f:
                    data = json.load(f)
                content = json.dumps(data, indent=2)
                doc = Document(
                    page_content=content,
                    metadata={
                        "scheme_name": scheme_name,
                        "source_url": data.get("source_url", "https://www.sbimf.com/"),
                        "document_type": "Deep Dive JSON",
                        "last_updated": "Jan 2025"
                    }
                )
                documents.append(doc)

        if documents:
            print(f"Storing {len(documents)} chunks in FAISS at {self.db_path}...")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            vectorstore.save_local(self.db_path)
            print("Ingestion complete. FAISS index saved.")
        else:
            print("No documents found to ingest.")

if __name__ == "__main__":
    ingestor = DataIngestor()
    ingestor.ingest()
