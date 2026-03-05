"""
AgentRoster Pydantic schema — the master output format for AgentifyX.
All Gemini outputs are parsed into this schema.
"""

from pydantic import BaseModel, Field


class AgentDetail(BaseModel):
    agent_id: str
    agent_name: str
    role: str
    goal: str
    tools_required: list[str] = Field(default_factory=list)
    input_sources: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    hitl_required: bool = False
    hitl_checkpoints: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence_citations: list[dict] = Field(default_factory=list)  # [{"page": N, "snippet": "..."}]


class AgentRoster(BaseModel):
    document_name: str
    analysis_timestamp: str
    readiness_scores: dict = Field(
        default_factory=dict,
        description=(
            "7 readiness dimensions, each 0-100: "
            "TaskDecomposability, DecisionComplexity, ToolIntegrability, "
            "AutonomyPotential, DataAvailability, RiskLevel, ROIPotential"
        ),
    )
    composite_readiness: float = Field(ge=0.0, le=100.0, default=0.0)
    agents: list[AgentDetail] = Field(default_factory=list)
    recommended_framework: str = "CrewAI"
    transformation_summary: str = ""
    assumptions_made: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    legacy_pain_points: list[dict] = Field(
        default_factory=list,
        description=(
            'Each dict: {"pain_point": str, "severity": "high|medium|low", '
            '"agent_solution": str (agent_id that resolves it)}'
        ),
    )
    mermaid_flowchart: str = ""   # Mermaid graph TD source code
    mermaid_sequence: str = ""    # Mermaid sequenceDiagram source code
    graph_spec: dict = Field(default_factory=dict)  # vis.js compatible nodes/edges JSON
