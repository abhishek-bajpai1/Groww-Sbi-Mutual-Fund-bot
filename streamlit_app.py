import streamlit as st
import json
import os
import sys

# --- CRITICAL: Inject secrets into env BEFORE importing any LangChain/Gemini modules ---
# On Streamlit Cloud, secrets come from st.secrets NOT from .env files.
# langchain-google-genai checks for both GOOGLE_API_KEY and GEMINI_API_KEY.
try:
    # Try all common secret names the user might have set in Streamlit Secrets UI
    api_key = (
        st.secrets.get("GOOGLE_API_KEY") or
        st.secrets.get("GEMINI_API_KEY") or
        None
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key
except Exception:
    pass  # Local dev: fall back to .env below

# Load .env for local development (no-op on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Page Config ---
st.set_page_config(
    page_title="Groww | MF Facts Assistant",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.header-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}

.groww-logo {
    width: 36px;
    height: 36px;
    background: #00d09c;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #1e2227;
    text-align: center;
    letter-spacing: -1px;
    margin-bottom: 8px;
}

.hero-sub {
    font-size: 1rem;
    color: #7c7e8c;
    text-align: center;
    margin-bottom: 32px;
}

.fact-card {
    background: #ffffff;
    border-left: 6px solid #00d09c;
    border-radius: 16px;
    padding: 24px 28px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    margin-top: 24px;
}

.fact-badge {
    color: #00d09c;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}

.fact-text {
    font-size: 17px;
    line-height: 1.8;
    color: #44475b;
}

.perf-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin: 16px 0;
}

.perf-box {
    background: #f4f7f9;
    border: 1px solid #eaebed;
    border-radius: 12px;
    padding: 12px 8px;
    text-align: center;
}

.perf-period {
    font-size: 11px;
    color: #7c7e8c;
    font-weight: 700;
    text-transform: uppercase;
}

.perf-val {
    font-size: 18px;
    font-weight: 700;
    color: #00d09c;
    margin-top: 4px;
}

.holdings-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    font-size: 14px;
}

.holdings-table th {
    color: #7c7e8c;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #eaebed;
}

.holdings-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #eaebed;
    color: #44475b;
}

.holdings-table td strong {
    color: #1e2227;
}

.section-title {
    font-size: 15px;
    font-weight: 700;
    color: #1e2227;
    margin: 20px 0 10px 0;
}

.meta-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #eaebed;
}

.meta-label {
    font-size: 11px;
    color: #7c7e8c;
    font-weight: 700;
    text-transform: uppercase;
}

.meta-value {
    font-size: 14px;
    font-weight: 600;
    color: #1e2227;
    margin-top: 2px;
}

.refusal-card {
    background: #fff8f0;
    border-left: 6px solid #ff9500;
    border-radius: 16px;
    padding: 24px 28px;
    margin-top: 24px;
}

.source-link {
    display: inline-block;
    color: #00d09c;
    font-weight: 600;
    font-size: 13px;
    text-decoration: none;
    margin-top: 14px;
}

.disclaimer {
    font-size: 12px;
    color: #94a3b8;
    text-align: center;
    margin-top: 40px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
    <div style="background:#00d09c; border-radius:50%; width:40px; height:40px; display:flex; align-items:center; justify-content:center;">
        <span style="color:white; font-size:20px;">✓</span>
    </div>
    <span style="font-size:24px; font-weight:800; color:#00d09c;">Groww</span>
    <span style="margin-left:auto; font-size:13px; color:#7c7e8c; font-weight:600;">MF Facts Pro</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">Expert Factual Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Get instant, verified data on SBI Mutual Fund schemes.<br>Sourced directly from official disclosures, updated Jan 2025.</div>', unsafe_allow_html=True)

# --- Initialize components with caching ---
@st.cache_resource
def load_components():
    from classifier import IntentClassifier
    from validator import Validator
    return IntentClassifier(), Validator()

@st.cache_resource
def load_rag():
    try:
        from rag import RAGAssistant
        return RAGAssistant()
    except Exception as e:
        st.session_state["rag_error"] = str(e)
        return None

# --- Fund routing logic ---
FUND_MAP = {
    ("flexicap", "flexi cap"): {
        "file": "data/processed/sbi_flexicap_details.json",
        "name": "SBI Flexicap Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-flexicap-fund-39"
    },
    ("large cap", "bluechip", "largecap"): {
        "file": "data/processed/sbi_large_cap_details.json",
        "name": "SBI Large Cap Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-Large-Cap-Fund-(Formerly-known-as-SBI-Bluechip-Fund)-43"
    },
    ("elss", "tax saver", "long term equity"): {
        "file": "data/processed/sbi_elss_details.json",
        "name": "SBI ELSS Tax Saver Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-ELSS-Tax-Saver-Fund-(formerly-known-as-SBI-Long-Term-Equity-Fund)-3"
    },
    ("nifty", "nifty index", "index fund"): {
        "file": "data/processed/sbi_nifty_index_details.json",
        "name": "SBI Nifty Index Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-nifty-index-fund-13"
    }
}

DEEP_DIVE_KEYWORDS = {"portfolio", "holdings", "components", "performance", "returns", "cagr", "managers", "deep dive"}

def detect_fund_and_mode(query):
    q = query.lower()
    for keywords, fund_info in FUND_MAP.items():
        if any(kw in q for kw in keywords):
            is_deep_dive = any(kw in q for kw in DEEP_DIVE_KEYWORDS)
            return fund_info, is_deep_dive
    return None, False

def render_deep_dive(fund_data, fund_info):
    perf = fund_data.get("performance", {}).get("regular_growth", {}).get("cagr", {})
    holdings = fund_data.get("portfolio", {}).get("top_holdings", [])
    
    perf_html = ""
    if perf:
        periods = [("1y", "1Y"), ("3y", "3Y"), ("5y", "5Y"), ("10y", "10Y"), ("since_inception", "ALL TIME")]
        perf_html = '<div class="section-title">📈 Performance (CAGR)</div><div class="perf-grid">'
        for key, label in periods:
            val = perf.get(key, "N/A")
            perf_html += f'<div class="perf-box"><div class="perf-period">{label}</div><div class="perf-val">{val}</div></div>'
        perf_html += "</div>"

    holdings_html = ""
    if holdings:
        holdings_html = '<div class="section-title">🏦 Top Holdings</div><table class="holdings-table"><tr><th>Company</th><th>Allocation</th></tr>'
        for h in holdings[:5]:
            holdings_html += f'<tr><td>{h["name"]}</td><td><strong>{h["percentage"]}</strong></td></tr>'
        holdings_html += "</table>"
    
    meta_html = f"""
    <div class="meta-row">
        <div>
            <div class="meta-label">Scheme Name</div>
            <div class="meta-value">{fund_info["name"]}</div>
        </div>
        <div>
            <div class="meta-label">Information Source</div>
            <div class="meta-value">Official Disclosure</div>
        </div>
    </div>
    <a href="{fund_info["url"]}" target="_blank" class="source-link">↗ View official scheme document</a>
    """
    
    st.markdown(f"""
    <div class="fact-card">
        <div class="fact-badge">✓ Official Fact</div>
        <div class="fact-text">Here is the detailed data for the <strong>{fund_info["name"]}</strong> from the official fact sheet.</div>
        {perf_html}
        {holdings_html}
        {meta_html}
    </div>
    """, unsafe_allow_html=True)

def process_query(query):
    from prompts import REFUSAL_RESPONSE
    classifier, validator = load_components()
    
    route = classifier.route_query(query)
    if route == "refusal":
        st.markdown(f"""
        <div class="refusal-card">
            <div style="color:#ff9500; font-weight:700; font-size:13px; margin-bottom:8px;">⚠️ SAFE REFUSAL</div>
            <div class="fact-text">{REFUSAL_RESPONSE.strip()}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    fund_info, is_deep_dive = detect_fund_and_mode(query)
    if fund_info and is_deep_dive:
        try:
            with open(fund_info["file"], "r") as f:
                fund_data = json.load(f)
            render_deep_dive(fund_data, fund_info)
            return
        except Exception as e:
            st.warning(f"Could not load deep dive data: {e}. Falling back to RAG.")

    rag = load_rag()
    if not rag:
        err = st.session_state.get("rag_error", "Unknown error")
        st.error(f"⚠️ RAG assistant could not initialize.\n\n**Error:** `{err}`\n\nCheck that `GOOGLE_API_KEY` is set in your Streamlit Cloud secrets.")
        return

    with st.spinner("Searching official sources..."):
        result = rag.get_answer(query)

    answer_text = result.get("answer", "")
    if not validator.validate_answer(answer_text):
        answer_text = validator.sanitize_answer(answer_text)

    source = result.get("source", "N/A")
    scheme = result.get("scheme", "N/A")
    
    st.markdown(f"""
    <div class="fact-card">
        <div class="fact-badge">✓ Official Fact</div>
        <div class="fact-text">{answer_text}</div>
        <div class="meta-row">
            <div>
                <div class="meta-label">Scheme Name</div>
                <div class="meta-value">{scheme}</div>
            </div>
            <div>
                <div class="meta-label">Information Source</div>
                <div class="meta-value">Official Disclosure</div>
            </div>
        </div>
        <a href="{source}" target="_blank" class="source-link">↗ View official scheme document</a>
    </div>
    """, unsafe_allow_html=True)

# --- Quick Chips ---
st.markdown("**Quick Questions:**")
col1, col2, col3, col4 = st.columns(4)
chips = {
    col1: "Flexicap Portfolio",
    col2: "Large Cap Holdings",
    col3: "ELSS Returns?",
    col4: "ELSS Lock-in?"
}
chip_queries = {
    "Flexicap Portfolio": "What are the portfolio holdings for SBI Flexicap?",
    "Large Cap Holdings": "What are the top holdings for SBI Large Cap?",
    "ELSS Returns?": "What is the performance of SBI ELSS Tax Saver?",
    "ELSS Lock-in?": "Lock-in period for SBI Long Term Equity?"
}
for col, label in chips.items():
    if col.button(label, use_container_width=True):
        st.session_state["query"] = chip_queries[label]

# --- Search Input ---
query = st.text_input(
    "Ask about expense ratio, exit load, performance, or portfolio...",
    value=st.session_state.get("query", ""),
    key="main_input",
    placeholder="e.g. What is the expense ratio of SBI Large Cap Fund?"
)

if st.button("🔍 Search", use_container_width=True, type="primary"):
    if query.strip():
        process_query(query.strip())
    else:
        st.warning("Please enter a question first.")
elif st.session_state.get("query") and st.session_state["query"] != st.session_state.get("last_query"):
    st.session_state["last_query"] = st.session_state["query"]
    process_query(st.session_state["query"])

# --- Footer ---
st.markdown("""
<div class="disclaimer">
    Built with integrity for Groww users. All facts sourced from 
    <a href="https://www.sbimf.com/" target="_blank" style="color:#00d09c;">SBI Mutual Fund Official</a>, SEBI, and AMFI.<br>
    <strong>Non-Advisory Disclaimer:</strong> This system is strictly for informational purposes and does not constitute financial advice.
</div>
""", unsafe_allow_html=True)
