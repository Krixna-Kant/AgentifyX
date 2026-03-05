# 🚀 AgentifyX

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?logo=google&logoColor=white)
![TECHgium](https://img.shields.io/badge/TECHgium-9th_Edition-7C3AED)

**Transform conventional software systems into Agentic AI architectures.**  
Upload legacy system documentation (PDF) or point to a GitHub repo — AgentifyX analyzes the codebase, recommends an optimal agent architecture, generates framework-specific boilerplate, and produces enterprise-grade reports with interactive architecture diagrams.

---

## ✅ Features

| Feature | Status |
|---------|--------|
| 📄 Multimodal PDF extraction (text, tables, images via Gemini Vision) | ✅ |
| 🧠 Semantic chunking + NER with spaCy | ✅ |
| 🔍 Vector search with ChromaDB + Sentence Transformers | ✅ |
| 🤖 Gemini-powered agentic blueprint generation | ✅ |
| 📊 7-dimension readiness radar chart | ✅ |
| 🏭 Industry-specific context templates (Healthcare, Finance, etc.) | ✅ |
| 🔧 Multi-framework boilerplate (CrewAI, LangGraph, AutoGen) | ✅ |
| ⚠️ HITL checkpoint code generator | ✅ |
| 🛠️ Automated tools recommendation catalog | ✅ |
| 💬 Streaming RAG chatbot with session persistence | ✅ |
| 🕸️ Interactive vis.js agent graph (drag, zoom, click) | ✅ |
| 🗺️ Mermaid flowchart & sequence diagrams | ✅ |
| 🔗 GitHub repo analyzer with AST-based code analysis | ✅ |
| ▶️ Agent pipeline simulation with HITL pause/approve/reject | ✅ |
| 📄 PDF & DOCX report generation (10 sections each) | ✅ |
| 📥 Full export (PDF/DOCX/JSON/Code/Diagrams) | ✅ |
| 🎯 Demo mode (zero API calls, all 7 tabs work) | ✅ |
| 🩺 Health check endpoint with service status | ✅ |
| 🌙 Dark theme with premium aesthetics | ✅ |

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/Krixna-Kant/AgentifyX.git
cd AgentifyX
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your key at: [Google AI Studio](https://aistudio.google.com/apikey)

### 3. Run

**Terminal 1 — FastAPI Backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run app/frontend.py
```

Open **http://localhost:8501** in your browser.

### 4. Demo Mode (For Judges)

Click **🎯 Load Demo** in the sidebar to instantly explore all 7 tabs with a pre-computed customer support system analysis — no API calls needed.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit + Plotly + vis.js |
| Backend | FastAPI + Uvicorn |
| AI/LLM | Google Gemini 2.0 Flash |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB |
| NLP | spaCy (en_core_web_sm) |
| Reports | ReportLab (PDF) + python-docx (DOCX) |
| Database | SQLite (via SQLAlchemy) |
| Code Analysis | PyGitHub + Python AST |

---

## 📁 Project Structure

```
AgentifyX/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── frontend.py                # Streamlit 7-tab dashboard
│   ├── schemas/
│   │   └── agent_roster.py        # Pydantic AgentRoster schema
│   ├── services/
│   │   ├── llm_engine.py          # Gemini blueprint generation
│   │   ├── document_parser.py     # PDF extraction
│   │   ├── semantic_pipeline.py   # Chunking + embedding
│   │   ├── boilerplate_generator.py  # Multi-framework code gen
│   │   ├── graph_builder.py       # vis.js graph spec builder
│   │   ├── github_analyzer.py     # GitHub repo + AST analysis
│   │   ├── simulation_generator.py   # Pipeline simulation
│   │   ├── hitl_generator.py      # HITL checkpoint code gen
│   │   ├── tools_matcher.py       # Tools recommendation
│   │   ├── report_generator.py    # PDF report (ReportLab)
│   │   └── docx_generator.py      # DOCX report (python-docx)
│   ├── routers/
│   │   └── chat.py                # Streaming chat endpoint
│   ├── db/
│   │   ├── database.py            # SQLite session storage
│   │   └── models.py              # SQLAlchemy models
│   ├── data/
│   │   ├── industry_templates.json
│   │   └── tools_catalog.json
│   └── demo/
│       └── demo_roster.json       # Pre-computed demo data
├── requirements.txt
├── .env
└── README.md
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service health check |
| `POST` | `/api/v1/process-document` | Analyze PDF + optional GitHub |
| `GET` | `/api/v1/industry-templates` | List industry templates |
| `POST` | `/api/v1/generate-boilerplate` | Generate framework code |
| `POST` | `/api/chat` | Streaming RAG chatbot |
| `GET` | `/api/v1/sessions` | List analysis sessions |
| `GET` | `/api/v1/sessions/{id}` | Get session details |

---

## 📜 License

Built for **TECHgium 9th Edition** hackathon.