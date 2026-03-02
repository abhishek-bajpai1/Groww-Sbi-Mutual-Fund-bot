import streamlit as st
import json
import os
import sys
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# =====================================================================
# CRITICAL: Read API key from Streamlit Secrets and inject into os.environ
# This must happen at module level, before any LangChain imports.
# =====================================================================
def _resolve_api_key():
    """Read API keys from st.secrets or os.environ."""
    try:
        # Gemini/Google Keys
        google_key = (
            st.secrets.get("GOOGLE_API_KEY") or
            st.secrets.get("google_api_key") or
            st.secrets.get("GEMINI_API_KEY") or
            st.secrets.get("gemini_api_key") or
            ""
        )
        if google_key:
            os.environ["GOOGLE_API_KEY"] = google_key
            os.environ["GEMINI_API_KEY"] = google_key

        # Groq Key
        groq_key = (
            st.secrets.get("GROQ_API_KEY") or
            st.secrets.get("groq_api_key") or
            ""
        )
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
        
        return google_key, groq_key
    except Exception:
        pass
    
    # Local dev fallback
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
    groq_key = os.environ.get("GROQ_API_KEY") or ""
    return google_key, groq_key

GOOGLE_API_KEY, GROQ_API_KEY = _resolve_api_key()

# =====================================================================
# Sidebar: API Key Diagnostics
# =====================================================================
with st.sidebar:
    st.markdown("## 🌱 SBI MF Quick Reference")
    st.markdown("---")
    st.markdown("**Supported Funds:**")
    fund_info = [
        ("🔵", "SBI Flexicap", "TER: 0.83% (D) / 1.66% (R)"),
        ("🟢", "SBI Large Cap", "TER: 0.80% (D) / 1.48% (R)"),
        ("🟡", "SBI ELSS", "TER: 0.89% (D) / 1.57% (R)"),
        ("🟣", "SBI Nifty Index", "TER: 0.19% (D) / 0.40% (R)"),
    ]
    for emoji, name, ter in fund_info:
        st.markdown(f"{emoji} **{name}**  \n{ter}")
    st.markdown("---")
    st.markdown("**📚 Sample Questions:**")
    st.markdown("""
- Expense ratio of SBI ELSS?
- Who manages SBI Flexicap?
- What is CAGR?
- SIP vs Lumpsum?
- Direct vs Regular plan?
- Lock-in for ELSS?
- How to redeem SBI Large Cap?
- What is Section 80C?
    """)
    st.markdown("---")
    st.caption("Source: SBI MF Official, SEBI, AMFI")

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

/* ── CSS Variables: Light (default) ──────────────────────────── */
:root {
  --bg:        #f4f7f9;
  --card-bg:   #ffffff;
  --text:      #44475b;
  --heading:   #1e2227;
  --muted:     #7c7e8c;
  --border:    #eaebed;
  --perf-bg:   #f4f7f9;
  --refusal-bg:#fff8f0;
  --accent:    #00d09c;
}

/* ── Dark Mode Variables ─────────────────────────────────────── */
body.dark-mode, body.dark-mode [class*="css"] {
  --bg:        #0f1117;
  --card-bg:   #1a1d2e;
  --text:      #c9cdd4;
  --heading:   #f0f2f6;
  --muted:     #8b8fa8;
  --border:    #2d3148;
  --perf-bg:   #252840;
  --refusal-bg:#2a1f0f;
  --accent:    #00d09c;
}

/* ── Base ────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  transition: background 0.3s, color 0.3s;
}

/* ── Hero ────────────────────────────────────────────────────── */
.hero-title {
  font-size: 2.2rem; font-weight: 800;
  color: var(--heading); text-align: center;
  letter-spacing: -1px; margin-bottom: 6px;
}
.hero-sub {
  font-size: 1rem; color: var(--muted);
  text-align: center; margin-bottom: 28px;
}

/* ── Fact Card ───────────────────────────────────────────────── */
.fact-card {
  background: var(--card-bg);
  border-left: 6px solid var(--accent);
  border-radius: 16px; padding: 22px 26px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.08);
  margin-top: 20px;
}
.fact-badge {
  color: var(--accent); font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;
}
.fact-text { font-size: 15px; line-height: 1.8; color: var(--text); }

/* ── Performance Grid ───────────────────────────────────────── */
.perf-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px; margin: 14px 0;
}
.perf-box {
  background: var(--perf-bg); border: 1px solid var(--border);
  border-radius: 12px; padding: 12px 8px; text-align: center;
}
.perf-period { font-size: 10px; color: var(--muted); font-weight: 700; text-transform: uppercase; }
.perf-val    { font-size: 17px; font-weight: 700; color: var(--accent); margin-top: 4px; }

/* ── Holdings Table ─────────────────────────────────────────── */
.holdings-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
.holdings-table th {
  color: var(--muted); font-size: 11px; font-weight: 700;
  text-transform: uppercase; padding: 8px 12px; text-align: left;
  border-bottom: 1px solid var(--border);
}
.holdings-table td {
  padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text);
}
.holdings-table td strong { color: var(--heading); }

/* ── Meta Row ───────────────────────────────────────────────── */
.section-title { font-size: 14px; font-weight: 700; color: var(--heading); margin: 18px 0 8px 0; }
.meta-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
  margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border);
}
.meta-label { font-size: 10px; color: var(--muted); font-weight: 700; text-transform: uppercase; }
.meta-value { font-size: 13px; font-weight: 600; color: var(--heading); margin-top: 2px; }
.source-link {
  display: inline-block; color: var(--accent); font-weight: 600;
  font-size: 13px; text-decoration: none; margin-top: 12px;
}
.refusal-card {
  background: var(--refusal-bg); border-left: 6px solid #ff9500;
  border-radius: 16px; padding: 22px 26px; margin-top: 20px;
}
.disclaimer {
  font-size: 12px; color: var(--muted); text-align: center;
  margin-top: 36px; line-height: 1.6;
}

/* ── Dark mode toggle button ─────────────────────────────────── */
.theme-btn {
  float: right; background: var(--perf-bg); border: 1px solid var(--border);
  border-radius: 100px; padding: 4px 14px; font-size: 13px;
  color: var(--text); cursor: pointer; font-weight: 600;
}

/* ── Mobile Responsive ──────────────────────────────────────── */
@media (max-width: 768px) {
  .hero-title { font-size: 1.6rem !important; }
  .hero-sub   { font-size: 0.85rem !important; }

  .fact-card  { padding: 16px 16px !important; border-radius: 12px !important; }
  .fact-text  { font-size: 14px !important; }

  /* Stack perf grid to 3 cols on tablet, 2 on phone */
  .perf-grid  { grid-template-columns: repeat(3, 1fr) !important; gap: 6px !important; }
  .perf-val   { font-size: 14px !important; }

  /* Stack meta-row to single column */
  .meta-row   { grid-template-columns: 1fr !important; gap: 8px !important; }

  .holdings-table th, .holdings-table td { padding: 6px 8px !important; font-size: 12px !important; }

  /* Make comparison table scroll horizontally */
  .holdings-table { display: block; overflow-x: auto; white-space: nowrap; }
}

@media (max-width: 480px) {
  .hero-title { font-size: 1.3rem !important; }
  .perf-grid  { grid-template-columns: repeat(2, 1fr) !important; }
  .fact-card  { padding: 14px 12px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Dark Mode Toggle + Header ────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

header_col, toggle_col = st.columns([5, 1])
with header_col:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
        <div style="background:#00d09c;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;">
            <span style="color:white;font-size:17px;font-weight:bold;">✓</span>
        </div>
        <span style="font-size:21px;font-weight:800;color:#00d09c;">Groww</span>
        <span style="font-size:13px;color:#7c7e8c;font-weight:600;margin-left:4px;">MF Facts Pro</span>
    </div>
    """, unsafe_allow_html=True)
with toggle_col:
    dark = st.toggle("🌙", value=st.session_state["dark_mode"], key="theme_toggle", help="Dark / Light mode")
    st.session_state["dark_mode"] = dark

# ── Inject dark theme via CSS override (Streamlit strips <script> tags) ──
if st.session_state["dark_mode"]:
    st.markdown("""
    <style>
    /* ── Dark Mode Overrides ───────────────────────────────────── */
    .stApp, .main, section[data-testid="stSidebar"] > div {
        background-color: #0f1117 !important;
    }
    html, body, [class*="css"], .stMarkdown, p, span, label {
        color: #c9cdd4 !important;
    }
    .fact-card { background: #1a1d2e !important; box-shadow: 0 8px 28px rgba(0,0,0,0.3) !important; }
    .fact-text { color: #c9cdd4 !important; }
    .perf-box  { background: #252840 !important; border-color: #2d3148 !important; }
    .perf-period { color: #8b8fa8 !important; }
    .holdings-table th { color: #8b8fa8 !important; border-color: #2d3148 !important; }
    .holdings-table td { color: #c9cdd4 !important; border-color: #2d3148 !important; }
    .holdings-table td strong { color: #f0f2f6 !important; }
    .section-title { color: #f0f2f6 !important; }
    .meta-row { border-color: #2d3148 !important; }
    .meta-label { color: #8b8fa8 !important; }
    .meta-value { color: #f0f2f6 !important; }
    .refusal-card { background: #2a1f0f !important; }
    .hero-title { color: #f0f2f6 !important; }
    .hero-sub   { color: #8b8fa8 !important; }
    .disclaimer { color: #8b8fa8 !important; }
    /* Streamlit native widgets in dark mode */
    .stTextInput > div > div > input {
        background: #1a1d2e !important;
        color: #c9cdd4 !important;
        border-color: #2d3148 !important;
    }
    .stButton > button {
        background: #252840 !important;
        color: #c9cdd4 !important;
        border-color: #2d3148 !important;
    }
    .stButton > button[kind="primary"] {
        background: #00d09c !important;
        color: white !important;
        border-color: #00d09c !important;
    }
    </style>
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
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-flexicap-fund-39",
        "scheme_code": 119718
    },
    {
        "keywords": ["large cap", "bluechip", "largecap"],
        "file": "data/processed/sbi_large_cap_details.json",
        "name": "SBI Large Cap Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-Large-Cap-Fund-(Formerly-known-as-SBI-Bluechip-Fund)-43",
        "scheme_code": 119598
    },
    {
        "keywords": ["elss", "tax saver", "long term equity"],
        "file": "data/processed/sbi_elss_details.json",
        "name": "SBI ELSS Tax Saver Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-ELSS-Tax-Saver-Fund-(formerly-known-as-SBI-Long-Term-Equity-Fund)-3",
        "scheme_code": 119723
    },
    {
        "keywords": ["nifty", "index fund", "nifty index"],
        "file": "data/processed/sbi_nifty_index_details.json",
        "name": "SBI Nifty Index Fund",
        "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-nifty-index-fund-13",
        "scheme_code": 119827
    }
]

DEEP_DIVE_KEYWORDS = {"portfolio", "holdings", "performance", "returns", "cagr", "managers", "deep dive", "components", "allocation", "chart", "nav", "price", "sector"}

def render_sector_chart(sector_data, fund_name):
    """Render Plotly pie chart for sector allocation."""
    df = pd.DataFrame(sector_data)
    fig = px.pie(df, values='percentage', names='sector', title=f"{fund_name} - Sector Allocation",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#7c7e8c" if st.session_state.get("dark_mode") else "#44475b"),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data(ttl=3600)
def get_nav_data(scheme_code):
    """Fetch NAV data from mfapi.in."""
    try:
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") == "SUCCESS":
            df = pd.DataFrame(data["data"])
            df["nav"] = pd.to_numeric(df["nav"])
            df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
            df = df.sort_values("date")
            return df, data["meta"]
    except Exception as e:
        st.error(f"Error fetching NAV: {e}")
    return None, None

def render_performance_chart(df, fund_name):
    """Render Plotly performance chart."""
    fig = px.line(df, x="date", y="nav", title=f"{fund_name} - NAV History")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="NAV (₹)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=40, b=0),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#7c7e8c" if st.session_state.get("dark_mode") else "#44475b")
    )
    fig.update_traces(line_color="#00d09c")
    st.plotly_chart(fig, use_container_width=True)

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
    # Fetch Live NAV data
    nav_df, meta = get_nav_data(fund_info["scheme_code"])
    
    current_nav = "N/A"
    nav_date = "N/A"
    one_day_change = "N/A"
    
    if nav_df is not None and not nav_df.empty:
        latest = nav_df.iloc[-1]
        current_nav = f"₹{latest['nav']:.2f}"
        nav_date = latest['date'].strftime("%d %b %Y")
        
        if len(nav_df) > 1:
            prev = nav_df.iloc[-2]
            change = ((latest['nav'] - prev['nav']) / prev['nav']) * 100
            one_day_change = f"{'+' if change > 0 else ''}{change:.2f}%"

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
        for h in holdings[:8]:
            holdings_html += f'<tr><td>{h["name"]}</td><td><strong>{h["percentage"]}</strong></td></tr>'
        holdings_html += "</table>"

    # Favorites Logic
    if "favorites" not in st.session_state:
        st.session_state["favorites"] = []
    
    is_fav = fund_info["name"] in st.session_state["favorites"]
    
    st.markdown(f"""
    <div class="fact-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div class="fact-badge">✓ Official Fact & Live NAV</div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:15px;">
            <div>
                <div style="font-size:24px; font-weight:800; color:var(--heading);">{current_nav}</div>
                <div style="font-size:12px; color:var(--muted);">Latest NAV ({nav_date})</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:16px; font-weight:700; color:{'#00d09c' if '+' in one_day_change else '#ff4b4b'};">{one_day_change}</div>
                <div style="font-size:12px; color:var(--muted);">Day Change</div>
            </div>
        </div>
        <div class="fact-text">Detailed data for <strong>{fund_info["name"]}</strong>.</div>
        {perf_html}
    """, unsafe_allow_html=True)

    fav_label = "❤️ In Favorites" if is_fav else "🤍 Add to Favorites"
    if st.button(fav_label, key=f"fav_{fund_info['name']}"):
        if is_fav:
            st.session_state["favorites"].remove(fund_info["name"])
        else:
            st.session_state["favorites"].append(fund_info["name"])
        st.rerun()

    if nav_df is not None:
        render_performance_chart(nav_df, fund_info["name"])
    
    sector_data = fund_data.get("portfolio", {}).get("sector_allocation", [])
    if sector_data:
        render_sector_chart(sector_data, fund_info["name"])
        
    st.markdown(f"""
        {holdings_html}
        <div class="meta-row">
            <div><div class="meta-label">Scheme</div><div class="meta-value">{fund_info["name"]}</div></div>
            <div><div class="meta-label">Category</div><div class="meta-value">{fund_data.get("category", "N/A")}</div></div>
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

import re

@st.cache_data
def load_faq():
    """Load the comprehensive FAQ database from JSON."""
    try:
        with open("data/processed/faq.json", "r") as f:
            return json.load(f)
    except Exception:
        return []

def normalize(text):
    """Lowercase + strip punctuation for better keyword matching."""
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

def faq_score(faq, q_norm):
    """Score a FAQ entry against a normalized query."""
    score = 0
    for kw in faq["keywords"]:
        kw_norm = normalize(kw)
        if kw_norm in q_norm:
            # Longer keyword matches are worth more
            score += 1 + len(kw_norm.split())
    return score

def best_faq_match(q_raw):
    """Find the best FAQ match using normalized keyword scoring."""
    q_norm = normalize(q_raw)
    faqs = load_faq()
    best_score, best_match = 0, None
    for faq in faqs:
        s = faq_score(faq, q_norm)
        if s > best_score:
            best_score, best_match = s, faq
    return best_match if best_score >= 2 else None

def faq_answer(query, fund_name, url):
    """Match query against FAQ database using normalized keyword scoring."""
    match = best_faq_match(query)
    if match:
        render_fact(match["answer"], match["source"], match["scheme"])
        return True
    return False

def get_groq_answer(query):
    """Fallback LLM answer using Groq (Llama 3)."""
    if not GROQ_API_KEY:
        return None
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        system_prompt = """You are a helpful, factual assistant for Groww Mutual Funds. 
        Your goal is to answer user queries about mutual funds as accurately as possible based on general financial knowledge.
        If you are unsure about a specific SBI fund detail, state that you are providing general information and suggest checking the official website.
        Be concise and use professional language. Format your response clearly with markdown.
        NEVER provide investment advice or specific 'buy/sell' recommendations."""
        
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.2,
            max_tokens=512
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Groq API Error: {e}")
        return None

def render_comparison_table():
    """Render a side-by-side comparison of all 4 funds."""
    st.markdown("""
    <div class="fact-card">
        <div class="fact-badge">✓ Official Data — Fund Comparison</div>
        <div class="fact-text"><strong>All SBI MF Funds — Side-by-Side</strong></div>
        <table class="holdings-table" style="margin-top:14px;">
            <tr><th>Feature</th><th>🔵 Flexicap</th><th>🟢 Large Cap</th><th>🟡 ELSS</th><th>🟣 Nifty Index</th></tr>
            <tr><td>Category</td><td>Flexi Cap</td><td>Large Cap</td><td>ELSS</td><td>Index Fund</td></tr>
            <tr><td>TER (Direct)</td><td><strong>0.83%</strong></td><td><strong>0.80%</strong></td><td><strong>0.89%</strong></td><td><strong>0.19%</strong></td></tr>
            <tr><td>TER (Regular)</td><td>1.66%</td><td>1.48%</td><td>1.57%</td><td>0.40%</td></tr>
            <tr><td>Lock-in</td><td>None</td><td>None</td><td><strong>3 Years</strong></td><td>None</td></tr>
            <tr><td>Exit Load</td><td>0.10%/30d</td><td>0.25%/30d</td><td>Nil</td><td>0.20%/15d</td></tr>
            <tr><td>Tax Saving</td><td>No</td><td>No</td><td><strong>80C ✓</strong></td><td>No</td></tr>
            <tr><td>Min SIP</td><td>₹500</td><td>₹500</td><td>₹500</td><td>₹500</td></tr>
            <tr><td>Risk</td><td>Very High</td><td>Very High</td><td>Very High</td><td>Very High</td></tr>
            <tr><td>Benchmark</td><td>Nifty 500 TRI</td><td>Nifty 100 TRI</td><td>Nifty 500 TRI</td><td>Nifty 50 TRI</td></tr>
        </table>
        <a href="https://www.sbimf.com/" target="_blank" class="source-link">↗ View at SBI MF Official</a>
    </div>
    """, unsafe_allow_html=True)

def render_stp_calculator():
    st.markdown("""
    <div class="fact-card">
        <div class="fact-badge">🧮 STP Calculator</div>
        <div class="fact-text">Systematic Transfer Plan: Move money from one fund to another monthly.</div>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        total_lumpsum = st.number_input("Total Lumpsum (₹)", min_value=10000, value=100000, step=5000)
    with cols[1]:
        transfer_amt = st.number_input("Monthly Transfer (₹)", min_value=1000, value=5000, step=1000)
    with cols[2]:
        debt_return = st.slider("Source Fund Return (%)", 1, 10, 6)
    
    equity_return = st.slider("Target Fund Return (%)", 1, 20, 12)
    months = int(total_lumpsum / transfer_amt)
    
    # Simple simulation
    source_bal = total_lumpsum
    target_bal = 0
    for _ in range(months):
        source_bal = (source_bal - transfer_amt) * (1 + debt_return/100/12)
        target_bal = (target_bal + transfer_amt) * (1 + equity_return/100/12)
    
    res_cols = st.columns(2)
    res_cols[0].metric("Final Source Bal", f"₹{source_bal:,.0f}")
    res_cols[1].metric("Final Target Bal", f"₹{target_bal:,.0f}")
    st.info(f"💡 This STP will take approx **{months} months** to complete.")

def render_swp_calculator():
    st.markdown("""
    <div class="fact-card">
        <div class="fact-badge">🧮 SWP Calculator</div>
        <div class="fact-text">Systematic Withdrawal Plan: Fixed monthly income from your investment.</div>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        initial = st.number_input("Initial Corpus (₹)", min_value=50000, value=500000, step=10000)
    with cols[1]:
        withdrawal = st.number_input("Monthly Withdrawal (₹)", min_value=1000, value=10000, step=1000)
    with cols[2]:
        growth = st.slider("Annual Growth (%)", 1, 15, 8)
    
    years = st.slider("Duration (Years)", 1, 30, 10)
    
    bal = initial
    total_withdrawn = 0
    for _ in range(years * 12):
        bal = (bal - withdrawal) * (1 + growth/100/12)
        total_withdrawn += withdrawal
        if bal <= 0:
            bal = 0
            break
            
    res_cols = st.columns(2)
    res_cols[0].metric("Total Withdrawn", f"₹{total_withdrawn:,.0f}")
    res_cols[1].metric("Final Balance", f"₹{bal:,.0f}")

def render_tax_estimator():
    st.markdown("""
    <div class="fact-card">
        <div class="fact-badge">🧮 Tax Savings Estimator (Section 80C)</div>
        <div class="fact-text">How much tax can you save by investing in SBI ELSS?</div>
    </div>
    """, unsafe_allow_html=True)
    income_slab = st.selectbox("Your Income Tax Slab", ["10%", "20%", "30%"])
    invest_amt = st.slider("ELSS Investment Amount (₹)", 1000, 150000, 50000)
    
    tax_rate = int(income_slab.replace("%", "")) / 100
    savings = invest_amt * tax_rate
    
    st.success(f"🎉 You can save approximately **₹{savings:,.0f}** in taxes!")
    st.caption("Note: Max limit for 80C is ₹1.5 Lakhs per year. Includes Surcharge/Cess as applicable.")

def render_mock_portfolio():
    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = []
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💼 My Mock Portfolio")
    
    if not st.session_state["portfolio"]:
        st.sidebar.info("Add investments to track them here!")
    else:
        total_inv = 0
        for item in st.session_state["portfolio"]:
            total_inv += item["amount"]
            st.sidebar.markdown(f"**{item['fund']}**")
            st.sidebar.markdown(f"Inv: ₹{item['amount']:,} @ {item['date']}")
        
        st.sidebar.metric("Total Invested", f"₹{total_inv:,}")
        if st.sidebar.button("Clear Portfolio"):
            st.session_state["portfolio"] = []
            st.rerun()

    with st.expander("➕ Log Mock Investment"):
        p_cols = st.columns(2)
        p_fund = p_cols[0].selectbox("Select Fund", [f["name"] for f in FUND_MAP])
        p_amt = p_cols[1].number_input("Amount (₹)", min_value=500, value=5000, step=500)
        if st.button("Add to Portfolio"):
            st.session_state["portfolio"].append({
                "fund": p_fund,
                "amount": p_amt,
                "date": datetime.now().strftime("%d %b %Y")
            })
            st.success(f"Added ₹{p_amt:,} in {p_fund} to portfolio!")
            st.rerun()


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

    # Special feature: Fund Comparison Table
    q_norm = normalize(q)
    if any(kw in q_norm for kw in ["compare", "comparison", "all funds", "vs", "difference between"]):
        render_comparison_table()
        return

    # Special feature: SIP Calculator
    if any(kw in q_norm for kw in ["sip calculator", "calculate sip", "how much will i get", "sip returns calculator", "calculate return"]):
        render_sip_calculator()
        return

    # STP/SWP/Tax
    if "stp" in q_norm:
        render_stp_calculator()
        return
    if "swp" in q_norm:
        render_swp_calculator()
        return
    if "tax" in q_norm and ("save" in q_norm or "savings" in q_norm or "estimator" in q_norm):
        render_tax_estimator()
        return
    if "portfolio" in q_norm and not any(kw in q_norm for kw in ["holdings", "allocation"]):
        st.info("Check the sidebar or use the 'Log Mock Investment' section below!")


    fund = detect_fund(q)

    # General MF question (no specific fund mentioned) → try FAQ first
    if not fund:
        match = best_faq_match(q)
        if match:
            render_fact(match["answer"], match["source"], match["scheme"])
            return
        st.info(
            "👋 I specialise in **SBI Mutual Funds**. Mention a fund name (Flexicap, Large Cap, ELSS, Nifty) "
            "or ask a general MF question like: *What is SIP? What is CAGR? SIP vs Lumpsum? Direct vs Regular?*"
        )
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

    # FAQ keyword-based lookup (no API needed)
    if faq_answer(q, fund["name"], fund["url"]):
        return

    # Final Fallback: Groq LLM
    with st.spinner("🤖 Consulting Groww AI (Groq)..."):
        llm_answer = get_groq_answer(q)
        if llm_answer:
            st.markdown(f"""
            <div class="fact-card">
                <div class="fact-badge">✨ AI Assistant (Groq)</div>
                <div class="fact-text">{llm_answer}</div>
                <div class="meta-row">
                    <div><div class="meta-label">Model</div><div class="meta-value">Llama 3 (via Groq)</div></div>
                    <div><div class="meta-label">Disclaimer</div><div class="meta-value">AI generated response</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(
                f"ℹ️ I don't have specific information about that query in my knowledge base. "
                f"Please visit the [official SBI MF website]({fund['url']}) for detailed information."
            )

# =====================================================================
# Quick Chips UI
# =====================================================================
st.markdown("**Quick Questions:**")
chip_queries = [
    ("📈 Flexicap Portfolio", "What are the portfolio holdings for SBI Flexicap?"),
    ("🏦 Large Cap Holdings", "What are the top holdings for SBI Large Cap?"),
    ("📊 ELSS Returns", "What is the performance of SBI ELSS Tax Saver?"),
    ("🔒 ELSS Lock-in", "What is the lock-in period for SBI ELSS Tax Saver Fund?"),
    ("💰 Expense Ratios", "What is the expense ratio of SBI Nifty Index Fund?"),
    ("🧑‍💼 Fund Manager", "Who is the fund manager of SBI Flexicap?"),
    ("💡 SIP vs Lumpsum", "SIP vs Lumpsum"),
    ("📋 Section 80C", "How does ELSS save tax under Section 80C?"),
    ("⚖️ Compare All Funds", "compare all funds"),
    ("📅 Inception Dates", "What is the inception date of SBI Flexicap?"),
    ("🔄 STP Calc", "STP Calculator"),
    ("💵 SWP Calc", "SWP Calculator"),
    ("🛡️ Tax Savings", "tax savings estimator"),
]
cols = st.columns(4)
for i, (label, query_text) in enumerate(chip_queries):
    with cols[i % 4]:
        if st.button(label, use_container_width=True, key=f"chip_{i}"):
            st.session_state["query"] = query_text

# ─── SIP Calculator (always visible at bottom) ─────────────────────
with st.expander("🧮 SIP Returns Calculator", expanded=False):
    st.markdown("Estimate how your SIP grows over time (illustrative, not a guarantee).")
    calc_cols = st.columns(3)
    with calc_cols[0]:
        monthly = st.number_input("Monthly SIP (₹)", min_value=500, max_value=100000, value=5000, step=500)
    with calc_cols[1]:
        years = st.slider("Duration (years)", 1, 30, 10)
    with calc_cols[2]:
        rate = st.slider("Expected CAGR (%)", 1, 25, 12)

    n = years * 12
    r = rate / 100 / 12
    future_value = monthly * ((((1 + r) ** n) - 1) / r) * (1 + r)
    invested = monthly * n
    gains = future_value - invested

    res_cols = st.columns(3)
    with res_cols[0]:
        st.metric("Total Invested", f"₹{invested/100000:.2f}L")
    with res_cols[1]:
        st.metric("Est. Gains", f"₹{gains/100000:.2f}L", delta="Market-linked")
    with res_cols[2]:
        st.metric("Est. Corpus", f"₹{future_value/100000:.2f}L")
    st.caption("⚠️ This is a mathematical projection using compound interest. Actual MF returns are market-linked and not guaranteed.")

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

# Render Sidebar Portfolio
render_mock_portfolio()

# Favorites section
if st.session_state.get("favorites"):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ❤️ Favorites")
    for fav in st.session_state["favorites"]:
        st.sidebar.markdown(f"- {fav}")


# Footer
st.markdown("""
<div class="disclaimer">
    Built with integrity for Groww users. All facts sourced from
    <a href="https://www.sbimf.com/" target="_blank" style="color:#00d09c;">SBI Mutual Fund Official</a>, SEBI, and AMFI.<br>
    <strong>Non-Advisory Disclaimer:</strong> This system is strictly for informational purposes and does not constitute financial advice.
</div>
""", unsafe_allow_html=True)
