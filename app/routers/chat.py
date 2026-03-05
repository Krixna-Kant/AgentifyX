"""
Chat endpoint — streaming RAG-powered chatbot using Gemini/Groq + ChromaDB context.
"""

import os
import json
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.semantic_pipeline import query_collection

load_dotenv()
logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str
    conversation_history: list[dict] = []  # [{"role": "user"|"assistant", "content": str}]
    roster_json: dict | None = None
    source_document: str | None = None


SYSTEM_PROMPT = """You are AgentifyX Assistant, an expert in agentic AI systems, CrewAI, LangGraph,
AutoGen, and enterprise AI transformation. You have analyzed the user's system
documentation and generated an agent architecture recommendation for them.

Your job: Answer questions about WHY specific agents were recommended, HOW to
implement specific parts of the architecture, framework trade-offs, HITL patterns,
and industry-specific best practices.

DOCUMENT EVIDENCE (retrieved from the analyzed document):
{retrieved_chunks}

GENERATED AGENT ARCHITECTURE:
{roster_summary}

RULES:
- When answering "why" questions, ALWAYS cite the document page and snippet
- Format citations as: (Source: Page N)
- If you don't have evidence, say: "The document doesn't explicitly mention this, but..."
- Never invent page numbers or document quotes
- Keep answers concise (3-5 sentences unless more detail is needed)
- Be conversational, not formal
"""


def _build_roster_summary(roster: dict | None) -> str:
    """Build a concise text summary of the AgentRoster for the system prompt."""
    if not roster:
        return "No architecture has been generated yet."

    parts = []
    parts.append(f"Document: {roster.get('document_name', 'Unknown')}")
    parts.append(f"Composite Readiness: {roster.get('composite_readiness', 0):.0f}/100")
    parts.append(f"Recommended Framework: {roster.get('recommended_framework', 'N/A')}")
    parts.append(f"Summary: {roster.get('transformation_summary', 'N/A')}")

    agents = roster.get("agents", [])
    if agents:
        parts.append(f"\nProposed Agents ({len(agents)}):")
        for a in agents:
            hitl = " [HITL REQUIRED]" if a.get("hitl_required") else ""
            parts.append(
                f"  - {a.get('agent_name', a.get('role', '?'))}: "
                f"{a.get('goal', '')}{hitl}"
            )

    pain_points = roster.get("legacy_pain_points", [])
    if pain_points:
        parts.append(f"\nLegacy Pain Points ({len(pain_points)}):")
        for pp in pain_points:
            parts.append(f"  - [{pp.get('severity', '?')}] {pp.get('pain_point', '')}")

    return "\n".join(parts)


def _retrieve_context(query: str, source_document: str | None) -> str:
    """Retrieve relevant chunks from ChromaDB."""
    try:
        results = query_collection(
            query_text=query,
            n_results=4,
            source_filter=source_document,
        )
        if results and results.get("documents"):
            docs = results["documents"][0] if isinstance(results["documents"][0], list) else results["documents"]
            metas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

            chunks = []
            for i, doc in enumerate(docs):
                meta = metas[i] if i < len(metas) else {}
                page = meta.get("page_number", "?")
                section = meta.get("section_title", "")
                prefix = f"[Page {page}"
                if section:
                    prefix += f" — {section}"
                prefix += "]"
                chunks.append(f"{prefix}\n{doc}")
            return "\n\n---\n\n".join(chunks)
    except Exception as e:
        logger.warning("ChromaDB retrieval failed: %s", e)
    return "No document context available."


async def _stream_gemini(prompt_parts: list[dict], system_instruction: str):
    """Stream tokens from Gemini."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=system_instruction,
        )
        response = model.generate_content(prompt_parts, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        logger.error("Gemini streaming error: %s", e)
        yield f"\n\n⚠️ Error generating response: {e}"


async def _stream_groq(messages: list[dict]):
    """Stream tokens from Groq."""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except Exception as e:
        logger.error("Groq streaming error: %s", e)
        yield f"\n\n⚠️ Error generating response: {e}"


@router.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Streaming chat endpoint with RAG context."""
    # 1. Retrieve relevant chunks
    retrieved = _retrieve_context(req.message, req.source_document)

    # 2. Build roster summary
    roster_summary = _build_roster_summary(req.roster_json)

    # 3. Build system prompt
    system_prompt = SYSTEM_PROMPT.format(
        retrieved_chunks=retrieved,
        roster_summary=roster_summary,
    )

    # 4. Build conversation (last 10 turns = 20 messages max)
    history = req.conversation_history[-20:] if req.conversation_history else []

    # 5. Stream response based on provider
    if LLM_PROVIDER == "groq":
        # Groq uses OpenAI-compatible message format
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": req.message})

        async def generate():
            async for token in _stream_groq(messages):
                yield token
    else:
        # Gemini format
        prompt_parts = []
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            prompt_parts.append({"role": role, "parts": [msg.get("content", "")]})
        prompt_parts.append({"role": "user", "parts": [req.message]})

        async def generate():
            async for token in _stream_gemini(prompt_parts, system_prompt):
                yield token

    return StreamingResponse(generate(), media_type="text/plain")
