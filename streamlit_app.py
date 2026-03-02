import streamlit as st
import json
import os
import sys

# =====================================================================
# CRITICAL: Inject API key from Streamlit Secrets into os.environ
# BEFORE any LangChain / Google AI modules are imported.
# Streamlit Cloud does NOT use .env files — only st.secrets.
# =====================================================================
try:
    api_key = (
        st.secrets.get("GOOGLE_API_KEY") or
        st.secrets.get("GEMINI_API_KEY") or
        None
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key
except Exception:
    pass  # Local dev — fall back to .env

# Load .env for local development (no-op on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# =====================================================================
# App Config
# =====================================================================
st.set_page_config(
    page_title="Groww | MF Facts Assistant",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =====================================================================
# CSS
# =====================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero-title { font-size: 2.4rem; font-weight: 800; color: #1e2227; text-align: center; letter-spacing: -1px; margin-bottom: 6px; }
.hero-sub { font-size: 1rem; color: #7c7e8c; text-align: center; margin-bottom: 28px; }

.fact-card { background: #fff; border-left: 6px solid #00d09c; border-radius: 16px; padding: 22px 26px; box-shadow: 0 8px 28px rgba(0,0,0,0.06); margin-top: 20px; }
.fact-badge { color: #00d09c; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
.fact-text { font-size: 16px; line-height: 1.8; color: #44475b; }

.perf-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 14px 0; }
.perf-box { background: #f4f7f9; border: 1px solid #eaebed; border-radius: 12px; padding: 12px 8px; text-align: center; }
.perf-period { font-size: 10px; color: #7c7e8c; font-weight: 700; text-transform: uppercase; }
.perf-val { font-size: 17px; font-weight: 700; color: #00d09c; margin-top: 4px; }

.holdings-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
.holdings-table th { color: #7c7e8c; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 8px 12px; text-align: left; border-bottom: 1px solid #eaebed; }
.holdings-table td { padding: 10px 12px; border-bottom: 1px solid #eaebed; color: #44475b; }
.holdings-table td strong { color: #1e2227; }

.section-title { font-size: 14px; font-weight: 700; color: #1e2227; margin: 18px 0 8px 0; }
.meta-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 18px; padding-top: 14px; border-top: 1px solid #eaebed; }
.meta-label { font-size: 10px; color: #7c7e8c; font-weight: 700; text-transform: uppercase; }
.meta-value { font-size: 13px; font-weight: 600; color: #1e2227; margin-top: 2px; }
.source-link { display: inline-block; color: #00d09c; font-weight: 600; font-size: 13px; text-decoration: none; margin-top: 12px; }
.refusal-card { background: #fff8f0; border-left: 6px solid #ff9500; border-radius: 16px; padding: 22px 26px; margin-top: 20px; }
.disclaimer { font-size: 12px; color: #94a3b8; text-align: center; margin-top: 36px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
    <div style="background:#00d09c;border-radius:50%;width:38px;height:38px;display:flex;align-items:center;justify-content:center;">
        <span style="color:white;font-size:18px;font-weight:bold;">✓</span>
    </div>
    <span style="font-size:22px;font-weight:800;color:#00d09c;">Groww</span>
    <span style="margin-left:auto;font-size:13px;color:#7c7e8c;font-weight:600;">MF Facts Pro</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">Expert Factual Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Get instant, verified data on SBI Mutual Fund schemes.<br>Sourced directly from official disclosures, updated Jan 2025.</div>', unsafe_allow_html=True)

# =====================================================================
# Fund Data
# =====================================================================
FUND_MAP = [
    {
        "keywords": ["flexicap", "flexi cap"],
        "file": "data/processed/sbi_flexicap_details.json",
        "name": "SBI Flexicap Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-flexicap-fund-39"
    },
    {
        "keywords": ["large cap", "bluechip", "largecap"],
        "file": "data/processed/sbi_large_cap_details.json",
        "name": "SBI Large Cap Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-Large-Cap-Fund-(Formerly-known-as-SBI-Bluechip-Fund)-43"
    },
    {
        "keywords": ["elss", "tax saver", "long term equity"],
        "file": "data/processed/sbi_elss_details.json",
        "name": "SBI ELSS Tax Saver Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-ELSS-Tax-Saver-Fund-(formerly-known-as-SBI-Long-Term-Equity-Fund)-3"
    },
    {
        "keywords": ["nifty", "index fund", "nifty index"],
        "file": "data/processed/sbi_nifty_index_details.json",
        "name": "SBI Nifty Index Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-nifty-index-fund-13"
    }
]

DEEP_DIVE_KEYWORDS = {"portfolio", "holdings", "performance", "returns", "cagr", "managers", "deep dive", "components"}

# Scheme summary facts from scheme_data.json (no API needed)
SCHEME_FACTS = {
    "SBI Flexicap Fund": {
        "expense_ratio": {"regular": "1.66%", "direct": "0.83%"},
        "exit_load": "0.10% if redeemed on or before 30 days; Nil after 30 days.",
        "category": "Equity: Flexi Cap",
        "lock_in": "No lock-in period.",
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-flexicap-fund-39"
    },
    "SBI Large Cap Fund": {
        "expense_ratio": {"regular": "1.48%", "direct": "0.80%"},
        "exit_load": "0.25% if redeemed within 30 days; 0.10% between 30-90 days; Nil after 90 days.",
        "category": "Equity: Large Cap",
        "lock_in": "No lock-in period.",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-Large-Cap-Fund-(Formerly-known-as-SBI-Bluechip-Fund)-43"
    },
    "SBI ELSS Tax Saver Fund": {
        "expense_ratio": {"regular": "1.57%", "direct": "0.89%"},
        "exit_load": "Nil (Statutory lock-in period of 3 years applies).",
        "category": "Equity: ELSS",
        "lock_in": "3 years statutory lock-in period (as per ELSS regulations).",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-ELSS-Tax-Saver-Fund-(formerly-known-as-SBI-Long-Term-Equity-Fund)-3"
    },
    "SBI Nifty Index Fund": {
        "expense_ratio": {"regular": "0.40%", "direct": "0.19%"},
        "exit_load": "0.20% if redeemed within 15 days; Nil after 15 days.",
        "category": "Index Fund",
        "lock_in": "No lock-in period.",
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-nifty-index-fund-13"
    }
}

# =====================================================================
# Advisory keywords (refusal)
# =====================================================================
ADVISORY_KEYWORDS = [
    "should i invest", "which is better", "recommend", "advice",
    "is it good", "will it go up", "buy", "sell", "market crash"
]

# =====================================================================
# Helper Functions
# =====================================================================
def detect_fund(query):
    q = query.lower()
    for fund in FUND_MAP:
        if any(kw in q for kw in fund["keywords"]):
            return fund
    return None

def is_deep_dive(query):
    q = query.lower()
    return any(kw in q for kw in DEEP_DIVE_KEYWORDS)

def is_advisory(query):
    q = query.lower()
    return any(kw in q for kw in ADVISORY_KEYWORDS)

def get_fact_answer(query, fund_name):
    """Answer simple factual queries from scheme_data without API call."""
    q = query.lower()
    facts = SCHEME_FACTS.get(fund_name, {})
    url = facts.get("url", "#")
    
    if "expense ratio" in q or "expense" in q or "ter" in q:
        er = facts.get("expense_ratio", {})
        return (
            f"The expense ratio for {fund_name} is **{er.get('regular', 'N/A')}** for the Regular Plan "
            f"and **{er.get('direct', 'N/A')}** for the Direct Plan.",
            url
        )
    if "exit load" in q:
        return f"Exit load for {fund_name}: {facts.get('exit_load', 'Check official website.')}", url
    if "lock" in q:
        return f"Lock-in period for {fund_name}: {facts.get('lock_in', 'No lock-in.')}", url
    if "category" in q or "type" in q:
        return f"{fund_name} is categorized as: **{facts.get('category', 'N/A')}**.", url
    return None, url

def render_deep_dive(fund_data, fund_info):
    perf = fund_data.get("performance", {}).get("regular_growth", {}).get("cagr", {})
    holdings = fund_data.get("portfolio", {}).get("top_holdings", [])

    perf_html = ""
    if perf:
        periods = [("1y","1Y"),("3y","3Y"),("5y","5Y"),("10y","10Y"),("since_inception","ALL TIME")]
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

    st.markdown(f"""
    <div class="fact-card">
        <div class="fact-badge">✓ Official Fact — Deep Dive</div>
        <div class="fact-text">Detailed data for <strong>{fund_info["name"]}</strong> from official fact sheet.</div>
        {perf_html}
        {holdings_html}
        <div class="meta-row">
            <div><div class="meta-label">Scheme</div><div class="meta-value">{fund_info["name"]}</div></div>
            <div><div class="meta-label">Source</div><div class="meta-value">Official Disclosure</div></div>
        </div>
        <a href="{fund_info["url"]}" target="_blank" class="source-link">↗ View official scheme document</a>
    </div>
    """, unsafe_allow_html=True)

def render_fact(answer, url, scheme):
    st.markdown(f"""
    <div class="fact-card">
        <div class="fact-badge">✓ Official Fact</div>
        <div class="fact-text">{answer}</div>
        <div class="meta-row">
            <div><div class="meta-label">Scheme</div><div class="meta-value">{scheme}</div></div>
            <div><div class="meta-label">Source</div><div class="meta-value">Official Disclosure</div></div>
        </div>
        <a href="{url}" target="_blank" class="source-link">↗ View official scheme document</a>
    </div>
    """, unsafe_allow_html=True)

# =====================================================================
# LLM-based fallback (only if API key available)
# =====================================================================
@st.cache_resource
def get_llm():
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    except Exception as e:
        return None

def llm_answer(query, fund_name, url):
    llm = get_llm()
    if not llm:
        st.warning("General queries need an API key. Deep Dive portfolio/performance queries work without it.")
        return
    facts = SCHEME_FACTS.get(fund_name, {})
    context = f"Scheme: {fund_name}\nExpense Ratio Regular: {facts.get('expense_ratio',{}).get('regular','N/A')}\nExpense Ratio Direct: {facts.get('expense_ratio',{}).get('direct','N/A')}\nExit Load: {facts.get('exit_load','N/A')}\nCategory: {facts.get('category','N/A')}\nLock-in: {facts.get('lock_in','N/A')}"
    prompt = f"""You are a factual assistant for SBI Mutual Funds. Answer ONLY from the given context. Max 2 sentences. End with: Source: {url}

Context:
{context}

Query: {query}"""
    try:
        resp = llm.invoke(prompt)
        answer = resp.content if hasattr(resp, 'content') else str(resp)
        render_fact(answer, url, fund_name)
    except Exception as e:
        st.error(f"Could not get answer: {e}")

# =====================================================================
# Main processing
# =====================================================================
def process_query(query):
    q = query.strip()
    if not q:
        return

    # Refusal
    if is_advisory(q):
        st.markdown(f"""
        <div class="refusal-card">
            <div style="color:#ff9500;font-weight:700;font-size:13px;margin-bottom:8px;">⚠️ SAFE REFUSAL</div>
            <div class="fact-text">I can only provide factual information from official AMC, SEBI, or AMFI sources. I cannot provide investment advice or recommendations.<br><br>
            Refer to SEBI's investor education page: <a href="https://investor.sebi.gov.in/" target="_blank">investor.sebi.gov.in</a></div>
        </div>
        """, unsafe_allow_html=True)
        return

    fund = detect_fund(q)
    if not fund:
        st.info("This assistant covers SBI Large Cap, SBI Flexicap, SBI ELSS Tax Saver, and SBI Nifty Index Fund only.")
        return

    # Deep Dive (no API key needed)
    if is_deep_dive(q):
        try:
            with open(fund["file"], "r") as f:
                fund_data = json.load(f)
            render_deep_dive(fund_data, fund)
            return
        except Exception as e:
            st.warning(f"Deep dive data not found: {e}")

    # Simple factual (no API key needed)
    answer, url = get_fact_answer(q, fund["name"])
    if answer:
        render_fact(answer, url, fund["name"])
        return

    # LLM fallback (needs API key)
    llm_answer(q, fund["name"], fund["url"])

# =====================================================================
# Quick Chips UI
# =====================================================================
st.markdown("**Quick Questions:**")
col1, col2, col3, col4 = st.columns(4)
chip_queries = {
    "Flexicap Portfolio": "What are the portfolio holdings for SBI Flexicap?",
    "Large Cap Holdings": "What are the top holdings for SBI Large Cap?",
    "ELSS Returns?": "What is the performance of SBI ELSS Tax Saver?",
    "ELSS Lock-in?": "What is the lock-in period for SBI ELSS Tax Saver Fund?"
}
chips = {col1: "Flexicap Portfolio", col2: "Large Cap Holdings", col3: "ELSS Returns?", col4: "ELSS Lock-in?"}
for col, label in chips.items():
    if col.button(label, use_container_width=True):
        st.session_state["query"] = chip_queries[label]

# Search Input
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

# Footer
st.markdown("""
<div class="disclaimer">
    Built with integrity for Groww users. All facts sourced from
    <a href="https://www.sbimf.com/" target="_blank" style="color:#00d09c;">SBI Mutual Fund Official</a>, SEBI, and AMFI.<br>
    <strong>Non-Advisory Disclaimer:</strong> This system is strictly for informational purposes and does not constitute financial advice.
</div>
""", unsafe_allow_html=True)
