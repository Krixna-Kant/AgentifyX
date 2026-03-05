"""
Graph Builder — derives a vis.js compatible graph spec from AgentRoster data.
No LLM calls; pure deterministic transformation.
"""

import logging

logger = logging.getLogger(__name__)

# ── Node style presets ──────────────────────────────────────────────────────
_NODE_STYLES = {
    "agent": {
        "color": {"background": "#7C3AED", "border": "#9F67FF",
                  "highlight": {"background": "#9F67FF", "border": "#C4B5FD"}},
        "shape": "box",
    },
    "tool": {
        "color": {"background": "#059669", "border": "#10B981",
                  "highlight": {"background": "#10B981", "border": "#6EE7B7"}},
        "shape": "ellipse",
    },
    "hitl": {
        "color": {"background": "#DC2626", "border": "#F87171",
                  "highlight": {"background": "#F87171", "border": "#FCA5A5"}},
        "shape": "diamond",
    },
    "input": {
        "color": {"background": "#1A56A6", "border": "#4F9FFF",
                  "highlight": {"background": "#4F9FFF", "border": "#93C5FD"}},
        "shape": "box",
    },
    "output": {
        "color": {"background": "#D97706", "border": "#FCD34D",
                  "highlight": {"background": "#FCD34D", "border": "#FDE68A"}},
        "shape": "box",
    },
}


def build_graph_spec(roster: dict) -> dict:
    """
    Build a vis.js compatible JSON with nodes and edges from an AgentRoster dict.
    Returns: {"nodes": [...], "edges": [...]}
    """
    agents = roster.get("agents", [])
    if not agents:
        return {"nodes": [], "edges": []}

    nodes = []
    edges = []
    node_ids = set()
    _id_counter = [0]

    def _make_id(prefix: str, label: str) -> str:
        """Generate a deterministic, unique node ID."""
        clean = label.lower().replace(" ", "_").replace("-", "_")[:30]
        return f"{prefix}_{clean}"

    def _add_node(node_id: str, label: str, group: str, title: str = ""):
        """Add node if not already present."""
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        style = _NODE_STYLES.get(group, _NODE_STYLES["agent"])
        node = {
            "id": node_id,
            "label": label,
            "group": group,
            "title": title or label,
            **style,
        }
        nodes.append(node)

    def _add_edge(from_id: str, to_id: str, label: str = "", dashes: bool = False):
        """Add an edge."""
        edge = {"from": from_id, "to": to_id}
        if label:
            edge["label"] = label
        if dashes:
            edge["dashes"] = True
        edges.append(edge)

    # ── Collect unique inputs, tools, outputs ───────────────────
    all_inputs = set()
    all_tools = set()
    all_outputs = set()

    for agent in agents:
        for inp in agent.get("input_sources", []):
            all_inputs.add(inp)
        for tool in agent.get("tools_required", []):
            all_tools.add(tool)
        for out in agent.get("output_artifacts", []):
            all_outputs.add(out)

    # ── Create input nodes ──────────────────────────────────────
    for inp in all_inputs:
        nid = _make_id("inp", inp)
        _add_node(nid, f"📥 {inp}", "input", f"<b>Input Source</b><br>{inp}")

    # ── Create agent nodes + HITL nodes ─────────────────────────
    for agent in agents:
        agent_id = agent.get("agent_id", f"agent_{_id_counter[0]}")
        _id_counter[0] += 1
        agent_name = agent.get("agent_name", agent.get("role", "Agent"))
        confidence = agent.get("confidence_score", 0)
        conf_pct = int(confidence * 100)

        title = (
            f"<b>{agent_name}</b><br>"
            f"<i>{agent.get('role', '')}</i><br>"
            f"Goal: {agent.get('goal', 'N/A')}<br>"
            f"Confidence: {conf_pct}%<br>"
            f"HITL: {'Yes ⚠️' if agent.get('hitl_required') else 'No ✅'}"
        )

        _add_node(agent_id, agent_name, "agent", title)

        # Input → Agent edges
        for inp in agent.get("input_sources", []):
            inp_id = _make_id("inp", inp)
            _add_edge(inp_id, agent_id)

        # Agent → Tool edges (dashed)
        for tool in agent.get("tools_required", []):
            tool_id = _make_id("tool", tool)
            _add_edge(agent_id, tool_id, dashes=True)

        # HITL checkpoint node
        if agent.get("hitl_required"):
            hitl_id = f"hitl_{agent_id}"
            checkpoints = agent.get("hitl_checkpoints", [])
            hitl_title = (
                f"<b>⏸️ Human Approval Required</b><br>"
                f"Agent: {agent_name}<br>"
                f"Checkpoints: {', '.join(checkpoints) if checkpoints else 'General review'}"
            )
            _add_node(hitl_id, "⏸️ HITL", "hitl", hitl_title)
            _add_edge(agent_id, hitl_id, "requires approval")

            # HITL → outputs
            for out in agent.get("output_artifacts", []):
                out_id = _make_id("out", out)
                _add_edge(hitl_id, out_id, "approved")
        else:
            # Agent → Output edges
            for out in agent.get("output_artifacts", []):
                out_id = _make_id("out", out)
                _add_edge(agent_id, out_id)

    # ── Create tool nodes ───────────────────────────────────────
    for tool in all_tools:
        nid = _make_id("tool", tool)
        _add_node(nid, f"🔧 {tool}", "tool", f"<b>Tool</b><br>{tool}")

    # ── Create output nodes ─────────────────────────────────────
    for out in all_outputs:
        nid = _make_id("out", out)
        _add_node(nid, f"📤 {out}", "output", f"<b>Output Artifact</b><br>{out}")

    return {"nodes": nodes, "edges": edges}
