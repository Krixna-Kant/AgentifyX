"""
Simulation Script Generator — builds a step-by-step simulation from AgentRoster data.
Each step mirrors what a real agentic pipeline would do, with mock timings.
"""

import random
from datetime import datetime

MAX_SIM_STEPS = 20


def generate_simulation(roster: dict) -> list[dict]:
    """
    Build simulation steps from real roster data.
    Returns a list of step dicts with type, agent info, tools, timing, and HITL flags.
    """
    agents = roster.get("agents", [])
    if not agents:
        return []

    steps = []
    step_num = 0

    # ── Step 0: START ───────────────────────────────────────────
    doc_name = roster.get("document_name", "Document")
    steps.append({
        "step": step_num,
        "type": "start",
        "agent_name": "System",
        "action": f"Pipeline initialized — received '{doc_name}'",
        "tools": [],
        "duration_ms": random.randint(200, 500),
        "tokens_estimated": 0,
        "hitl_pause": False,
        "hitl_message": "",
        "hitl_checkpoints": [],
    })
    step_num += 1

    # ── Agent steps ─────────────────────────────────────────────
    for agent in agents:
        if step_num >= MAX_SIM_STEPS - 1:
            break

        agent_name = agent.get("agent_name", agent.get("role", "Agent"))
        tools = agent.get("tools_required", [])
        goal = agent.get("goal", "Processing...")
        hitl = agent.get("hitl_required", False)
        checkpoints = agent.get("hitl_checkpoints", [])
        inputs = agent.get("input_sources", [])
        outputs = agent.get("output_artifacts", [])

        # Input gathering step
        if inputs:
            steps.append({
                "step": step_num,
                "type": "agent_input",
                "agent_name": agent_name,
                "action": f"Gathering inputs: {', '.join(inputs)}",
                "tools": [],
                "duration_ms": random.randint(300, 800),
                "tokens_estimated": random.randint(100, 500),
                "hitl_pause": False,
                "hitl_message": "",
                "hitl_checkpoints": [],
            })
            step_num += 1
            if step_num >= MAX_SIM_STEPS - 1:
                break

        # Main execution step
        tool_str = f" using [{', '.join(tools)}]" if tools else ""
        steps.append({
            "step": step_num,
            "type": "agent_exec",
            "agent_name": agent_name,
            "action": f"Executing: {goal}{tool_str}",
            "tools": tools,
            "duration_ms": random.randint(800, 3000),
            "tokens_estimated": random.randint(500, 2500),
            "hitl_pause": False,
            "hitl_message": "",
            "hitl_checkpoints": [],
        })
        step_num += 1
        if step_num >= MAX_SIM_STEPS - 1:
            break

        # HITL step (if required)
        if hitl:
            cp_str = ", ".join(checkpoints) if checkpoints else "General review"
            steps.append({
                "step": step_num,
                "type": "hitl",
                "agent_name": agent_name,
                "action": f"⏸️ Awaiting human approval — checkpoints: {cp_str}",
                "tools": [],
                "duration_ms": 0,
                "tokens_estimated": 0,
                "hitl_pause": True,
                "hitl_message": f"{agent_name} requires human approval before proceeding.",
                "hitl_checkpoints": checkpoints,
            })
            step_num += 1
            if step_num >= MAX_SIM_STEPS - 1:
                break

        # Output step
        if outputs:
            steps.append({
                "step": step_num,
                "type": "agent_output",
                "agent_name": agent_name,
                "action": f"Producing outputs: {', '.join(outputs)}",
                "tools": [],
                "duration_ms": random.randint(200, 600),
                "tokens_estimated": random.randint(50, 300),
                "hitl_pause": False,
                "hitl_message": "",
                "hitl_checkpoints": [],
            })
            step_num += 1
            if step_num >= MAX_SIM_STEPS - 1:
                break

    # ── END step ────────────────────────────────────────────────
    total_hitl = sum(1 for s in steps if s["type"] == "hitl")
    total_auto = sum(1 for s in steps if s["type"] in ("agent_exec", "agent_input", "agent_output"))
    auto_rate = round(total_auto / max(total_auto + total_hitl, 1) * 100, 1)

    steps.append({
        "step": step_num,
        "type": "end",
        "agent_name": "System",
        "action": f"✅ Pipeline complete — {len(agents)} agents executed, "
                  f"automation rate: {auto_rate}%",
        "tools": [],
        "duration_ms": random.randint(100, 300),
        "tokens_estimated": 0,
        "hitl_pause": False,
        "hitl_message": "",
        "hitl_checkpoints": [],
        "automation_rate": auto_rate,
        "total_hitl": total_hitl,
        "total_auto": total_auto,
    })

    return steps
