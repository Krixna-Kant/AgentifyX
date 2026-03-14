"""
AgentifyX FastAPI application — main entry point.
Includes process-document, download-blueprint, and job status endpoints.
"""

import os
import json
import uuid
import traceback
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app.services.document_parser import extract_structured_pages, extract_text_from_pdf
from app.services.semantic_pipeline import chunk_and_enrich, store_embeddings, chunk_text
from app.services.llm_engine import generate_agentic_blueprint
from app.services.code_generator import generate_crewai_script
from app.services.boilerplate_generator import generate_boilerplate, SUPPORTED_FRAMEWORKS
from app.services.graph_builder import build_graph_spec
from app.services.github_analyzer import analyze_github_repo
from app.routers.chat import router as chat_router
from app.routers.roster_chat import router as roster_chat_router
from app.db.database import init_db, SessionLocal
from app.db.models import AnalysisSession

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgentifyX Middleware",
    description="API for transforming conventional solutions into Agentic AI frameworks.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(roster_chat_router)

# Initialize DB tables on startup
@app.on_event("startup")
def startup_event():
    init_db()

# ── In-memory job store ──────────────────────────────────────────────────────
_jobs: dict[str, dict] = {}


def _update_job(job_id: str, stage: str, progress: int, detail: str = ""):
    """Update job status in the in-memory store."""
    _jobs[job_id] = {
        "job_id": job_id,
        "stage": stage,
        "progress": progress,
        "detail": detail,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ═════════════════════════════════════════════════════════════════════════════
#  Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Return service health status."""
    services = {
        "gemini_api": False,
        "chromadb": False,
        "sentence_transformers": False,
        "sqlite": False,
    }
    # Gemini — just check if API key is set (don't waste quota)
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY") or genai._config._api_key
        services["gemini_api"] = bool(api_key)
    except Exception:
        services["gemini_api"] = bool(os.environ.get("GEMINI_API_KEY"))
    # ChromaDB
    try:
        import chromadb
        client = chromadb.Client()
        client.heartbeat()
        services["chromadb"] = True
    except Exception:
        pass
    # Sentence Transformers
    try:
        from sentence_transformers import SentenceTransformer
        services["sentence_transformers"] = True
    except Exception:
        pass
    # SQLite
    try:
        from sqlalchemy import text as sa_text
        db = SessionLocal()
        db.execute(sa_text("SELECT 1"))
        db.close()
        services["sqlite"] = True
    except Exception:
        try:
            import sqlite3
            conn = sqlite3.connect("agentifyx.db")
            conn.execute("SELECT 1")
            conn.close()
            services["sqlite"] = True
        except Exception:
            pass

    all_ok = all(services.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": services,
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini"),
        "groq_configured": bool(os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY") != "your_groq_key_here"),
        "version": "2.0.0",
    }

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Return current processing status for a given job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return _jobs[job_id]


# ── Load industry templates ──────────────────────────────────────────────────
def _load_industry_templates() -> dict:
    templates_path = Path(__file__).parent / "data" / "industry_templates.json"
    if templates_path.exists():
        with open(templates_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"templates": []}


def _get_industry_context(industry_id: str | None) -> str:
    if not industry_id or industry_id == "general":
        return ""
    data = _load_industry_templates()
    for tmpl in data.get("templates", []):
        if tmpl["id"] == industry_id:
            return tmpl.get("domain_context", "")
    return ""


@app.get("/api/v1/industry-templates")
async def get_industry_templates():
    """Return the list of available industry templates."""
    return _load_industry_templates()


@app.post("/api/v1/process-document")
async def process_document(
    file: UploadFile = File(None),
    industry_id: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    github_pat: Optional[str] = Form(None),
):
    if not file and not github_url:
        raise HTTPException(status_code=400, detail="Provide a PDF file and/or a GitHub repo URL.")

    if file and not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Currently, only PDF files are supported. Please upload a .pdf file.",
        )

    job_id = str(uuid.uuid4())
    _update_job(job_id, "starting", 0, "Initializing pipeline...")

    github_result = None
    code_context = ""

    try:
        # ── GitHub Analysis (optional) ─────────────────────────
        if github_url:
            _update_job(job_id, "analyzing_github", 5, "Analyzing GitHub repository...")
            github_result = analyze_github_repo(github_url, pat=github_pat or None)
            if github_result.get("error"):
                raise HTTPException(status_code=422, detail=github_result["error"])
            # Build code context for Gemini
            cs = github_result.get("code_summary", {})
            code_context = (
                f"\n\nCODE ANALYSIS from GitHub repo ({github_result.get('repo_name','')}):\n"
                f"Files analyzed: {cs.get('total_files_analyzed', 0)}\n"
                f"Functions: {cs.get('total_functions', 0)} "
                f"({len(cs.get('agent_candidate_functions', []))} agent candidates)\n"
                f"Primary frameworks: {', '.join(cs.get('primary_frameworks', []))}\n"
                f"External imports: {', '.join(cs.get('all_external_imports', [])[:20])}\n"
            )
            candidates = cs.get("agent_candidate_functions", [])
            if candidates:
                code_context += "Agent candidate functions (high complexity):\n"
                for c in candidates[:10]:
                    code_context += f"  - {c['file']}::{c['function']}() — {c['reason']}\n"
            code_context += (
                "\nWhen recommending agents, reference specific function names "
                "from the code analysis where relevant."
            )

        # ── PDF Analysis ────────────────────────────────────────
        parsed_pages = []
        chunks_stored = 0
        doc_filename = "github_analysis"

        if file:
            doc_filename = file.filename
            _update_job(job_id, "parsing", 10, "Extracting text, tables, and images from PDF...")
            contents = await file.read()

            try:
                parsed_pages = extract_structured_pages(contents)
            except Exception as parse_err:
                logger.warning("Structured extraction failed: %s", parse_err)
                raise HTTPException(
                    status_code=422,
                    detail=f"PDF parsing failed: {parse_err}.",
                )

            _update_job(job_id, "chunking", 30, "Splitting text into chunks and extracting entities...")
            enriched_chunks = chunk_and_enrich(parsed_pages, source_document=file.filename)

            _update_job(job_id, "embedding", 50, "Generating embeddings and storing in vector database...")
            chunks_stored = store_embeddings(file.filename, enriched_chunks)

        # Phase 3: Reason & Generate Blueprint (with industry + code context)
        _update_job(job_id, "reasoning", 70, "Gemini is analyzing and generating the agentic blueprint...")
        industry_context = _get_industry_context(industry_id)
        full_context = (industry_context or "") + code_context
        blueprint = generate_agentic_blueprint(doc_filename, industry_context=full_context or None)

        # Build vis.js graph spec from roster data
        blueprint["graph_spec"] = build_graph_spec(blueprint)

        _update_job(job_id, "complete", 100, "Analysis complete!")

        result = {
            "job_id": job_id,
            "filename": doc_filename,
            "status": "success",
            "pipeline_metrics": {
                "chunks_stored": chunks_stored,
                "pages_parsed": len(parsed_pages),
                "image_descriptions": sum(
                    1 for p in parsed_pages if p.get("content_type") == "image_description"
                ) if parsed_pages else 0,
            },
            "Agent Architecture File": (
                "Successfully generated!"
            ),
            "agentifyx_analysis": blueprint,
        }

        if github_result:
            result["github_analysis"] = github_result.get("code_summary")
            result["github_repo"] = github_result.get("repo_name")
            if github_result.get("warning"):
                result["github_warning"] = github_result["warning"]

        # Save session to SQLite
        try:
            db = SessionLocal()
            session = AnalysisSession(
                id=job_id,
                created_at=datetime.now(timezone.utc),
                document_name=doc_filename,
                industry_id=industry_id,
                framework_selected=blueprint.get("recommended_framework"),
                composite_readiness=blueprint.get("composite_readiness", 0),
                roster_json=json.dumps(blueprint),
                chat_history="[]",
            )
            db.add(session)
            db.commit()
            db.close()
        except Exception as db_err:
            logger.warning("Failed to save session: %s", db_err)

        return result

    except HTTPException:
        _update_job(job_id, "failed", 0, "Processing failed.")
        raise  # re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error("Unexpected error: %s", traceback.format_exc())
        _update_job(job_id, "failed", 0, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during document processing: {e}",
        )


@app.post("/api/v1/download-blueprint")
async def download_blueprint(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        contents = await file.read()

        try:
            parsed_pages = extract_structured_pages(contents)
        except Exception:
            # Fallback to legacy extraction
            raw_text = extract_text_from_pdf(contents)
            text_chunks = chunk_text(raw_text)
            store_embeddings(file.filename, [
                {"text": c, "page_number": 0, "section_title": "", "content_type": "text",
                 "source_document": file.filename, "chunk_index": i, "extracted_entities": []}
                for i, c in enumerate(text_chunks)
            ])
            blueprint = generate_agentic_blueprint(file.filename)
            python_code = generate_crewai_script(blueprint)
            return Response(
                content=python_code,
                media_type="text/x-python",
                headers={"Content-Disposition": 'attachment; filename="agentic_architecture.py"'},
            )

        enriched_chunks = chunk_and_enrich(parsed_pages, source_document=file.filename)
        store_embeddings(file.filename, enriched_chunks)
        blueprint = generate_agentic_blueprint(file.filename)

        python_code = generate_crewai_script(blueprint)

        return Response(
            content=python_code,
            media_type="text/x-python",
            headers={"Content-Disposition": 'attachment; filename="agentic_architecture.py"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Blueprint generation error: %s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate blueprint: {e}",
        )


@app.post("/api/v1/generate-boilerplate")
async def generate_boilerplate_endpoint(
    roster_json: str = Form(...),
    framework: str = Form("CrewAI"),
):
    """Generate framework-specific boilerplate from an AgentRoster JSON."""
    if framework not in SUPPORTED_FRAMEWORKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported framework: '{framework}'. Supported: {SUPPORTED_FRAMEWORKS}",
        )
    try:
        roster = json.loads(roster_json)
        code = generate_boilerplate(roster, framework)
        return {"framework": framework, "code": code}
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON in roster_json.")
    except Exception as e:
        logger.error("Boilerplate generation error: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Code generation failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
#  Session Endpoints
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/v1/sessions")
async def list_sessions(limit: int = 5):
    """Return the last N analysis sessions."""
    db = SessionLocal()
    try:
        sessions = (
            db.query(AnalysisSession)
            .order_by(AnalysisSession.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "document_name": s.document_name,
                "industry_id": s.industry_id,
                "framework_selected": s.framework_selected,
                "composite_readiness": s.composite_readiness,
            }
            for s in sessions
        ]
    finally:
        db.close()


@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str):
    """Load a full session by ID."""
    db = SessionLocal()
    try:
        session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
        return {
            "id": session.id,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "document_name": session.document_name,
            "industry_id": session.industry_id,
            "framework_selected": session.framework_selected,
            "composite_readiness": session.composite_readiness,
            "roster_json": json.loads(session.roster_json) if session.roster_json else None,
            "chat_history": json.loads(session.chat_history) if session.chat_history else [],
        }
    finally:
        db.close()


@app.put("/api/v1/sessions/{session_id}/chat")
async def update_chat_history(session_id: str, chat_history: list[dict]):
    """Update the chat history for a session."""
    db = SessionLocal()
    try:
        session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
        session.chat_history = json.dumps(chat_history)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()