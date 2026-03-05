"""
LLM reasoning engine — provider-agnostic wrapper supporting Gemini and Groq.
Sends enriched context to the configured LLM with structured JSON output.
All responses are parsed into the AgentRoster Pydantic schema.
"""

import os
import json
import time
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv

from app.schemas.agent_roster import AgentRoster
from app.services.semantic_pipeline import query_collection

load_dotenv()
logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


# ═════════════════════════════════════════════════════════════════════════════
#  Provider Backends
# ═════════════════════════════════════════════════════════════════════════════

def _generate_gemini(prompt: str, system_prompt: str = "") -> str:
    """Generate text using Google Gemini 1.5 Flash with retry logic."""
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        ),
    )

    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

    for attempt in range(3):
        try:
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            if "429" in str(e) or "quota" in err_str or "rate" in err_str:
                wait = (2 ** attempt) * 2  # 2s, 4s, 8s
                logger.warning(
                    "Gemini rate limit — retrying in %ds (attempt %d/3)", wait, attempt + 1
                )
                time.sleep(wait)
            else:
                raise e
    raise Exception(
        "Gemini rate limit exceeded after 3 retries. "
        "Switch to Groq by setting LLM_PROVIDER=groq in .env, or wait and retry."
    )


def _generate_groq(prompt: str, system_prompt: str = "") -> str:
    """Generate text using Groq (Llama 3.3 70B Versatile)."""
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def generate_text(prompt: str, system_prompt: str = "") -> str:
    """Provider-agnostic text generation. Respects LLM_PROVIDER env var."""
    if LLM_PROVIDER == "groq":
        return _generate_groq(prompt, system_prompt)
    else:
        return _generate_gemini(prompt, system_prompt)


# ═════════════════════════════════════════════════════════════════════════════
#  Public API
# ═════════════════════════════════════════════════════════════════════════════

def query_vector_db(query_text: str, n_results: int = 5, source: str | None = None) -> str:
    """Retrieve the most relevant chunks from ChromaDB."""
    results = query_collection(query_text, n_results=n_results, source_filter=source)

    if results["documents"] and len(results["documents"]) > 0:
        parts: list[str] = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            prefix = (
                f"[Page {meta.get('page_number', '?')} | "
                f"Section: {meta.get('section_title', 'N/A')} | "
                f"Type: {meta.get('content_type', 'text')}]"
            )
            parts.append(f"{prefix}\n{doc}")
        return "\n\n---\n\n".join(parts)

    return "No relevant context found in the database."


def generate_agentic_blueprint(filename: str, industry_context: str = "") -> dict:
    """
    Analyze document context and generate a transformation blueprint.
    Returns a validated AgentRoster dict.
    Uses a SINGLE merged ChromaDB query to minimize API calls.
    """
    # Single merged query instead of 3 separate ones
    merged_query = (
        "system architecture workflows decision logic legacy limitations "
        "data flow integration automation technology stack dependencies"
    )
    context = query_vector_db(merged_query, n_results=10, source=filename)

    # Build industry prefix if provided
    industry_prefix = ""
    if industry_context:
        industry_prefix = (
            f"INDUSTRY CONTEXT:\n{industry_context}\n\n"
            "Apply domain-specific knowledge, compliance requirements, and typical "
            "agent patterns for this industry when making recommendations.\n\n"
        )

    prompt = f"""{industry_prefix}You are AgentifyX, an expert AI middleware engine specializing in
transforming legacy systems into Agentic AI architectures.

DOCUMENT CONTEXT (extracted from "{filename}"):
{context}

INSTRUCTIONS:
1. Analyze the document context above carefully.
2. For each proposed agent, cite the specific page number and a short snippet from
   the document that supports your recommendation in "evidence_citations".
3. Score each of these 7 readiness dimensions from 0 to 100:
   - TaskDecomposability: Can the system's work be broken into discrete agent tasks?
   - DecisionComplexity: How complex are the decision points that agents must handle?
   - ToolIntegrability: How easily can external tools/APIs be integrated?
   - AutonomyPotential: How much can be automated without human intervention?
   - DataAvailability: Is sufficient data available for agent decision-making?
   - RiskLevel: What is the risk level? (higher score = lower risk = more suitable)
   - ROIPotential: What is the expected return on investment from transformation?
4. Calculate composite_readiness as the weighted average of all 7 dimensions.
5. For each agent, set confidence_score (0.0-1.0) based on how strongly the
   document evidence supports that agent's existence.
6. Set hitl_required=true and list hitl_checkpoints for any agent handling
   sensitive decisions, financial data, or customer-facing outputs.
7. List any assumptions you made in "assumptions_made".
8. List any information gaps in the document in "data_gaps".
9. Recommend a framework (CrewAI, LangGraph, AutoGen, or custom).
10. legacy_pain_points: Identify 4-6 specific bottlenecks, manual steps, or
    limitations in the current system from the document. For each, specify
    severity (high/medium/low) and which proposed agent resolves it.
11. mermaid_flowchart: Generate a Mermaid graph TD diagram showing the agent workflow.
    Use agent names as nodes. Show data flow with arrows and labels.
    Mark HITL nodes with diamond shape like C{{HITL: Human Review}}.
    Return ONLY the diagram source code starting with "graph TD".
12. mermaid_sequence: Generate a Mermaid sequenceDiagram showing inter-agent communication.
    Return ONLY the diagram source code starting with "sequenceDiagram".

Use chain-of-thought reasoning: think step by step about each dimension and agent
before writing your final answer.

REQUIRED JSON SCHEMA — your response must be a single JSON object with exactly these fields:
{{
  "document_name": "{filename}",
  "analysis_timestamp": "{datetime.now(timezone.utc).isoformat()}",
  "readiness_scores": {{
    "TaskDecomposability": <int 0-100>,
    "DecisionComplexity": <int 0-100>,
    "ToolIntegrability": <int 0-100>,
    "AutonomyPotential": <int 0-100>,
    "DataAvailability": <int 0-100>,
    "RiskLevel": <int 0-100>,
    "ROIPotential": <int 0-100>
  }},
  "composite_readiness": <float 0-100>,
  "agents": [
    {{
      "agent_id": "<unique string>",
      "agent_name": "<name>",
      "role": "<role>",
      "goal": "<goal>",
      "tools_required": ["<tool1>", ...],
      "input_sources": ["<source1>", ...],
      "output_artifacts": ["<artifact1>", ...],
      "hitl_required": <bool>,
      "hitl_checkpoints": ["<checkpoint1>", ...],
      "confidence_score": <float 0.0-1.0>,
      "evidence_citations": [{{"page": <int>, "snippet": "<text>"}}]
    }}
  ],
  "recommended_framework": "<CrewAI|LangGraph|AutoGen|custom>",
  "transformation_summary": "<paragraph>",
  "assumptions_made": ["<assumption1>", ...],
  "data_gaps": ["<gap1>", ...],
  "legacy_pain_points": [
    {{"pain_point": "<description>", "severity": "high|medium|low", "agent_solution": "<agent_id>"}}
  ],
  "mermaid_flowchart": "graph TD\\n  A[Agent1] --> B[Agent2]\\n  ...",
  "mermaid_sequence": "sequenceDiagram\\n  User->>Agent1: input\\n  ..."
}}

IMPORTANT: Return ONLY a valid JSON object matching the schema above. No markdown, no extra text.
"""

    try:
        raw_text = generate_text(prompt)

        # Parse and validate through Pydantic
        try:
            roster = AgentRoster.model_validate_json(raw_text)
            return roster.model_dump()
        except Exception as parse_err:
            logger.warning("Pydantic validation failed, attempting JSON parse: %s", parse_err)
            data = json.loads(raw_text)
            return data

    except Exception as e:
        logger.error("LLM generation failed (%s): %s", LLM_PROVIDER, e)
        fallback = AgentRoster(
            document_name=filename,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            transformation_summary=f"Analysis failed: {e}",
            data_gaps=["LLM generation failed — please retry."],
        )
        return fallback.model_dump()