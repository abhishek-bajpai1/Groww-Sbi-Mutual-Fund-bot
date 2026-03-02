# 🤖 Groww SBI Mutual Fund FAQ Assistant

A **facts-only RAG (Retrieval-Augmented Generation)** assistant for querying SBI Mutual Fund scheme data. Built for accuracy and transparency — it only answers factual questions sourced from official AMC disclosures and refuses investment advice entirely.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask)
![LangChain](https://img.shields.io/badge/LangChain-0.3-orange?style=flat-square)
![Gemini](https://img.shields.io/badge/Google_Gemini-AI-purple?style=flat-square&logo=google)
![Tests](https://img.shields.io/badge/Tests-14%20Passing-brightgreen?style=flat-square)

---

## ✨ Features

- **RAG Pipeline** — ChromaDB vector store + Gemini AI for factual retrieval
- **Intent Classifier** — Automatically routes factual queries to RAG and blocks investment advice
- **Deep Dive UI** — Interactive cards with CAGR performance grids and top holdings tables
- **Output Validator** — Enforces 3-sentence limit, official source citation, and disclaimer
- **Auto Scheduler** — APScheduler refreshes fund data every 30 days
- **Premium UI** — Groww-branded glassmorphic design with micro-animations

---

## 📊 Supported Schemes

| Fund | Category | Deep Dive |
|---|---|---|
| SBI Large Cap Fund | Equity: Large Cap | ✅ Portfolio + Performance |
| SBI Flexicap Fund | Equity: Flexi Cap | ✅ Portfolio + Performance |
| SBI ELSS Tax Saver Fund | Equity: ELSS | ✅ Portfolio + Performance |
| SBI Nifty Index Fund | Index Fund | ✅ Portfolio + Performance |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/abhishek-bajpai1/Groww-Sbi-Mutual-Fund-bot.git
cd Groww-Sbi-Mutual-Fund-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment
```bash
cp .env.example .env
# Edit .env and add your Google Gemini API Key
# GOOGLE_API_KEY=your_key_here
```

### 4. Build the vector store
```bash
python ingest.py
```

### 5. Run the app
```bash
python app.py
```

Visit **http://127.0.0.1:5001** in your browser.

---

## 🧠 How It Works

```
User Query
    │
    ▼
Intent Classifier
    ├── Advisory Query → Safe Refusal Engine
    └── Factual Query
            │
            ▼
     Structured Data? ─── Yes ──▶ JSON Deep Dive Response
            │
           No
            │
            ▼
     ChromaDB Similarity Search
            │
            ▼
     Gemini Flash LLM
            │
            ▼
     Output Validator (3 sentences, 1 URL)
            │
            ▼
     Final Response to User
```

---

## 🗂️ Project Structure

```
groww-mf-faq/
├── app.py                  # Flask app & routing
├── rag.py                  # RAG retrieval engine
├── classifier.py           # Intent routing
├── validator.py            # Output compliance
├── ingest.py               # Data ingestion
├── scheduler.py            # APScheduler refresh
├── prompts.py              # LLM system prompts
├── sources.csv             # Official source URLs
├── data/
│   └── processed/          # Structured fund JSON files
├── templates/
│   └── index.html          # Premium UI
├── static/css/             # Glassmorphic styles
├── tests/                  # 14-test suite
│   ├── test_app.py
│   ├── test_rag.py
│   ├── test_classifier.py
│   └── test_validator.py
└── vectorstore/            # ChromaDB (auto-generated)
```

---

## 🧪 Running Tests

```bash
export PYTHONPATH=$PYTHONPATH:.
python -m pytest tests/ -v
```

**All 14 tests pass** covering intent classification, RAG flow, output validation, and API endpoints.

---

## 🔒 What It Refuses

The assistant will **never** answer:
- "Should I invest in SBI Large Cap?"
- "Which fund is better?"
- "Will the market go up?"

All advisory queries return a safe refusal with a SEBI investor education link.

---

## 📋 Sample Questions

```
✅ What is the expense ratio of SBI Large Cap Fund?
✅ What is the exit load for SBI Flexicap?
✅ What are the top holdings of SBI Flexicap?
✅ Show me the CAGR performance of SBI ELSS?
✅ What is the lock-in period for the ELSS fund?
✅ How do I download my capital gains statement?

❌ Should I invest in SBI Flexicap? (Refused)
❌ Which fund gives better returns? (Refused)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI / LLM | Google Gemini Flash |
| Embeddings | Google `gemini-embedding-001` |
| Vector DB | ChromaDB |
| Scraping | BeautifulSoup, Requests |
| Scheduler | APScheduler |
| Frontend | HTML, CSS (Glassmorphic) |
| Testing | unittest, pytest |

---

## ⚠️ Disclaimer

This assistant is strictly for **informational purposes only**. All data is sourced from official AMC (SBI Mutual Fund), SEBI, and AMFI sources. It does **not** constitute financial advice or investment recommendations.

---

*Built with ❤️ for Groww users.*
