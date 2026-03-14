"""
Roster Chat — Conversational Plan Refinement endpoint.
Allows users to add, modify, or remove agents from the roster
through natural language conversation with Gemini/Groq.
"""

import os
import re
import json
import logging
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from app.schemas.agent_roster import AgentRoster, AgentDetail
from app.services.llm_engine import generate_text
from app.services.graph_builder import build_graph_spec
from app.services.semantic_pipeline import query_collection

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(tags=["roster-chat"])


# ═════════════════════════════════════════════════════════════════════════════
#  System Prompt
# ═════════════════════════════════════════════════════════════════════════════

ARCHITECT_SYSTEM_PROMPT = """You are an expert AI systems architect assistant for AgentifyX.
You are helping a user refine an agent roster for transforming a legacy system.

You have access to:
1. The CURRENT AGENT ROSTER (full JSON) — provided below
2. RELEVANT DOCUMENT CONTEXT — chunks from the original source document
3. CONVERSATION HISTORY — the dialogue so far

YOUR BEHAVIOR RULES:
- If the user's request is AMBIGUOUS: respond with response_type="message"
  and ask exactly ONE clarifying question. Do not make assumptions.
- If the user's request is CLEAR or they have confirmed after your question:
  respond with response_type="roster_update" and return the COMPLETE updated roster.
- Never partially update the roster. Always return the FULL roster JSON with ALL agents.
- When adding an agent, you MUST include: agent_id, agent_name, role, goal,
  tools_required, input_sources, output_artifacts, hitl_required,
  hitl_checkpoints, confidence_score, evidence_citations.
- For evidence_citations: cite actual page numbers from the document context
  if available. If no evidence exists, set confidence_score to 0.5 and note
  the assumption in evidence_citations as [{{"page": 0, "snippet": "User-requested addition"}}].
- When modifying composite_readiness score: recalculate as average of all
  readiness_scores dimensions.
- Always regenerate mermaid_flowchart and mermaid_sequence to include
  new/modified agents.
- Keep all existing agents EXACTLY as they are unless the user explicitly asks
  to modify or remove them. Do NOT drop, rename, or alter untouched agents.

CRITICAL: Your entire response must be valid JSON. No text outside the JSON.
No markdown code blocks. No preamble. Raw JSON only.

RESPONSE SCHEMA:
For conversational replies:
{{"response_type": "message", "content": "your response here"}}

For roster updates:
{{
  "response_type": "roster_update",
  "content": "Human-readable summary of what changed",
  "updated_roster": {{ <COMPLETE AgentRoster JSON — every field including all existing agents> }},
  "changes_summary": {{
    "added": ["AgentName1"],
    "modified": ["AgentName2 — what changed"],
    "removed": ["AgentName3"]
  }}
}}

CURRENT ROSTER:
{roster_json}

DOCUMENT CONTEXT:
{document_context}
"""


# ═════════════════════════════════════════════════════════════════════════════
#  Request / Response Models
# ═════════════════════════════════════════════════════════════════════════════

class ModifyRosterRequest(BaseModel):
    message: str
    current_roster: dict
    conversation_history: list[dict] = []
    source_document: Optional[str] = None
    clarification_count: int = 0


class ModifyRosterResponse(BaseModel):
    response_type: str              # "message" or "roster_update"
    content: str                    # Human-readable summary
    updated_roster: Optional[dict] = None
    changes_summary: Optional[dict] = None
    error: Optional[str] = None


# ═════════════════════════════════════════════════════════════════════════════
#  Safety: Roster Integrity Validation
# ═════════════════════════════════════════════════════════════════════════════

def validate_roster_update(
    original_roster: dict,
    updated_roster: dict,
    changes_summary: dict,
) -> tuple[bool, str]:
    """
    Prevents silent agent loss — the most dangerous failure mode.
    Checks that agents not mentioned in changes_summary still exist.
    """
    original_agents = original_roster.get("agents", [])
    updated_agents = updated_roster.get("agents", [])

    original_count = len(original_agents)
    updated_count = len(updated_agents)
    agents_added = len(changes_summary.get("added", []))
    agents_removed = len(changes_summary.get("removed", []))

    expected_count = original_count + agents_added - agents_removed

    # Allow ±1 tolerance for edge cases
    if abs(updated_count - expected_count) > 1:
        return False, (
            f"Roster integrity check failed: had {original_count} agents, "
            f"summary says +{agents_added}/-{agents_removed}, "
            f"but received {updated_count} agents. Rejecting update to prevent data loss."
        )

    # Check that surviving agents still exist
    removed_names = set(changes_summary.get("removed", []))
    added_names = set(changes_summary.get("added", []))

    original_agent_names = {
        a.get("agent_name", a.get("role", "")) for a in original_agents
    }
    updated_agent_names = {
        a.get("agent_name", a.get("role", "")) for a in updated_agents
    }

    should_survive = original_agent_names - removed_names
    actually_survived = updated_agent_names - added_names

    missing = should_survive - actually_survived
    if missing:
        return False, f"Agents unexpectedly removed from roster: {missing}"

    return True, "OK"


# ═════════════════════════════════════════════════════════════════════════════
#  Document Context Retrieval
# ═════════════════════════════════════════════════════════════════════════════

def _retrieve_document_context(query: str, source_document: Optional[str]) -> str:
    """Retrieve relevant chunks from ChromaDB for the architect prompt."""
    try:
        results = query_collection(
            query_text=query,
            n_results=4,
            source_filter=source_document,
        )
        if results and results.get("documents"):
            docs = (
                results["documents"][0]
                if isinstance(results["documents"][0], list)
                else results["documents"]
            )
            metas = (
                results.get("metadatas", [[]])[0]
                if results.get("metadatas")
                else []
            )

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


# ═════════════════════════════════════════════════════════════════════════════
#  Smart Suggestion Generator
# ═════════════════════════════════════════════════════════════════════════════

def generate_architect_suggestions(roster: dict) -> list[str]:
    """Generate contextually relevant suggestion chips from the current roster."""
    suggestions = []
    agents = roster.get("agents", [])

    if agents:
        # Find the lowest confidence agent
        sorted_agents = sorted(agents, key=lambda a: a.get("confidence_score", 1))
        weakest = sorted_agents[0]
        conf_pct = int(weakest.get("confidence_score", 0) * 100)
        suggestions.append(
            f"🔍 Strengthen {weakest.get('agent_name', 'agent')} — "
            f"confidence is only {conf_pct}%"
        )

        # Find agents with no HITL that might need it
        risky_keywords = [
            "payment", "email", "delete", "send", "billing",
            "notify", "refund", "transfer", "approve",
        ]
        for agent in agents:
            goal = agent.get("goal", "").lower()
            if not agent.get("hitl_required") and any(
                kw in goal for kw in risky_keywords
            ):
                suggestions.append(
                    f"🔒 Add HITL checkpoint to {agent.get('agent_name', 'agent')} "
                    f"— it performs risky actions"
                )
                break

    # Check data_gaps from roster
    data_gaps = roster.get("data_gaps", [])
    if data_gaps:
        gap_text = data_gaps[0][:60]
        suggestions.append(f"📋 Address data gap: {gap_text}...")

    # Generic intelligent fallbacks
    suggestions.append("🛡️ Add an error handling and retry agent")
    suggestions.append("📡 Add a real-time monitoring and alerting agent")

    return suggestions[:4]


# ═════════════════════════════════════════════════════════════════════════════
#  Endpoint
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/api/chat/modify-roster", response_model=ModifyRosterResponse)
async def modify_roster(request: ModifyRosterRequest):
    """
    Conversational roster modification endpoint.
    Accepts user messages + full roster context, returns either a
    conversational reply or a validated roster update.
    """
    try:
        # Step 1: Retrieve relevant document chunks
        document_context = _retrieve_document_context(
            request.message, request.source_document
        )

        # Step 2: Build system prompt with roster + document context
        force_commit = ""
        if request.clarification_count >= 2:
            force_commit = (
                "\n\nIMPORTANT: The user has answered your clarifying question. "
                "Stop asking questions. Make the change now and return "
                "response_type='roster_update' with the COMPLETE updated roster."
            )

        system_prompt = ARCHITECT_SYSTEM_PROMPT.format(
            roster_json=json.dumps(request.current_roster, indent=2),
            document_context=document_context,
        ) + force_commit

        # Step 3: Build conversation messages for context
        history_messages = request.conversation_history[-8:]
        conversation_text = ""
        for msg in history_messages:
            role_label = "User" if msg.get("role") == "user" else "Assistant"
            conversation_text += f"\n{role_label}: {msg.get('content', '')}"
        conversation_text += f"\nUser: {request.message}"

        full_prompt = f"{system_prompt}\n\nCONVERSATION:\n{conversation_text}"

        # Step 4: Call LLM in JSON mode
        raw_response = generate_text(full_prompt)

        # Step 5: Parse response (handle markdown-wrapped JSON)
        try:
            response_data = json.loads(raw_response)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown fences
            json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if json_match:
                try:
                    response_data = json.loads(json_match.group())
                except json.JSONDecodeError as e2:
                    logger.error("Failed to parse LLM response: %s", e2)
                    return ModifyRosterResponse(
                        response_type="message",
                        content="I had trouble processing that request. Could you rephrase it?",
                        error=f"JSON parse error: {e2}",
                    )
            else:
                logger.error("No JSON found in LLM response: %s", raw_response[:200])
                return ModifyRosterResponse(
                    response_type="message",
                    content="I had trouble processing that request. Could you rephrase it?",
                    error="No JSON in LLM response",
                )

        response_type = response_data.get("response_type", "message")

        # Step 6: If roster update — validate thoroughly
        if response_type == "roster_update":
            updated_roster_raw = response_data.get("updated_roster", {})
            changes_summary = response_data.get("changes_summary", {})

            # Pydantic validation
            try:
                updated_roster_obj = AgentRoster(**updated_roster_raw)
            except (ValidationError, Exception) as e:
                logger.error("Roster validation failed: %s", e)
                return ModifyRosterResponse(
                    response_type="message",
                    content=(
                        "I generated an update but it failed validation. "
                        "Please try rephrasing your request. "
                        f"(Detail: {str(e)[:120]})"
                    ),
                    error=str(e),
                )

            # Integrity check — prevent silent agent loss
            is_valid, integrity_msg = validate_roster_update(
                request.current_roster,
                updated_roster_raw,
                changes_summary,
            )

            if not is_valid:
                logger.error("Integrity check failed: %s", integrity_msg)
                return ModifyRosterResponse(
                    response_type="message",
                    content=(
                        f"I detected a potential issue with the update "
                        f"({integrity_msg}). Could you rephrase and try again?"
                    ),
                    error=integrity_msg,
                )

            # Regenerate graph_spec from validated roster
            updated_roster_dict = updated_roster_obj.model_dump()
            updated_roster_dict["graph_spec"] = build_graph_spec(updated_roster_dict)

            return ModifyRosterResponse(
                response_type="roster_update",
                content=response_data.get("content", "Roster updated successfully."),
                updated_roster=updated_roster_dict,
                changes_summary=changes_summary,
            )

        # Step 7: Conversational reply
        return ModifyRosterResponse(
            response_type="message",
            content=response_data.get("content", "I'm not sure how to help with that."),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("modify_roster error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Roster modification failed: {str(e)}",
        )


@router.get("/api/chat/architect-suggestions")
async def get_architect_suggestions(roster_json: str):
    """Return smart suggestion chips based on the current roster."""
    try:
        roster = json.loads(roster_json)
        suggestions = generate_architect_suggestions(roster)
        return {"suggestions": suggestions}
    except json.JSONDecodeError:
        return {"suggestions": [
            "➕ Add a new agent",
            "🔒 Add HITL checkpoint",
            "🛡️ Add error handling agent",
            "📡 Add monitoring agent",
        ]}
