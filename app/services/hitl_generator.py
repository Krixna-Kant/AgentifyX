"""
HITL Checkpoint Code Generator — produces LangGraph interrupt() code snippets
for agents that require human-in-the-loop approval.
"""

import ast
import re
import logging

logger = logging.getLogger(__name__)


def _snake_case(name: str) -> str:
    """Convert a name to snake_case."""
    s = re.sub(r"[^a-zA-Z0-9\s_]", "", name)
    s = re.sub(r"[\s\-]+", "_", s).strip("_").lower()
    return s or "agent"


def generate_hitl_map(roster: dict) -> dict:
    """
    Build a dict mapping agent_id → HITL details for agents with hitl_required=True.

    Returns:
        {agent_id: {agent_name, hitl_checkpoints, risk_level, code_snippet}}
    """
    agents = roster.get("agents", [])
    hitl_map: dict = {}

    for agent in agents:
        if not agent.get("hitl_required", False):
            continue

        agent_id = agent.get("agent_id", "unknown")
        agent_name = agent.get("agent_name", agent.get("role", "Agent"))
        checkpoints = agent.get("hitl_checkpoints", [])
        risk_level = _derive_risk_level(checkpoints, agent)
        snake_name = _snake_case(agent_name)

        checkpoint_reason = checkpoints[0] if checkpoints else "Human review required"

        code_snippet = f'''# ─── HITL Checkpoint: {agent_name} ───────────────────────
# Trigger: {", ".join(checkpoints) if checkpoints else "Human review required"}
# Risk Level: {risk_level}

from langgraph.types import interrupt


def {snake_name}_with_approval(state):
    """Execute {agent_name} with mandatory human approval."""
    result = {snake_name}_execute(state)

    # HUMAN CHECKPOINT — Review required before proceeding
    human_decision = interrupt({{
        "agent": "{agent_name}",
        "proposed_action": result.get("action", ""),
        "risk_level": "{risk_level}",
        "checkpoint_reason": "{checkpoint_reason}",
        "preview": result,
    }})

    if human_decision.get("approved", False):
        return {{**state, "last_action": result, "approved": True}}
    else:
        return {{
            **state,
            "rejected": True,
            "rejection_reason": human_decision.get("reason", ""),
        }}
'''

        # Validate syntax
        try:
            ast.parse(code_snippet)
        except SyntaxError as e:
            logger.warning("HITL snippet for %s has syntax error: %s", agent_name, e)

        hitl_map[agent_id] = {
            "agent_name": agent_name,
            "hitl_checkpoints": checkpoints,
            "risk_level": risk_level,
            "code_snippet": code_snippet,
        }

    return hitl_map


def _derive_risk_level(checkpoints: list[str], agent: dict) -> str:
    """Derive risk level from checkpoints and agent metadata."""
    high_keywords = [
        "approval", "financial", "clinical", "legal", "safety",
        "compliance", "security", "patient", "transaction", "firing",
        "hiring", "diagnosis", "contract",
    ]
    medium_keywords = [
        "review", "verify", "confirm", "check", "validate", "escalat",
    ]

    text = " ".join(checkpoints).lower() + " " + agent.get("role", "").lower()

    if any(kw in text for kw in high_keywords):
        return "HIGH"
    elif any(kw in text for kw in medium_keywords):
        return "MEDIUM"
    return "LOW"
