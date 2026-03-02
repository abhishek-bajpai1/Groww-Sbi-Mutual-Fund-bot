import streamlit as st
import json
import os

# =====================================================================
# Resolve API key (kept for future use, not required for FAQ)
# =====================================================================
def _resolve_api_key():
    try:
        key = (
            st.secrets.get("GOOGLE_API_KEY") or
            st.secrets.get("google_api_key") or
            st.secrets.get("GEMINI_API_KEY") or
            st.secrets.get("gemini_api_key") or
            ""
        )
        if key:
            os.environ["GOOGLE_API_KEY"] = key
            os.environ["GEMINI_API_KEY"] = key
            return key
    except Exception:
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""

_resolve_api_key()

# =====================================================================
# Page Config
# =====================================================================
st.set_page_config(
    page_title="Groww MF Assistant",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =====================================================================
# CSS — Premium Chat UI
# =====================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

/* --- Header --- */
.bot-header {
    display: flex; align-items: center; gap: 14px;
    background: linear-gradient(135deg, #00d09c 0%, #00b386 100%);
    border-radius: 20px; padding: 18px 24px; margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0,208,156,0.25);
}
.bot-avatar {
    width: 52px; height: 52px; background: rgba(255,255,255,0.25);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 26px;
}
.bot-name { font-size: 20px; font-weight: 800; color: white; }
.bot-status { font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 2px; }
.status-dot {
    display: inline-block; width: 8px; height: 8px; background: #a8ffdf;
    border-radius: 50%; margin-right: 6px; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* --- Fund Pills --- */
.fund-pills { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.fund-pill {
    background: #f0fdf9; border: 2px solid #00d09c; color: #00b386;
    border-radius: 100px; padding: 6px 16px; font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all 0.2s;
}
.fund-pill.active, .fund-pill:hover {
    background: #00d09c; color: white;
}

/* --- Chat Messages --- */
.chat-wrap { 
    background: #f8fafb; border-radius: 20px; padding: 20px;
    min-height: 200px; max-height: 500px; overflow-y: auto;
    margin-bottom: 16px; border: 1px solid #eaebed;
}

.msg-row { display: flex; gap: 10px; margin-bottom: 18px; align-items: flex-end; }
.msg-row.user { flex-direction: row-reverse; }

.msg-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}
.msg-avatar.bot { background: linear-gradient(135deg,#00d09c,#00b386); }
.msg-avatar.user { background: linear-gradient(135deg,#6c63ff,#5a52e0); }

.msg-bubble {
    max-width: 80%; padding: 14px 18px; border-radius: 18px;
    font-size: 14px; line-height: 1.7; color: #2d3748;
}
.msg-bubble.bot {
    background: white; border-bottom-left-radius: 4px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}
.msg-bubble.user {
    background: linear-gradient(135deg,#6c63ff,#5a52e0);
    color: white; border-bottom-right-radius: 4px;
}

.msg-time { font-size: 11px; color: #94a3b8; margin-top: 4px; }

/* --- Welcome State --- */
.welcome-card {
    text-align: center; padding: 30px 20px;
    background: white; border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.welcome-emoji { font-size: 48px; margin-bottom: 12px; }
.welcome-title { font-size: 20px; font-weight: 700; color: #1e2227; margin-bottom: 8px; }
.welcome-sub { font-size: 14px; color: #7c7e8c; line-height: 1.6; }

/* --- Quick Actions --- */
.qa-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 16px 0; }
.qa-card {
    background: white; border: 1.5px solid #eaebed; border-radius: 12px;
    padding: 12px 14px; cursor: pointer; transition: all 0.2s; text-align: left;
}
.qa-card:hover { border-color: #00d09c; box-shadow: 0 4px 16px rgba(0,208,156,0.12); }
.qa-icon { font-size: 18px; margin-bottom: 4px; }
.qa-text { font-size: 13px; color: #44475b; font-weight: 500; }

/* --- Performance Grid --- */
.perf-grid {
    display: grid; grid-template-columns: repeat(5, 1fr);
    gap: 8px; margin: 12px 0;
}
.perf-box {
    background: linear-gradient(135deg, #f0fdf9, #e8faf5);
    border: 1px solid #b2f0e0; border-radius: 12px;
    padding: 10px 6px; text-align: center;
}
.perf-period { font-size: 10px; color: #00b386; font-weight: 700; text-transform: uppercase; }
.perf-val { font-size: 18px; font-weight: 800; color: #00b386; margin-top: 2px; }

/* --- Holdings Table --- */
.h-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
.h-table th {
    color: #94a3b8; font-size: 11px; font-weight: 700;
    text-transform: uppercase; padding: 8px 12px; text-align: left;
    border-bottom: 1px solid #eaebed;
}
.h-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #44475b; font-size: 14px; }
.h-table .alloc { font-weight: 700; color: #00b386; }

/* --- Source badge --- */
.source-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f0fdf9; border: 1px solid #b2f0e0; border-radius: 8px;
    padding: 6px 12px; font-size: 12px; color: #00b386; font-weight: 600;
    text-decoration: none; margin-top: 10px;
}

/* --- Refusal --- */
.refusal-bubble {
    background: #fff8f0; border-left: 4px solid #ff9500;
    border-radius: 12px; padding: 14px 18px; font-size: 14px; color: #44475b;
}

/* --- Info banner --- */
.info-banner {
    background: #eff6ff; border-left: 4px solid #3b82f6;
    border-radius: 12px; padding: 12px 16px;
    font-size: 13px; color: #1d4ed8;
}

/* --- Section title inside bubble --- */
.section-head { font-size: 13px; font-weight: 700; color: #1e2227; margin: 14px 0 6px 0; }

/* --- Disclaimer --- */
.disclaimer {
    font-size: 11px; color: #cbd5e1; text-align: center;
    margin-top: 20px; line-height: 1.6;
}

/* Hide streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
.stTextInput > div > div > input {
    border-radius: 100px !important; border: 2px solid #eaebed !important;
    padding: 12px 20px !important; font-size: 14px !important;
}
.stTextInput > div > div > input:focus { border-color: #00d09c !important; box-shadow: 0 0 0 3px rgba(0,208,156,0.15) !important; }
.stButton > button {
    border-radius: 100px !important; font-weight: 600 !important;
    padding: 10px 24px !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# Data & Logic
# =====================================================================
FUND_MAP = [
    {"keywords": ["flexicap", "flexi cap"], "file": "data/processed/sbi_flexicap_details.json",
     "name": "SBI Flexicap", "full": "SBI Flexicap Fund",
     "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-flexicap-fund-39", "emoji": "🔵"},
    {"keywords": ["large cap", "bluechip", "largecap"], "file": "data/processed/sbi_large_cap_details.json",
     "name": "SBI Large Cap", "full": "SBI Large Cap Fund",
     "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-Large-Cap-Fund-(Formerly-known-as-SBI-Bluechip-Fund)-43", "emoji": "🟢"},
    {"keywords": ["elss", "tax saver", "long term equity"], "file": "data/processed/sbi_elss_details.json",
     "name": "SBI ELSS", "full": "SBI ELSS Tax Saver Fund",
     "url": "https://www.sbimf.com/sbimf-scheme-details/SBI-ELSS-Tax-Saver-Fund-(formerly-known-as-SBI-Long-Term-Equity-Fund)-3", "emoji": "🟡"},
    {"keywords": ["nifty", "index fund", "nifty index"], "file": "data/processed/sbi_nifty_index_details.json",
     "name": "SBI Nifty", "full": "SBI Nifty Index Fund",
     "url": "https://www.sbimf.com/sbimf-scheme-details/sbi-nifty-index-fund-13", "emoji": "🟣"},
]

SCHEME_FACTS = {
    "SBI Flexicap Fund": {"expense_ratio": {"regular":"1.66%","direct":"0.83%"},
        "exit_load":"0.10% if redeemed within 30 days; Nil after 30 days.","lock_in":"No lock-in.","category":"Equity: Flexi Cap"},
    "SBI Large Cap Fund": {"expense_ratio": {"regular":"1.48%","direct":"0.80%"},
        "exit_load":"0.25% within 30 days; 0.10% between 30–90 days; Nil after 90 days.","lock_in":"No lock-in.","category":"Equity: Large Cap"},
    "SBI ELSS Tax Saver Fund": {"expense_ratio": {"regular":"1.57%","direct":"0.89%"},
        "exit_load":"Nil (3-year statutory lock-in applies).","lock_in":"3 years (statutory, per ELSS regulations).","category":"Equity: ELSS"},
    "SBI Nifty Index Fund": {"expense_ratio": {"regular":"0.40%","direct":"0.19%"},
        "exit_load":"0.20% within 15 days; Nil after 15 days.","lock_in":"No lock-in.","category":"Index Fund"},
}

DEEP_DIVE_KEYWORDS = {"portfolio","holdings","performance","returns","cagr","managers","deep dive","components"}
ADVISORY_KEYWORDS = ["should i invest","which is better","recommend","advice","is it good","will it go up","buy","sell","market crash"]

def detect_fund(q):
    for fund in FUND_MAP:
        if any(kw in q.lower() for kw in fund["keywords"]):
            return fund
    return None

def is_advisory(q):
    return any(kw in q.lower() for kw in ADVISORY_KEYWORDS)

@st.cache_data
def load_faq():
    try:
        with open("data/processed/faq.json","r") as f:
            return json.load(f)
    except Exception:
        return []

def get_fact_answer(query, fund_name):
    q = query.lower()
    facts = SCHEME_FACTS.get(fund_name,{})
    url = next((f["url"] for f in FUND_MAP if f["full"]==fund_name), "#")
    if any(k in q for k in ["expense ratio","expense","ter"]):
        er = facts.get("expense_ratio",{})
        return f"💡 **Expense Ratio** for {fund_name}:\n\n• Regular Plan: **{er.get('regular','N/A')}**\n• Direct Plan: **{er.get('direct','N/A')}**", url
    if "exit load" in q:
        return f"💡 **Exit Load** for {fund_name}:\n\n{facts.get('exit_load','N/A')}", url
    if "lock" in q:
        return f"🔒 **Lock-in Period** for {fund_name}:\n\n{facts.get('lock_in','N/A')}", url
    if "category" in q or "type" in q:
        return f"📁 **Category**: {fund_name} is classified as **{facts.get('category','N/A')}**.", url
    return None, url

def get_faq_answer(query, fund_name):
    q = query.lower()
    faqs = load_faq()
    best_score, best_match = 0, None
    for faq in faqs:
        score = sum(1 for kw in faq["keywords"] if kw in q)
        if score == 0: continue
        faq_funds = [f.lower() for f in faq.get("funds",[])]
        if any(kw in q for kw in faq_funds): score += 2
        if score > best_score:
            best_score, best_match = score, faq
    if best_match and best_score >= 1:
        return best_match["answer"], best_match["source"], best_match["scheme"]
    return None, None, None

def deep_dive_html(fund_data, fund_info):
    perf = fund_data.get("performance",{}).get("regular_growth",{}).get("cagr",{})
    holdings = fund_data.get("portfolio",{}).get("top_holdings",[])
    
    html = f'<div style="font-weight:700;color:#1e2227;margin-bottom:12px;">📊 Deep Dive — {fund_info["full"]}</div>'
    
    if perf:
        html += '<div class="section-head">📈 Performance (CAGR)</div><div class="perf-grid">'
        for key, label in [("1y","1Y"),("3y","3Y"),("5y","5Y"),("10y","10Y"),("since_inception","Since\nInception")]:
            val = perf.get(key,"N/A")
            html += f'<div class="perf-box"><div class="perf-period">{label}</div><div class="perf-val">{val}</div></div>'
        html += "</div>"
    
    if holdings:
        html += '<div class="section-head">🏦 Top Holdings</div><table class="h-table"><tr><th>Company</th><th>Weight</th></tr>'
        for h in holdings[:5]:
            html += f'<tr><td>{h["name"]}</td><td class="alloc">{h["percentage"]}</td></tr>'
        html += "</table>"
    
    html += f'<br><a href="{fund_info["url"]}" target="_blank" class="source-badge">↗ Official Source</a>'
    return html

def format_answer(answer, source, scheme):
    html = f'<div style="margin-bottom:8px;">{answer.replace(chr(10), "<br>")}</div>'
    if source and source != "#":
        html += f'<a href="{source}" target="_blank" class="source-badge">↗ Official Source</a>'
    return html

# =====================================================================
# Session State
# =====================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""

# =====================================================================
# Header
# =====================================================================
st.markdown("""
<div class="bot-header">
    <div class="bot-avatar">🌱</div>
    <div>
        <div class="bot-name">Groww MF Assistant</div>
        <div class="bot-status"><span class="status-dot"></span>Online • SBI Mutual Funds Expert</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# Fund Selector Chips
# =====================================================================
st.markdown("**Select a Fund to explore:**")
cols = st.columns(4)
fund_btns = {}
for i, fund in enumerate(FUND_MAP):
    with cols[i]:
        fund_btns[fund["name"]] = st.button(f"{fund['emoji']} {fund['name']}", use_container_width=True)
        if fund_btns[fund["name"]]:
            st.session_state.pending_query = f"Tell me about {fund['full']}"

# =====================================================================
# Chat Window — render each message separately
# =====================================================================
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-emoji">👋</div>
        <div class="welcome-title">Hi! I'm your SBI MF Expert</div>
        <div class="welcome-sub">Ask me anything about SBI Mutual Fund schemes.<br>
        I can answer questions about performance, portfolio, expense ratio, tax, and more.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        t = msg.get("time", "")
        if role == "user":
            st.markdown(f"""
            <div class="msg-row user">
                <div class="msg-avatar user">👤</div>
                <div>
                    <div class="msg-bubble user">{content}</div>
                    <div class="msg-time" style="text-align:right">{t}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-row bot">
                <div class="msg-avatar bot">🌱</div>
                <div>
                    <div class="msg-bubble bot">{content}</div>
                    <div class="msg-time">{t}</div>
                </div>
            </div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# Quick Action Grid (only when no messages)
# =====================================================================
if not st.session_state.messages:
    st.markdown("**Quick Actions:**")
    qa_cols = st.columns(2)
    quick_actions = [
        ("💰", "Expense Ratio", "What is the expense ratio of SBI Flexicap?"),
        ("📈", "Performance", "Show performance of SBI Large Cap"),
        ("🏦", "Portfolio", "Show portfolio holdings of SBI ELSS"),
        ("🔒", "Lock-in Period", "What is lock-in period of SBI ELSS?"),
        ("💸", "Exit Load", "What is exit load for SBI Nifty Index?"),
        ("🧑‍💼", "Fund Manager", "Who is fund manager of SBI Flexicap?"),
        ("📊", "Benchmark", "What is benchmark for SBI Large Cap?"),
        ("💵", "Current NAV", "What is NAV of SBI Nifty Index Fund?"),
    ]
    for i, (icon, label, query) in enumerate(quick_actions):
        with qa_cols[i % 2]:
            if st.button(f"{icon} {label}", use_container_width=True, key=f"qa_{i}"):
                st.session_state.pending_query = query

# =====================================================================
# Input + Send
# =====================================================================
st.markdown("")
input_col, btn_col = st.columns([5, 1])
with input_col:
    user_input = st.text_input(
        "", placeholder="Ask about any SBI MF scheme...",
        value=st.session_state.pending_query,
        key="chat_input", label_visibility="collapsed"
    )
with btn_col:
    send = st.button("Send →", type="primary", use_container_width=True)

# =====================================================================
# Process Query
# =====================================================================
from datetime import datetime

def process_and_reply(query):
    q = query.strip()
    if not q:
        return
    
    now = datetime.now().strftime("%I:%M %p")
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": q, "time": now})
    st.session_state.pending_query = ""
    
    # --- Refusal ---
    if is_advisory(q):
        bot_msg = """⚠️ <b>Safe Refusal Notice</b><br><br>
        I'm a factual information assistant and cannot provide investment advice, recommendations, or market predictions.<br><br>
        For investment guidance, please consult a SEBI-registered financial advisor.<br>
        📚 <a href="https://investor.sebi.gov.in/" target="_blank">SEBI Investor Education</a>"""
        st.session_state.messages.append({"role": "bot", "content": bot_msg, "time": now})
        st.rerun()
        return
    
    fund = detect_fund(q)
    
    if not fund:
        bot_msg = """ℹ️ I specialize in these 4 SBI Mutual Fund schemes:<br><br>
        🔵 <b>SBI Flexicap Fund</b> — Multi-cap equity<br>
        🟢 <b>SBI Large Cap Fund</b> — Large cap equity<br>
        🟡 <b>SBI ELSS Tax Saver</b> — Tax saving equity<br>
        🟣 <b>SBI Nifty Index Fund</b> — Passive index<br><br>
        Please include the fund name in your question!"""
        st.session_state.messages.append({"role": "bot", "content": bot_msg, "time": now})
        st.rerun()
        return
    
    # Deep Dive
    if any(kw in q.lower() for kw in DEEP_DIVE_KEYWORDS):
        try:
            with open(fund["file"], "r") as f:
                fund_data = json.load(f)
            bot_msg = deep_dive_html(fund_data, fund)
            st.session_state.messages.append({"role": "bot", "content": bot_msg, "time": now})
            st.rerun()
            return
        except Exception:
            pass
    
    # Simple factual
    answer, url = get_fact_answer(q, fund["full"])
    if answer:
        bot_msg = format_answer(answer, url, fund["full"])
        st.session_state.messages.append({"role": "bot", "content": bot_msg, "time": now})
        st.rerun()
        return
    
    # FAQ lookup
    answer, source, scheme = get_faq_answer(q, fund["full"])
    if answer:
        bot_msg = format_answer(f"💡 {answer}", source or fund["url"], scheme or fund["full"])
        st.session_state.messages.append({"role": "bot", "content": bot_msg, "time": now})
        st.rerun()
        return
    
    # Fallback
    bot_msg = f"""I found the fund (<b>{fund['full']}</b>) but couldn't find a specific answer for your query.<br><br>
    Try asking about:<br>
    📊 <i>expense ratio, exit load, lock-in, fund manager, benchmark, NAV, AUM, performance, portfolio, tax, SIP amount</i><br><br>
    <a href="{fund['url']}" target="_blank" class="source-badge">↗ View official scheme document</a>"""
    st.session_state.messages.append({"role": "bot", "content": bot_msg, "time": now})
    st.rerun()

if send and user_input.strip():
    process_and_reply(user_input)
elif st.session_state.pending_query and not send:
    pq = st.session_state.pending_query
    if st.session_state.messages and st.session_state.messages[-1]["content"] == pq:
        pass
    else:
        process_and_reply(pq)

# Clear chat button
if st.session_state.messages:
    if st.button("🗑️ Clear Chat", use_container_width=False):
        st.session_state.messages = []
        st.rerun()

# =====================================================================
# Disclaimer
# =====================================================================
st.markdown("""
<div class="disclaimer">
    🌱 Built for Groww Users · All facts from <a href="https://www.sbimf.com/" target="_blank" style="color:#00d09c;">SBI Mutual Fund Official</a>, SEBI & AMFI<br>
    <b>Disclaimer:</b> For informational purposes only. Not financial advice.
</div>
""", unsafe_allow_html=True)
