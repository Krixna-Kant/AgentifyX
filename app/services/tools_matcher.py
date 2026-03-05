"""
Tools matcher — matches agent tool requirements against the tools catalog.
Uses simple string containment + keyword matching (no fuzzy library needed).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CATALOG_PATH = Path(__file__).parent.parent / "data" / "tools_catalog.json"


def _load_catalog() -> list[dict]:
    """Load the tools catalog JSON."""
    if _CATALOG_PATH.exists():
        with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("tools", [])
    return []


def match_tools(roster: dict, framework: str = "crewai") -> dict:
    """
    For each agent, match tools_required against the catalog.

    Returns:
        {agent_id: [matched_catalog_entries_or_unmatched_notes]}
    """
    catalog = _load_catalog()
    agents = roster.get("agents", [])
    result: dict = {}

    for agent in agents:
        agent_id = agent.get("agent_id", "unknown")
        required_tools = agent.get("tools_required", [])
        matched: list[dict] = []
        matched_names: set = set()

        for tool_name in required_tools:
            tool_lower = tool_name.lower().strip()
            best_match = _find_best_match(tool_lower, catalog, framework)

            if best_match:
                if best_match["name"] not in matched_names:
                    matched.append(best_match)
                    matched_names.add(best_match["name"])
            else:
                # Unmatched tool — include with a note
                matched.append({
                    "name": tool_name,
                    "pip_install": f"# Research needed: {tool_name}",
                    "category": "unknown",
                    "purpose": "Not found in catalog — research needed",
                    "free": True,
                    "framework_compat": [],
                    "use_when": f"Required by {agent.get('agent_name', 'agent')}",
                    "docs_url": "",
                    "_unmatched": True,
                })

        result[agent_id] = matched

    return result


def _find_best_match(tool_name: str, catalog: list[dict], framework: str) -> dict | None:
    """Find the best matching catalog entry for a tool name."""
    # Exact name match
    for entry in catalog:
        if entry["name"].lower() == tool_name:
            return entry

    # Containment match (tool name contains catalog name or vice versa)
    for entry in catalog:
        cat_name = entry["name"].lower()
        if cat_name in tool_name or tool_name in cat_name:
            return entry

    # Keyword match — check if any word in tool_name matches
    tool_words = set(tool_name.replace("-", " ").replace("_", " ").split())
    for entry in catalog:
        cat_words = set(entry["name"].lower().replace("-", " ").replace("_", " ").split())
        # Match if significant overlap
        if len(tool_words & cat_words) >= 1 and len(tool_words & cat_words) / len(tool_words) > 0.4:
            return entry

    # Check purpose/use_when for keyword matches
    for entry in catalog:
        purpose_lower = (entry.get("purpose", "") + " " + entry.get("use_when", "")).lower()
        if tool_name in purpose_lower:
            return entry

    return None
