import os
import traceback
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from classifier import IntentClassifier
from rag import RAGAssistant
from validator import Validator
from prompts import REFUSAL_RESPONSE
from scheduler import start_scheduler
from logger import log_query, log_error
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Start background scheduler
start_scheduler()

# Initialize components
classifier = IntentClassifier()
validator = Validator()

# Lazy loading RAG to avoid early failures if vectorstore/API key is missing
rag_assistant = None

def get_rag():
    global rag_assistant
    if rag_assistant is None:
        try:
            rag_assistant = RAGAssistant()
        except Exception as e:
            print(f"Error initializing RAG: {e}")
            return None
    return rag_assistant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Empty query"}), 400

        # Step 1: Intent Classification
        route = classifier.route_query(query)
        
        if route == "refusal":
            log_query(query, "refusal", REFUSAL_RESPONSE)
            return jsonify({"answer": REFUSAL_RESPONSE, "source": "Safe Refusal Engine"})

        # Step 1.5: Intercept queries for structured deep dive
        q_lower = query.lower()
        fund_file = None
        fund_name = None
        source_url = None

        if "flexicap" in q_lower or "flexi cap" in q_lower:
            fund_file = 'data/processed/sbi_flexicap_details.json'
            fund_name = 'SBI Flexicap Fund'
            source_url = "https://www.sbimf.com/sbimf-scheme-details/sbi-flexicap-fund-39"
        elif "large cap" in q_lower or "bluechip" in q_lower:
            fund_file = 'data/processed/sbi_large_cap_details.json'
            fund_name = 'SBI Large Cap Fund'
            source_url = "https://www.sbimf.com/sbimf-scheme-details/SBI-Large-Cap-Fund-(Formerly-known-as-SBI-Bluechip-Fund)-43"
        elif "elss" in q_lower or "tax saver" in q_lower or "long term equity" in q_lower:
            fund_file = 'data/processed/sbi_elss_details.json'
            fund_name = 'SBI ELSS Tax Saver Fund'
            source_url = "https://www.sbimf.com/sbimf-scheme-details/SBI-ELSS-Tax-Saver-Fund-(formerly-known-as-SBI-Long-Term-Equity-Fund)-3"
        elif "nifty" in q_lower or "index" in q_lower:
            fund_file = 'data/processed/sbi_nifty_index_details.json'
            fund_name = 'SBI Nifty Index Fund'
            source_url = "https://www.sbimf.com/sbimf-scheme-details/sbi-nifty-index-fund-13"

        if fund_file and any(keyword in q_lower for keyword in ["portfolio", "holdings", "components", "performance", "returns", "cagr", "managers", "deep dive"]):
            try:
                with open(fund_file, 'r') as f:
                    fund_data = json.load(f)
                
                # Log and return the structured data directly
                log_query(query, "structured", f"Returned {fund_name} Deep Dive Data")
                return jsonify({
                    "answer": f"Here is the detailed data for the {fund_name} from the official fact sheet.",
                    "source": source_url,
                    "scheme": fund_name,
                    "last_updated": fund_data.get("nav", {}).get("as_on", "Jan 2025"),
                    "structured_data": fund_data
                })
            except Exception as e:
                print(f"Error loading {fund_name} data: {e}")
                # Fallback to standard RAG if file fails to load

        # Step 2: Retrieval (RAG)
        rag = get_rag()
        if not rag:
            log_error("RAG not initialized")
            return jsonify({"answer": "Assistant is still being set up. Please ensure the vector store is created.", "source": "System"}), 503

        raw_result = rag.get_answer(query)
        
        # Use answer for validation, but preserve metadata
        answer_text = raw_result.get("answer", "")
        
        # Step 3: Validation
        final_answer = answer_text
        if not validator.validate_answer(answer_text):
            final_answer = validator.sanitize_answer(answer_text)
        
        log_query(query, "rag", final_answer)
        
        return jsonify({
            "answer": final_answer,
            "source": raw_result.get("source"),
            "scheme": raw_result.get("scheme"),
            "last_updated": raw_result.get("last_updated")
        })
    except Exception as e:
        error_details = traceback.format_exc()
        log_error(f"Error processing query: \n{error_details}")
        return jsonify({"answer": "An internal error occurred. Please try again later.", "source": "System"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
