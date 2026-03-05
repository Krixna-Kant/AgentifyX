"""
PDF Report Generator — produces a professional 10-section PDF report using ReportLab.
"""

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib import colors


PRIMARY = HexColor("#1A56A6")
DARK_BG = HexColor("#0F0F1A")
SUCCESS = HexColor("#059669")
WARNING = HexColor("#D97706")
DANGER = HexColor("#DC2626")
LIGHT_GRAY = HexColor("#F1F5F9")
MID_GRAY = HexColor("#94A3B8")


def _severity_color(severity: str):
    s = severity.upper()
    if s == "HIGH":
        return DANGER
    elif s == "MEDIUM":
        return WARNING
    return SUCCESS


def _score_interpretation(score: float) -> str:
    if score > 75:
        return "Strong"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Moderate"
    return "Challenging"


def generate_pdf_report(roster: dict, boilerplate_code: str = "") -> bytes:
    """Generate a professional PDF report from an AgentRoster dict. Returns bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", fontName="Helvetica-Bold",
                              fontSize=28, textColor=PRIMARY, alignment=TA_CENTER,
                              spaceAfter=12))
    styles.add(ParagraphStyle(name="CoverSub", fontName="Helvetica",
                              fontSize=14, textColor=MID_GRAY, alignment=TA_CENTER,
                              spaceAfter=6))
    styles.add(ParagraphStyle(name="SectionH", fontName="Helvetica-Bold",
                              fontSize=16, textColor=PRIMARY, spaceAfter=10,
                              spaceBefore=18))
    styles.add(ParagraphStyle(name="SubH", fontName="Helvetica-Bold",
                              fontSize=12, textColor=HexColor("#334155"),
                              spaceAfter=6, spaceBefore=10))
    styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10,
                              leading=14, spaceAfter=6))
    styles.add(ParagraphStyle(name="CodeBlock", fontName="Courier", fontSize=8,
                              leading=10, spaceAfter=4, textColor=HexColor("#334155")))
    styles.add(ParagraphStyle(name="ScoreBig", fontName="Helvetica-Bold",
                              fontSize=36, textColor=PRIMARY, alignment=TA_CENTER,
                              spaceAfter=6))

    elements = []
    composite = roster.get("composite_readiness", 0)
    doc_name = roster.get("document_name", "Unknown Document")
    timestamp = roster.get("analysis_timestamp", datetime.now().isoformat())

    # ── 1. COVER PAGE ───────────────────────────────────────────
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph("AgentifyX", styles["CoverTitle"]))
    elements.append(Paragraph("Transformation Report", styles["CoverTitle"]))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"System: {doc_name}", styles["CoverSub"]))
    elements.append(Paragraph(f"Generated: {timestamp[:10]}", styles["CoverSub"]))
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph(f"{composite:.0f}/100", styles["ScoreBig"]))
    elements.append(Paragraph("Agentic Readiness Score", styles["CoverSub"]))
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="60%", color=PRIMARY, thickness=2))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("AgentifyX | TECHgium 2026", styles["CoverSub"]))
    elements.append(PageBreak())

    # ── 2. EXECUTIVE SUMMARY ────────────────────────────────────
    elements.append(Paragraph("1. Executive Summary", styles["SectionH"]))
    summary = roster.get("transformation_summary", "No summary available.")
    elements.append(Paragraph(summary, styles["Body"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── 3. AGENTIC READINESS ASSESSMENT ─────────────────────────
    elements.append(Paragraph("2. Agentic Readiness Assessment", styles["SectionH"]))
    scores = roster.get("readiness_scores", {})
    dim_names = ["TaskDecomposability", "DecisionComplexity", "ToolIntegrability",
                 "AutonomyPotential", "DataAvailability", "RiskLevel", "ROIPotential"]
    dim_labels = ["Task Decomposability", "Decision Complexity", "Tool Integrability",
                  "Autonomy Potential", "Data Availability", "Risk Level (↑=safer)", "ROI Potential"]

    table_data = [["Dimension", "Score", "Interpretation"]]
    for key, label in zip(dim_names, dim_labels):
        val = scores.get(key, 0)
        table_data.append([label, f"{val}/100", _score_interpretation(val)])
    table_data.append(["COMPOSITE", f"{composite:.0f}/100", _score_interpretation(composite)])

    t = Table(table_data, colWidths=[200, 80, 120])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT_GRAY]),
        ("BACKGROUND", (0, -1), (-1, -1), HexColor("#EFF6FF")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))

    # ── 4. CURRENT STATE ANALYSIS ───────────────────────────────
    elements.append(Paragraph("3. Current State Analysis", styles["SectionH"]))
    pain_points = roster.get("legacy_pain_points", [])
    if pain_points:
        for pp in pain_points:
            sev = pp.get("severity", "medium").upper()
            elements.append(Paragraph(
                f"<b>[{sev}]</b> {pp.get('pain_point', '')}",
                styles["Body"],
            ))
    else:
        elements.append(Paragraph("No specific pain points identified.", styles["Body"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── 5. PROPOSED AGENT ARCHITECTURE ──────────────────────────
    elements.append(Paragraph("4. Proposed Agent Architecture", styles["SectionH"]))
    agents = roster.get("agents", [])
    for agent in agents:
        name = agent.get("agent_name", agent.get("role", "Agent"))
        elements.append(Paragraph(name, styles["SubH"]))
        elements.append(Paragraph(f"<b>Role:</b> {agent.get('role', 'N/A')}", styles["Body"]))
        elements.append(Paragraph(f"<b>Goal:</b> {agent.get('goal', 'N/A')}", styles["Body"]))
        tools = ", ".join(agent.get("tools_required", []))
        if tools:
            elements.append(Paragraph(f"<b>Tools:</b> {tools}", styles["Body"]))
        hitl = "Yes" if agent.get("hitl_required") else "No"
        elements.append(Paragraph(f"<b>HITL Required:</b> {hitl}", styles["Body"]))
        if agent.get("hitl_required") and agent.get("hitl_checkpoints"):
            elements.append(Paragraph(
                f"<b>Checkpoints:</b> {', '.join(agent['hitl_checkpoints'])}",
                styles["Body"],
            ))
        conf = agent.get("confidence_score", 0)
        elements.append(Paragraph(f"<b>Confidence:</b> {int(conf*100)}%", styles["Body"]))
        citations = agent.get("evidence_citations", [])
        if citations:
            for c in citations:
                elements.append(Paragraph(
                    f"  <i>Source: Page {c.get('page', '?')}: {c.get('snippet', '')}</i>",
                    styles["Body"],
                ))
        elements.append(Spacer(1, 0.3*cm))

    # ── 6. HITL REQUIREMENTS ────────────────────────────────────
    elements.append(Paragraph("5. HITL Requirements", styles["SectionH"]))
    hitl_agents = [a for a in agents if a.get("hitl_required")]
    if hitl_agents:
        ht_data = [["Agent", "Checkpoint Triggers", "Risk Level"]]
        for a in hitl_agents:
            triggers = ", ".join(a.get("hitl_checkpoints", [])) or "General review"
            ht_data.append([a.get("agent_name", ""), triggers, "Review Required"])
        ht = Table(ht_data, colWidths=[130, 200, 100])
        ht.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(ht)
    else:
        elements.append(Paragraph("No agents require human-in-the-loop approval.", styles["Body"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── 7. FRAMEWORK RECOMMENDATION ─────────────────────────────
    elements.append(Paragraph("6. Framework Recommendation", styles["SectionH"]))
    fw = roster.get("recommended_framework", "N/A")
    elements.append(Paragraph(f"Recommended framework: <b>{fw}</b>", styles["Body"]))
    elements.append(Paragraph(summary, styles["Body"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── 8. TOOLS RECOMMENDATION ─────────────────────────────────
    elements.append(Paragraph("7. Tools Recommendation", styles["SectionH"]))
    for agent in agents:
        tools = agent.get("tools_required", [])
        if tools:
            agent_name = agent.get("agent_name", "Agent")
            elements.append(Paragraph(f"<b>{agent_name}:</b> {', '.join(tools)}", styles["Body"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── 9. ASSUMPTIONS & DATA GAPS ──────────────────────────────
    elements.append(Paragraph("8. Assumptions & Data Gaps", styles["SectionH"]))
    assumptions = roster.get("assumptions_made", [])
    gaps = roster.get("data_gaps", [])
    if assumptions:
        elements.append(Paragraph("<b>Assumptions Made:</b>", styles["Body"]))
        for a in assumptions:
            elements.append(Paragraph(f"  • {a}", styles["Body"]))
    if gaps:
        elements.append(Paragraph("<b>Data Gaps Identified:</b>", styles["Body"]))
        for g in gaps:
            elements.append(Paragraph(f"  • {g}", styles["Body"]))
    if not assumptions and not gaps:
        elements.append(Paragraph("None identified.", styles["Body"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── 10. APPENDIX: GENERATED CODE ────────────────────────────
    if boilerplate_code:
        elements.append(PageBreak())
        elements.append(Paragraph("Appendix: Generated Code", styles["SectionH"]))
        elements.append(Paragraph(
            "<i>Generated by AgentifyX — review before production use</i>",
            styles["Body"],
        ))
        # Split code into lines and wrap in Code style
        for line in boilerplate_code.split("\n"):
            safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(safe_line or " ", styles["CodeBlock"]))

    # Build
    doc.build(elements)
    return buf.getvalue()
