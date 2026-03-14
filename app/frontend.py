import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import requests
import json
import base64
import plotly.graph_objects as go

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="AgentifyX Dashboard", layout="wide", page_icon="🚀")

# ═════════════════════════════════════════════════════════════════════════════
#  Dark Theme CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    :root {
        --bg-deep: #0F0F1A; --bg-card: #1E1E2E; --bg-input: #252535;
        --accent: #1A56A6; --accent2: #7C3AED;
        --success: #059669; --warning: #D97706; --danger: #DC2626;
        --text-main: #E2E8F0; --text-muted: #94A3B8;
    }
    .stApp { background-color: #0F0F1A; }
    .stSidebar { background-color: #1E1E2E; border-right: 1px solid #333355; }
    .stButton > button {
        background: linear-gradient(135deg, #1A56A6, #7C3AED);
        color: white; border: none; border-radius: 8px;
        padding: 0.5rem 1.2rem; font-weight: 600; transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #252535; color: #E2E8F0;
        border: 1px solid #333355; border-radius: 6px;
    }
    .stExpander { background-color: #1E1E2E; border: 1px solid #333355; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1E1E2E; }
    .stTabs [data-baseweb="tab"] { color: #94A3B8; }
    .stTabs [aria-selected="true"] { color: #4F9FFF; border-bottom: 2px solid #4F9FFF; }
    div[data-testid="metric-container"] {
        background-color: #1E1E2E; border: 1px solid #333355;
        border-radius: 8px; padding: 1rem;
    }
    .agent-header {
        background: linear-gradient(135deg, #1A56A6, #7C3AED);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 1.3rem; font-weight: 700; margin-bottom: 0.3rem;
    }
    .role-pill { background: #252535; color: #94A3B8; padding: 2px 10px;
        border-radius: 12px; font-size: 0.75rem; border: 1px solid #333355; }
    .tool-chip { background: #1A56A6; color: white; padding: 2px 10px;
        border-radius: 12px; font-size: 0.8rem; margin: 2px; display: inline-block; }
    .hitl-badge-danger { background: #DC2626; color: white; padding: 6px 12px;
        border-radius: 6px; font-weight: bold; display: inline-block; margin: 4px 0; }
    .hitl-badge-safe { background: #059669; color: white; padding: 6px 12px;
        border-radius: 6px; font-weight: bold; display: inline-block; margin: 4px 0; }
    .io-flow { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 6px 0; }
    .io-item { background: #252535; padding: 4px 8px; border-radius: 4px;
        color: #E2E8F0; font-size: 0.85rem; }
    .io-arrow { color: #4F9FFF; font-weight: bold; }
    .sidebar-brand { text-align: center; padding: 1rem 0 0.5rem 0; }
    .sidebar-brand h1 { background: linear-gradient(135deg, #4F9FFF, #7C3AED);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2rem; margin-bottom: 0; }
    .sidebar-tagline { color: #94A3B8; font-size: 0.85rem; text-align: center; }
    .sidebar-version { color: #4F9FFF; font-size: 0.75rem; text-align: center; margin-top: 4px; }
    .placeholder-tab { text-align: center; padding: 4rem 2rem; color: #94A3B8; font-size: 1.1rem; }
    .placeholder-tab .emoji { font-size: 3rem; margin-bottom: 1rem; }
    .interp-bar { padding: 10px 16px; border-radius: 8px; margin-top: 10px;
        font-size: 0.95rem; font-weight: 500; text-align: center; }
    .industry-card { background: #1E1E2E; border-radius: 8px; padding: 12px;
        border: 1px solid #333355; cursor: pointer; transition: border-color 0.2s; min-height: 90px; }
    .industry-card:hover { border-color: #4F9FFF; }
    .industry-card .icon { font-size: 1.5rem; }
    .industry-card .name { color: #E2E8F0; font-weight: 600; font-size: 0.9rem; }
    .industry-card .desc { color: #94A3B8; font-size: 0.75rem; margin-top: 2px;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .industry-selected { background: #1A56A6; color: white; padding: 8px 16px;
        border-radius: 8px; font-weight: 600; margin: 8px 0; display: inline-block; }
    .fw-table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    .fw-table th { background: #252535; color: #E2E8F0; padding: 10px 12px;
        text-align: left; border-bottom: 2px solid #333355; font-size: 0.85rem; }
    .fw-table td { padding: 10px 12px; border-bottom: 1px solid #333355;
        color: #94A3B8; font-size: 0.85rem; }
    .fw-table tr.recommended { background: rgba(26, 86, 166, 0.15); }
    .fw-table tr.recommended td { color: #E2E8F0; font-weight: 500; }
    .hitl-table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    .hitl-table th { background: #252535; color: #E2E8F0; padding: 8px 12px;
        text-align: left; border-bottom: 2px solid #333355; font-size: 0.85rem; }
    .hitl-table td { padding: 8px 12px; border-bottom: 1px solid #333355;
        color: #E2E8F0; font-size: 0.85rem; }
    .hitl-table tr.risk-high { background: rgba(220, 38, 38, 0.12); }
    .hitl-table tr.risk-medium { background: rgba(217, 119, 6, 0.12); }
    .hitl-table tr.risk-low { background: rgba(5, 150, 105, 0.12); }
    .tool-card { background: #1E1E2E; border: 1px solid #333355; border-radius: 8px;
        padding: 10px 14px; margin: 4px 0; }
    .tool-card .tool-name { color: #4F9FFF; font-weight: 600; font-size: 0.95rem; }
    .tool-card .tool-purpose { color: #94A3B8; font-size: 0.8rem; margin-top: 2px; }
    .cat-badge { background: #252535; color: #94A3B8; padding: 1px 8px; border-radius: 10px;
        font-size: 0.7rem; border: 1px solid #333355; display: inline-block; margin-left: 6px; }
    .pain-legacy { background: #2D1515; border-left: 4px solid #DC2626;
        padding: 10px 14px; border-radius: 6px; margin: 6px 0; }
    .pain-solution { background: #0D2D1F; border-left: 4px solid #059669;
        padding: 10px 14px; border-radius: 6px; margin: 6px 0; }
    .session-card { background: #252535; border: 1px solid #333355; border-radius: 6px;
        padding: 8px 10px; margin: 4px 0; }
    .session-card .doc-name { color: #E2E8F0; font-weight: 600; font-size: 0.85rem; }
    .session-card .doc-meta { color: #94A3B8; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  Sidebar
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand"><h1>🚀 AgentifyX</h1></div>
    <p class="sidebar-tagline">Transforming Conventional Solutions<br>into Agentic AI Frameworks</p>
    <p class="sidebar-version">v2.0 — TECHgium Edition</p>
    <hr style="border-color:#333355">
    """, unsafe_allow_html=True)
    st.caption("Upload a PDF → analyze → explore agent recommendations")

    # Demo Mode Button
    st.markdown("---")
    if st.button("🎯 Load Demo", type="primary", use_container_width=True, key="load_demo_btn"):
        import os
        demo_path = os.path.join(os.path.dirname(__file__), "demo", "demo_roster.json")
        if os.path.exists(demo_path):
            with open(demo_path, "r", encoding="utf-8") as f:
                demo = json.load(f)
            st.session_state["roster"] = demo
            st.session_state["demo_mode"] = True
            st.session_state["uploaded_filename"] = demo.get("document_name", "Demo")
            st.session_state["session_id"] = "demo"
            st.session_state["chat_history"] = []
            st.session_state["pipeline_metrics"] = {
                "chunks_stored": 47, "pages_parsed": 32, "image_descriptions": 3}
            st.rerun()
        else:
            st.error("Demo file not found.")
    st.caption("Load a sample customer support system for judges")

    # Health Check Indicator
    st.markdown("---")
    try:
        hc = requests.get(f"{API_BASE}/api/health", timeout=5)
        if hc.status_code == 200:
            hd = hc.json()
            status = hd.get("status", "unknown")
            icon = "🟢" if status == "ok" else "🟡"
            st.markdown(f"{icon} API Status: **{status.upper()}** (v{hd.get('version','?')})")
            svcs = hd.get("services", {})
            svc_line = " · ".join(
                f"{'✅' if v else '❌'} {k.replace('_',' ').title()}" for k, v in svcs.items())
            st.caption(svc_line)
            # LLM Provider indicator
            provider = hd.get("llm_provider", "gemini")
            if provider == "groq":
                st.markdown("🤖 LLM: **Groq (Llama 3.3 70B)**")
            else:
                st.markdown("🤖 LLM: **Gemini 1.5 Flash**")
        else:
            st.markdown("🔴 API Status: **OFFLINE**")
    except Exception:
        st.markdown("🔴 API Status: **OFFLINE**")
        st.caption("Run: `uvicorn app.main:app --reload`")

    # Previous Sessions
    st.markdown("---")
    st.write("#### 📂 Previous Sessions")
    try:
        sr = requests.get(f"{API_BASE}/api/v1/sessions?limit=5", timeout=3)
        if sr.status_code == 200:
            sl = sr.json()
            if sl:
                for sess in sl:
                    dn = sess.get("document_name", "Unknown")
                    disp = dn[:25] + "..." if len(dn) > 25 else dn
                    rd = sess.get("composite_readiness", 0)
                    cr = sess.get("created_at", "")[:10]
                    st.markdown(f'<div class="session-card"><div class="doc-name">📄 {disp}</div>'
                        f'<div class="doc-meta">{cr} · Readiness: {rd:.0f}/100</div></div>', unsafe_allow_html=True)
                    if st.button("Load →", key=f"load_{sess['id']}", use_container_width=True):
                        try:
                            full = requests.get(f"{API_BASE}/api/v1/sessions/{sess['id']}", timeout=5).json()
                            if full.get("roster_json"):
                                st.session_state["roster"] = full["roster_json"]
                                st.session_state["session_id"] = sess["id"]
                                st.session_state["uploaded_filename"] = full.get("document_name", "")
                                st.session_state["chat_history"] = full.get("chat_history", [])
                                st.session_state.pop("demo_mode", None)
                                st.success(f"Session loaded: {dn}")
                                st.rerun()
                        except Exception:
                            st.error("Failed to load session.")
            else:
                st.caption("No sessions yet.")
        else:
            st.caption("Sessions unavailable.")
    except Exception:
        st.caption("API not connected.")


# ═════════════════════════════════════════════════════════════════════════════
#  Cached loaders
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def load_industry_templates():
    try:
        resp = requests.get(f"{API_BASE}/api/v1/industry-templates", timeout=5)
        if resp.status_code == 200:
            return resp.json().get("templates", [])
    except Exception:
        pass
    import os
    lp = os.path.join(os.path.dirname(__file__), "data", "industry_templates.json")
    if os.path.exists(lp):
        with open(lp, "r", encoding="utf-8") as f:
            return json.load(f).get("templates", [])
    return []


# ═════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════
def render_agent_card(agent: dict):
    name = agent.get("agent_name", agent.get("role", "Unknown Agent"))
    role = agent.get("role", "N/A")
    confidence = agent.get("confidence_score", 0)
    conf_pct = int(confidence * 100)
    with st.expander(f"🔹 {name} — {conf_pct}% confidence", expanded=True):
        st.markdown(f'<div class="agent-header">{name}</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="role-pill">{role}</span>', unsafe_allow_html=True)
        st.write(f"**Goal:** {agent.get('goal', 'N/A')}")
        tools = agent.get("tools_required", [])
        if tools:
            chips = " ".join(f'<span class="tool-chip">{t}</span>' for t in tools)
            st.markdown(f"**Tools:** {chips}", unsafe_allow_html=True)
        inputs, outputs = agent.get("input_sources", []), agent.get("output_artifacts", [])
        if inputs or outputs:
            flow = [f'<span class="io-item">{i}</span>' for i in inputs]
            if inputs and outputs: flow.append('<span class="io-arrow">→</span>')
            flow += [f'<span class="io-item">{o}</span>' for o in outputs]
            st.markdown(f'<div class="io-flow">{"".join(flow)}</div>', unsafe_allow_html=True)
        if agent.get("hitl_required"):
            st.markdown('<div class="hitl-badge-danger">⚠️ HUMAN APPROVAL REQUIRED</div>', unsafe_allow_html=True)
            cps = agent.get("hitl_checkpoints", [])
            if cps: st.caption(f"Checkpoints: {', '.join(cps)}")
        else:
            st.markdown('<div class="hitl-badge-safe">🤖 AUTONOMOUS</div>', unsafe_allow_html=True)
        st.progress(confidence)
        color = "#059669" if conf_pct > 70 else "#D97706" if conf_pct >= 40 else "#DC2626"
        st.markdown(f'<span style="color:{color};font-weight:600">Confidence: {conf_pct}%</span>', unsafe_allow_html=True)
        citations = agent.get("evidence_citations", [])
        if citations:
            cit_html = "".join(
                f'<div style="color:#94A3B8;font-size:0.8rem;margin:3px 0">'
                f'📌 Page {c.get("page","?")}: <i>{c.get("snippet","")}</i></div>'
                for c in citations
            )
            st.markdown(
                f'<details style="margin-top:6px"><summary style="color:#4F9FFF;'
                f'cursor:pointer;font-size:0.85rem">📄 Evidence Citations ({len(citations)})</summary>'
                f'<div style="padding:6px 0">{cit_html}</div></details>',
                unsafe_allow_html=True,
            )


DIM_KEYS = ["TaskDecomposability", "DecisionComplexity", "ToolIntegrability",
            "AutonomyPotential", "DataAvailability", "RiskLevel", "ROIPotential"]
DIM_LABELS = ["Task\nDecomposability", "Decision\nComplexity", "Tool\nIntegrability",
              "Autonomy\nPotential", "Data\nAvailability", "Risk Level\n(↑=safer)", "ROI\nPotential"]

def render_radar_chart(scores: dict, composite: float):
    vals = [scores.get(k, 0) for k in DIM_KEYS]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals, theta=DIM_LABELS, fill='toself',
        fillcolor='rgba(26, 86, 166, 0.25)', line=dict(color='#4F9FFF', width=2), name='Readiness'))
    fig.update_layout(
        polar=dict(bgcolor='#1E1E2E',
            radialaxis=dict(visible=True, range=[0,100], gridcolor='#333355',
                tickcolor='#94A3B8', tickfont=dict(color='#94A3B8', size=10)),
            angularaxis=dict(gridcolor='#333355', tickfont=dict(color='#E2E8F0', size=11))),
        paper_bgcolor='#0F0F1A', plot_bgcolor='#0F0F1A',
        font=dict(color='#E2E8F0'), showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40), height=400)
    st.plotly_chart(fig, use_container_width=True)
    if composite > 75: i, bg, bd = "✅ Strong candidate", "rgba(5,150,105,0.15)", "#059669"
    elif composite >= 60: i, bg, bd = "🟡 Good candidate — moderate redesign", "rgba(217,119,6,0.15)", "#D97706"
    elif composite >= 40: i, bg, bd = "🟠 Possible — significant effort", "rgba(217,119,6,0.15)", "#D97706"
    else: i, bg, bd = "🔴 Challenging — pilot first", "rgba(220,38,38,0.15)", "#DC2626"
    st.markdown(f'<div class="interp-bar" style="background:{bg};border:1px solid {bd}">{i}</div>', unsafe_allow_html=True)


def render_mermaid_url(diagram_code: str) -> str:
    """Convert Mermaid source to a mermaid.ink PNG URL."""
    encoded = base64.urlsafe_b64encode(diagram_code.encode("utf-8")).decode("ascii")
    return f"https://mermaid.ink/img/{encoded}?type=png"


def demo_banner():
    """Show demo mode banner if active."""
    if st.session_state.get("demo_mode"):
        st.markdown(
            '<div style="background:rgba(79,159,255,0.12);border:1px solid #4F9FFF;'
            'border-radius:8px;padding:8px 14px;color:#93C5FD;font-weight:500;'
            'text-align:center;margin-bottom:8px">'
            '🎯 Demo Mode — Sample customer support system</div>',
            unsafe_allow_html=True,
        )


EMPTY_STATE = "📤 Upload a document or click **🎯 Load Demo** in the sidebar to get started."


# ═════════════════════════════════════════════════════════════════════════════
#  Main — Tab Structure
# ═════════════════════════════════════════════════════════════════════════════
st.title("🚀 AgentifyX")
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Analyze", "📊 Results", "🗺️ Architecture", "🔧 Generate",
    "💬 Chat", "▶️ Simulate", "📥 Export",
])

# ── Tab 1: Analyze ──────────────────────────────────────────────────────────
with tab1:
    st.subheader("Upload & Analyze")
    st.write("#### 🏭 Select Industry Context")
    st.caption("Choose an industry for domain-specific recommendations, or skip for general analysis.")
    templates = load_industry_templates()
    all_options = [{"id": "general", "name": "General / Other", "icon": "🔄",
                    "description": "No specific industry — general analysis",
                    "color": "#4F9FFF", "domain_context": ""}] + templates
    rows = [all_options[i:i+4] for i in range(0, len(all_options), 4)]
    for row in rows:
        cols = st.columns(4)
        for col, tmpl in zip(cols, row):
            with col:
                st.markdown(
                    f'<div class="industry-card" style="border-left:4px solid {tmpl.get("color","#333355")}">'
                    f'<div class="icon">{tmpl["icon"]}</div><div class="name">{tmpl["name"]}</div>'
                    f'<div class="desc">{tmpl.get("description","")}</div></div>', unsafe_allow_html=True)
                if st.button("Select", key=f"ind_{tmpl['id']}", use_container_width=True):
                    st.session_state["selected_industry"] = tmpl
    sel = st.session_state.get("selected_industry")
    if sel and sel["id"] != "general":
        st.markdown(f'<div class="industry-selected">{sel["icon"]} Selected: {sel["name"]}</div>', unsafe_allow_html=True)
        st.caption(f"HITL: {sel.get('hitl_requirement','N/A')} | Compliance: {', '.join(sel.get('compliance_flags',[]))}")
    elif not sel:
        st.info("💡 Select an industry for more targeted recommendations, or proceed without one.")
    st.divider()

    uploaded_file = st.file_uploader("Upload Legacy System Documentation (PDF)", type="pdf")

    # GitHub input
    with st.expander("🔗 GitHub Repository (Optional)"):
        st.caption("Provide a GitHub repo URL to analyze its Python code structure. "
                   "Functions with high branching complexity (>8 branches) are flagged as agent candidates.")
        github_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/owner/repo", key="github_url_input")
        is_private = st.checkbox("Private repository (requires PAT)", key="github_private")
        github_pat = ""
        if is_private:
            github_pat = st.text_input("Personal Access Token", type="password",
                placeholder="ghp_...", key="github_pat_input")
            st.caption("Create a PAT at: https://github.com/settings/tokens/new (select 'repo' scope)")

    can_analyze = uploaded_file is not None or github_url
    if can_analyze:
        if st.button("⚡ Analyze & Transform Architecture", type="primary"):
            progress_bar = st.progress(0)
            status_container = st.status("🔄 Processing...", expanded=True)
            steps = []
            if github_url:
                steps.append(("🔗 GitHub Analysis", "Fetching and analyzing Python files from repository..."))
            if uploaded_file:
                steps.extend([
                    ("📄 Parsing PDF", "Extracting text, tables, and detecting images..."),
                    ("✂️ Chunking & NER", "Splitting into semantic chunks and extracting entities..."),
                    ("🧠 Embedding", "Generating vector embeddings and storing in ChromaDB..."),
                ])
            steps.append(("🤖 Reasoning", "Gemini is analyzing and building the agentic blueprint..."))
            for label, desc in steps:
                status_container.write(f"**{label}**: {desc}")
            industry_id = st.session_state.get("selected_industry", {}).get("id")
            files = {}
            if uploaded_file:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            form_data = {}
            if industry_id: form_data["industry_id"] = industry_id
            if github_url: form_data["github_url"] = github_url
            if github_pat: form_data["github_pat"] = github_pat
            try:
                response = requests.post(f"{API_BASE}/api/v1/process-document",
                    files=files if files else None, data=form_data, timeout=300)
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API."); st.stop()
            except requests.exceptions.Timeout:
                st.error("⏳ Request timed out."); st.stop()
            if response.status_code == 200:
                data = response.json()
                analysis = data.get("agentifyx_analysis", {})
                if isinstance(analysis, str):
                    clean = analysis.replace("```json","").replace("```","").strip()
                    try: analysis = json.loads(clean)
                    except json.JSONDecodeError:
                        st.error("Failed to parse AI output."); st.code(analysis); st.stop()
                # Check if analysis shows a rate limit failure
                summary = analysis.get("transformation_summary", "") if isinstance(analysis, dict) else ""
                if "429" in summary or "rate limit" in summary.lower() or "quota" in summary.lower():
                    st.warning(
                        "⏳ **Gemini API rate limit reached.** This is a free tier restriction.\n\n"
                        "Please wait 60 seconds and try again, or use the "
                        "**🎯 Load Demo** button in the sidebar to explore features without API calls."
                    )
                    st.session_state["roster"] = analysis
                    st.session_state["pipeline_metrics"] = data.get("pipeline_metrics", {})
                    st.session_state["uploaded_filename"] = data.get("filename", "")
                    st.session_state["session_id"] = data.get("job_id", "")
                else:
                    st.session_state["roster"] = analysis
                    st.session_state["pipeline_metrics"] = data.get("pipeline_metrics", {})
                    st.session_state["uploaded_filename"] = data.get("filename", "")
                    st.session_state["session_id"] = data.get("job_id", "")
                    st.session_state["chat_history"] = []
                    if data.get("github_analysis"):
                        st.session_state["github_analysis"] = data["github_analysis"]
                        st.session_state["github_repo"] = data.get("github_repo", "")
                    if data.get("github_warning"):
                        st.warning(data["github_warning"])
                    progress_bar.progress(100)
                    status_container.update(label="✅ Analysis Complete!", state="complete")
                    st.success("🎉 Analysis complete! Switch to the **📊 Results** tab.")
            elif response.status_code in (400, 422):
                detail = response.json().get("detail", "Error.")
                if "429" in detail or "rate limit" in detail.lower() or "quota" in detail.lower():
                    st.warning(
                        "⏳ **Gemini API rate limit reached.** This is a free tier restriction.\n\n"
                        "Please wait 60 seconds and try again, or use the "
                        "**🎯 Load Demo** button in the sidebar to explore features without API calls."
                    )
                else:
                    st.error(f"⚠️ {detail}")
            else:
                try: detail = response.json().get("detail", "Unknown error.")
                except Exception: detail = response.text
                st.error(f"❌ Server error ({response.status_code}): {detail}")
    if "roster" not in st.session_state:
        st.info("👆 Upload a PDF and/or provide a GitHub URL, then click Analyze.")

# ── Tab 2: Results ──────────────────────────────────────────────────────────
with tab2:
    if "roster" not in st.session_state:
        st.info("📋 Run an analysis first from the **🏠 Analyze** tab.")
    else:
        roster = st.session_state["roster"]
        metrics = st.session_state.get("pipeline_metrics", {})
        st.subheader("Analysis Results")
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        composite = roster.get("composite_readiness", 0)
        with c1: st.metric("🎯 Composite Readiness", f"{composite:.0f}/100")
        with c2: st.metric("📦 Chunks Stored", metrics.get("chunks_stored", 0))
        with c3: st.metric("📄 Pages Parsed", metrics.get("pages_parsed", 0))
        with c4: st.metric("🖼️ Images Described", metrics.get("image_descriptions", 0))
        st.divider()
        st.write("### 📊 Readiness Dimension Scores")
        render_radar_chart(roster.get("readiness_scores", {}), composite)
        st.divider()
        agents = roster.get("agents", [])
        if agents:
            st.write(f"### 🤖 Proposed Agentic Architecture ({len(agents)} agents)")
            for a in agents: render_agent_card(a)
        st.divider()
        st.write("### 📝 Transformation Summary")
        st.info(roster.get("transformation_summary", "No summary available."))
        fw = roster.get("recommended_framework", "")
        if fw: st.write(f"### 🏗️ Recommended Framework: **{fw}**")

        # Before / After
        pain_points = roster.get("legacy_pain_points", [])
        st.divider()
        st.write("### 🔄 Transformation: Before vs After")
        if pain_points:
            col_b, col_a = st.columns(2)
            agent_map = {a.get("agent_id", ""): a for a in agents}
            with col_b:
                st.write("#### ❌ Current State (Legacy)")
                for pp in pain_points:
                    sev = pp.get("severity", "medium").upper()
                    clr = "#DC2626" if sev == "HIGH" else "#D97706" if sev == "MEDIUM" else "#059669"
                    st.markdown(f'<div class="pain-legacy"><b style="color:{clr}">{sev} RISK</b><br>'
                        f'<span style="color:#E2E8F0">{pp.get("pain_point","")}</span></div>', unsafe_allow_html=True)
            with col_a:
                st.write("#### ✅ Future State (Agentic)")
                for pp in pain_points:
                    aid = pp.get("agent_solution", "")
                    ag = agent_map.get(aid, {})
                    aname = ag.get("agent_name", ag.get("role", aid))
                    st.markdown(f'<div class="pain-solution"><b style="color:#059669">RESOLVED BY: {aname}</b><br>'
                        f'<span style="color:#E2E8F0">{ag.get("goal","Automated resolution")}</span></div>', unsafe_allow_html=True)
            st.divider()
            s1, s2, s3 = st.columns(3)
            with s1: st.metric("🔧 Manual Steps Automated", sum(1 for p in pain_points if p.get("agent_solution") in agent_map))
            with s2: st.metric("👤 HITL Checkpoints", sum(1 for a in agents if a.get("hitl_required")))
            with s3: st.metric("✨ New Capabilities", len(agents))
        else:
            st.info("📄 Upload a document with workflow descriptions for before/after analysis.")

        assumptions, gaps = roster.get("assumptions_made", []), roster.get("data_gaps", [])
        if assumptions or gaps:
            st.divider()
            ca, cb = st.columns(2)
            with ca:
                st.write("### ⚠️ Assumptions Made")
                for a in assumptions: st.write(f"- {a}")
                if not assumptions: st.write("_None_")
            with cb:
                st.write("### 🔍 Data Gaps")
                for g in gaps: st.write(f"- {g}")
                if not gaps: st.write("_None_")

        # GitHub Analysis Results
        gh = st.session_state.get("github_analysis")
        if gh:
            st.divider()
            st.write("### 🔗 GitHub Code Analysis")
            repo_name = st.session_state.get("github_repo", "")
            if repo_name:
                st.caption(f"Repository: **{repo_name}**")
            g1, g2, g3 = st.columns(3)
            with g1: st.metric("📂 Files Analyzed", gh.get("total_files_analyzed", 0))
            with g2: st.metric("🎯 Agent Candidates", len(gh.get("agent_candidate_functions", [])))
            with g3: st.metric("🌐 APIs Detected", len(gh.get("detected_api_endpoints", [])))

            candidates = gh.get("agent_candidate_functions", [])
            if candidates:
                st.write("#### 🎯 Agent Candidate Functions")
                st.caption("Functions with high branching complexity (>8 branches) — strong candidates for agent decomposition")
                for c in candidates:
                    st.markdown(
                        f'<div class="tool-card">'
                        f'<span class="tool-name">{c["file"]}::{c["function"]}()</span>'
                        f'<div class="tool-purpose">{c["reason"]}</div></div>',
                        unsafe_allow_html=True,
                    )

            frameworks = gh.get("primary_frameworks", [])
            if frameworks:
                st.write("#### 📦 Primary Frameworks Detected")
                chips = " ".join(f'<span class="tool-chip">{f}</span>' for f in frameworks)
                st.markdown(chips, unsafe_allow_html=True)

            endpoints = gh.get("detected_api_endpoints", [])
            if endpoints:
                with st.expander("🌐 Detected API Endpoints"):
                    for ep in endpoints:
                        st.code(ep)

# ── Tab 3: Architecture Diagrams ────────────────────────────────────────────
with tab3:
    if "roster" not in st.session_state:
        st.info("📋 Run an analysis first from the **🏠 Analyze** tab.")
    else:
        roster = st.session_state["roster"]
        graph_spec = roster.get("graph_spec", {})
        flowchart = roster.get("mermaid_flowchart", "")
        sequence = roster.get("mermaid_sequence", "")

        st.subheader("🗺️ Architecture Diagrams")

        # ── vis.js Interactive Graph ────────────────────────────
        if graph_spec and graph_spec.get("nodes"):
            st.write("### 🕸️ Interactive Agent Graph")

            import streamlit.components.v1 as components

            graph_json = json.dumps(graph_spec)
            vis_html = f"""
<!DOCTYPE html>
<html>
<head>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin: 0; padding: 0; background: transparent; font-family: Arial, sans-serif; }}
  #graph-container {{
    background: #1E1E2E; border: 1px solid #333355;
    border-radius: 12px; width: 100%; height: 500px;
  }}
  #node-detail {{
    color: #E2E8F0; padding: 10px 14px;
    background: #252535; border-radius: 8px;
    margin-top: 8px; min-height: 40px;
    font-size: 13px; border: 1px solid #333355;
  }}
  #legend {{
    display: flex; gap: 16px; padding: 8px 0; flex-wrap: wrap;
    justify-content: center; margin-top: 6px;
  }}
  .legend-item {{
    display: flex; align-items: center; gap: 5px;
    color: #94A3B8; font-size: 12px;
  }}
  .legend-dot {{
    width: 12px; height: 12px; border-radius: 3px; display: inline-block;
  }}
</style>
</head>
<body>
<div id="graph-container"></div>
<div id="node-detail">Click any node to see details</div>
<div id="legend">
  <span class="legend-item"><span class="legend-dot" style="background:#7C3AED"></span> Agent</span>
  <span class="legend-item"><span class="legend-dot" style="background:#059669;border-radius:50%"></span> Tool</span>
  <span class="legend-item"><span class="legend-dot" style="background:#DC2626;transform:rotate(45deg)"></span> HITL</span>
  <span class="legend-item"><span class="legend-dot" style="background:#1A56A6"></span> Input</span>
  <span class="legend-item"><span class="legend-dot" style="background:#D97706"></span> Output</span>
</div>
<script>
  const graphData = {graph_json};
  const nodes = new vis.DataSet(graphData.nodes);
  const edges = new vis.DataSet(graphData.edges);
  const container = document.getElementById("graph-container");
  const data = {{ nodes: nodes, edges: edges }};
  const options = {{
    nodes: {{
      font: {{ color: "#E2E8F0", size: 13, face: "Arial" }},
      borderWidth: 2,
      shadow: {{ enabled: true, color: "rgba(0,0,0,0.3)", size: 6 }}
    }},
    edges: {{
      color: {{ color: "#4F9FFF", opacity: 0.7, highlight: "#93C5FD" }},
      arrows: {{ to: {{ enabled: true, scaleFactor: 0.8 }} }},
      font: {{ color: "#94A3B8", size: 10, face: "Arial", strokeWidth: 0 }},
      smooth: {{ type: "cubicBezier", forceDirection: "horizontal" }}
    }},
    physics: {{
      enabled: true,
      barnesHut: {{
        gravitationalConstant: -3000,
        centralGravity: 0.3,
        springLength: 120,
        springConstant: 0.04
      }},
      stabilization: {{ iterations: 200 }}
    }},
    interaction: {{
      hover: true,
      tooltipDelay: 200,
      navigationButtons: true,
      keyboard: true
    }},
    layout: {{ randomSeed: 42 }}
  }};
  const network = new vis.Network(container, data, options);
  network.on("click", function(params) {{
    if (params.nodes.length > 0) {{
      const nodeId = params.nodes[0];
      const node = nodes.get(nodeId);
      document.getElementById("node-detail").innerHTML =
        "<b style='color:#4F9FFF'>" + node.label + "</b><br>" +
        (node.title || "");
    }} else {{
      document.getElementById("node-detail").innerHTML = "Click any node to see details";
    }}
  }});
</script>
</body>
</html>
"""
            components.html(vis_html, height=650, scrolling=False)

            st.caption("💡 Drag nodes to rearrange • Scroll to zoom • Click for details")

            if st.button("🔄 Reset Layout", key="reset_graph"):
                st.rerun()

        elif not graph_spec or not graph_spec.get("nodes"):
            st.info("🕸️ Re-analyze a document to see the interactive agent graph.")

        st.divider()

        # ── Mermaid Diagrams ────────────────────────────────────
        if flowchart:
            st.write("### 🔄 Agent Workflow (Mermaid)")
            try:
                url = render_mermaid_url(flowchart)
                st.image(url, use_container_width=True)
            except Exception:
                st.warning("🔧 Offline — paste at [mermaid.live](https://mermaid.live)")
                st.code(flowchart, language="markdown")
            with st.expander("📝 View Mermaid Source"):
                st.code(flowchart, language="markdown")
            st.download_button("📐 Download Flowchart (.mmd)", data=flowchart,
                file_name="agent_workflow.mmd", mime="text/plain", key="dl_flow_tab3")

        if sequence:
            st.divider()
            st.write("### 💬 Agent Communication Sequence (Mermaid)")
            try:
                url = render_mermaid_url(sequence)
                st.image(url, use_container_width=True)
            except Exception:
                st.warning("🔧 Offline — paste at [mermaid.live](https://mermaid.live)")
                st.code(sequence, language="markdown")
            with st.expander("📝 View Mermaid Source"):
                st.code(sequence, language="markdown")
            st.download_button("📐 Download Sequence (.mmd)", data=sequence,
                file_name="agent_sequence.mmd", mime="text/plain", key="dl_seq_tab3")

        if not flowchart and not sequence and (not graph_spec or not graph_spec.get("nodes")):
            st.info("🔧 Architecture diagrams will appear after analysis.")

# ── Tab 4: Generate ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("🔧 Generate Agent Boilerplate Code")
    if "roster" not in st.session_state:
        st.info("📋 Run an analysis first from the **🏠 Analyze** tab.")
    else:
        roster = st.session_state["roster"]
        recommended = roster.get("recommended_framework", "CrewAI")
        st.write("#### 📋 Framework Comparison")
        fw_data = [("CrewAI","Role-based agent teams","Low","Basic","✅"),
            ("LangGraph","Stateful, complex workflows","Medium","Advanced","✅"),
            ("AutoGen","Conversational multi-agent","Medium","Basic","✅"),
            ("LlamaIndex","RAG-heavy pipelines","High","Advanced","✅")]
        rh = ""
        for fn, bf, cx, sm, fr in fw_data:
            cls = ' class="recommended"' if fn == recommended else ""
            badge = ' <span style="background:#059669;color:white;padding:1px 6px;border-radius:4px;font-size:0.7rem">★ Recommended</span>' if fn == recommended else ""
            rh += f"<tr{cls}><td><strong>{fn}</strong>{badge}</td><td>{bf}</td><td>{cx}</td><td>{sm}</td><td>{fr}</td></tr>"
        st.markdown(f'<table class="fw-table"><thead><tr><th>Framework</th><th>Best For</th>'
            f'<th>Complexity</th><th>State Mgmt</th><th>Free</th></tr></thead><tbody>{rh}</tbody></table>', unsafe_allow_html=True)
        avail = ["CrewAI", "LangGraph", "AutoGen"]
        idx = avail.index(recommended) if recommended in avail else 0
        selected_framework = st.radio("Select framework:", avail, index=idx, horizontal=True, key="selected_framework")
        st.divider()
        if st.button("⚙️ Generate Code", type="primary"):
            with st.spinner(f"Generating {selected_framework} boilerplate..."):
                try:
                    resp = requests.post(f"{API_BASE}/api/v1/generate-boilerplate",
                        data={"roster_json": json.dumps(roster), "framework": selected_framework}, timeout=30)
                    if resp.status_code == 200:
                        st.session_state["generated_code"] = resp.json().get("code", "# No code")
                        st.session_state["generated_framework"] = selected_framework
                    else: st.error(f"Failed: {resp.json().get('detail', resp.text)}")
                except Exception as e: st.error(f"Error: {e}")
        if "generated_code" in st.session_state:
            gfw = st.session_state.get("generated_framework", "")
            st.write(f"#### 💻 Generated {gfw} Code")
            st.code(st.session_state["generated_code"], language="python")
            st.download_button(f"⬇️ Download {gfw} Script (.py)",
                data=st.session_state["generated_code"],
                file_name=f"agentifyx_{gfw.lower()}.py", mime="text/x-python")
        st.divider()

        # HITL Checkpoint Map
        from app.services.hitl_generator import generate_hitl_map
        hitl_map = generate_hitl_map(roster)
        if hitl_map:
            st.write("#### ⚠️ HITL Checkpoint Map")
            hr = ""
            for aid, info in hitl_map.items():
                risk = info["risk_level"]
                rc = f"risk-{risk.lower()}"
                rclr = "#DC2626" if risk == "HIGH" else "#D97706" if risk == "MEDIUM" else "#059669"
                trig = ", ".join(info["hitl_checkpoints"]) or "General review"
                hr += f'<tr class="{rc}"><td>{info["agent_name"]}</td><td>{trig}</td><td style="color:{rclr};font-weight:600">{risk}</td><td>LangGraph interrupt()</td></tr>'
            st.markdown(f'<table class="hitl-table"><thead><tr><th>Agent</th><th>Triggers</th><th>Risk Level</th><th>Pattern</th></tr></thead><tbody>{hr}</tbody></table>', unsafe_allow_html=True)
            for aid, info in hitl_map.items():
                with st.expander(f"📋 {info['agent_name']} — HITL Code Snippet"):
                    st.code(info["code_snippet"], language="python")
        st.divider()

        # Tools Recommendation
        from app.services.tools_matcher import match_tools
        fw_low = selected_framework.lower() if selected_framework else "crewai"
        tool_matches = match_tools(roster, fw_low)
        if tool_matches:
            st.write("#### 🔧 Recommended Tools by Agent")
            am = {a.get("agent_id"): a for a in roster.get("agents", [])}
            for aid, tools in tool_matches.items():
                aname = am.get(aid, {}).get("agent_name", aid)
                with st.expander(f"🔹 {aname} — {len(tools)} tools"):
                    for t in tools:
                        um = t.get("_unmatched", False)
                        nc = "#D97706" if um else "#4F9FFF"
                        fb = '⚠️ Research needed' if um else ('✅ Free' if t.get("free") else '⚠️ Has free tier')
                        dl = f' · <a href="{t["docs_url"]}" style="color:#4F9FFF;text-decoration:none">Docs ↗</a>' if t.get("docs_url") else ""
                        st.markdown(f'<div class="tool-card"><span class="tool-name" style="color:{nc}">{t["name"]}</span>'
                            f'<span class="cat-badge">{t.get("category","")}</span> · {fb}{dl}'
                            f'<div class="tool-purpose">{t.get("purpose","")}</div>'
                            f'<div style="color:#94A3B8;font-size:0.75rem;margin-top:4px"><code style="background:#252535;padding:1px 6px;border-radius:4px">{t.get("pip_install","")}</code></div>'
                            f'<div style="color:#4F9FFF;font-size:0.75rem;margin-top:2px">💡 {t.get("use_when","")}</div></div>', unsafe_allow_html=True)

# ── Tab 5: Chat ─────────────────────────────────────────────────────────────
with tab5:
    if "roster" not in st.session_state:
        st.info("📤 Please analyze a document first to enable the chat assistant.")
    else:
        roster = st.session_state["roster"]

        # ── Mode toggle ─────────────────────────────────────────
        chat_mode = st.radio(
            "Chat Mode",
            ["💬 Q&A Assistant", "🏗️ Architect Mode"],
            horizontal=True,
            key="chat_mode_radio",
            help="Q&A: ask questions about your analysis. Architect: add/modify/remove agents live.",
        )
        is_architect = chat_mode == "🏗️ Architect Mode"

        if is_architect:
            st.markdown(
                '<div style="background:rgba(124,58,237,0.15);border:1px solid #7C3AED;'
                'border-radius:8px;padding:8px 14px;color:#C4B5FD;font-weight:500;'
                'text-align:center;margin-bottom:8px">'
                '🏗️ Architect Mode — Add, modify, or remove agents through conversation. '
                'Changes update your entire dashboard live.</div>',
                unsafe_allow_html=True,
            )
            st.subheader("🏗️ Architect Chat")
        else:
            st.subheader("💬 Chat with AgentifyX Assistant")

        # ── Init state ──────────────────────────────────────────
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        if "architect_history" not in st.session_state:
            st.session_state["architect_history"] = []
        if "architect_clarification_count" not in st.session_state:
            st.session_state["architect_clarification_count"] = 0
        if "roster_snapshots" not in st.session_state:
            st.session_state["roster_snapshots"] = []
        if "pending_roster_refresh" not in st.session_state:
            st.session_state["pending_roster_refresh"] = False

        # ── Apply pending refresh (triggered from previous cycle) ─
        if st.session_state.get("pending_roster_refresh"):
            st.session_state["pending_roster_refresh"] = False
            # Roster is already updated — tabs will read from session_state

        # ── Select active history ────────────────────────────────
        active_history_key = "architect_history" if is_architect else "chat_history"
        active_history = st.session_state[active_history_key]

        # ── Smart Suggestions ────────────────────────────────────
        if len(active_history) == 0:
            st.write("#### 💡 Get started:")
            if is_architect:
                # Dynamic smart suggestions
                def _get_architect_suggestions(r):
                    suggestions = []
                    agents = r.get("agents", [])
                    if agents:
                        sa = sorted(agents, key=lambda a: a.get("confidence_score", 1))
                        w = sa[0]
                        cp = int(w.get("confidence_score", 0) * 100)
                        suggestions.append(
                            f"🔍 Strengthen {w.get('agent_name', 'agent')} — "
                            f"confidence is only {cp}%"
                        )
                        risky = ["payment", "email", "delete", "send", "billing",
                                 "notify", "refund", "transfer", "approve"]
                        for ag in agents:
                            gl = ag.get("goal", "").lower()
                            if not ag.get("hitl_required") and any(k in gl for k in risky):
                                suggestions.append(
                                    f"🔒 Add HITL to {ag.get('agent_name', 'agent')} "
                                    f"— it performs risky actions"
                                )
                                break
                    dg = r.get("data_gaps", [])
                    if dg:
                        suggestions.append(f"📋 Address: {dg[0][:55]}...")
                    suggestions.append("🛡️ Add an error handling and retry agent")
                    suggestions.append("📡 Add a monitoring and alerting agent")
                    return suggestions[:4]

                suggestions = _get_architect_suggestions(roster)
            else:
                suggestions = [
                    "❓ Why these specific agents?",
                    "🔧 How do I implement HITL checkpoints?",
                    "⚖️ Which framework should I choose?",
                    "🛠️ What tools should I set up first?",
                    "⏱️ How long will this transformation take?",
                ]

            sg_cols = st.columns(min(len(suggestions), 4))
            for col, sug in zip(sg_cols, suggestions):
                with col:
                    if st.button(sug, key=f"sg_{hash(sug)}", use_container_width=True):
                        st.session_state["pending_chat_msg"] = sug
                        st.rerun()

        # ── Undo button (Architect Mode only) ────────────────────
        if is_architect and st.session_state.get("roster_snapshots"):
            undo_col, spacer_col = st.columns([2, 8])
            with undo_col:
                if st.button("↩️ Undo Last Change", key="arch_undo"):
                    snaps = st.session_state["roster_snapshots"]
                    prev_roster = snaps.pop()
                    st.session_state["roster"] = prev_roster
                    st.session_state["roster_snapshots"] = snaps
                    # Remove the last roster_update + user message pair from history
                    ah = st.session_state["architect_history"]
                    while ah and ah[-1].get("msg_type") != "roster_update":
                        ah.pop()
                    if ah:
                        ah.pop()  # remove the roster_update message
                    if ah:
                        ah.pop()  # remove the user message that triggered it
                    st.session_state["architect_history"] = ah
                    st.success("↩️ Reverted to previous roster.")
                    st.rerun()

        # ── Render conversation history ──────────────────────────
        for msg in active_history:
            role = msg.get("role", "user")
            msg_type = msg.get("msg_type", "text")

            if msg_type == "roster_update":
                # Special green roster update bubble
                changes = msg.get("changes", {})
                added = changes.get("added", [])
                modified = changes.get("modified", [])
                removed = changes.get("removed", [])
                summary_parts = []
                if added:
                    summary_parts.append(f"**Added:** {', '.join(added)}")
                if modified:
                    summary_parts.append(f"**Modified:** {', '.join(modified)}")
                if removed:
                    summary_parts.append(f"**Removed:** {', '.join(removed)}")
                changes_text = " · ".join(summary_parts) if summary_parts else "Roster updated"

                st.markdown(
                    f'<div style="background:rgba(5,150,105,0.15);border:1px solid #059669;'
                    f'border-radius:8px;padding:10px 14px;margin:6px 0">'
                    f'<span style="color:#6EE7B7;font-weight:700">✅ Roster Updated</span>'
                    f'<br><span style="color:#E2E8F0">{msg.get("content", "")}</span>'
                    f'<br><span style="color:#94A3B8;font-size:0.85rem">{changes_text}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                with st.chat_message(role, avatar="🤖" if role == "assistant" else None):
                    st.markdown(msg.get("content", ""))

        # ── Chat input ───────────────────────────────────────────
        pending = st.session_state.pop("pending_chat_msg", None)
        chat_col1, chat_col2 = st.columns([6, 1])
        with chat_col1:
            placeholder = (
                "Tell me what to change: add agents, modify tools, set HITL..."
                if is_architect
                else "Ask about your agent architecture..."
            )
            user_input = st.text_input(
                "Message", placeholder=placeholder,
                key="chat_text_input", label_visibility="collapsed",
            )
        with chat_col2:
            send_clicked = st.button("📩 Send", key="chat_send_btn", type="primary")

        if pending and not user_input:
            user_input = pending
            send_clicked = True

        # ── Send message ─────────────────────────────────────────
        if user_input and send_clicked:
            # Append user message
            user_msg = {"role": "user", "content": user_input, "msg_type": "text"}
            if is_architect:
                user_msg["roster_before"] = json.dumps(roster)
            active_history.append(user_msg)
            with st.chat_message("user"):
                st.markdown(user_input)

            if is_architect:
                # ── ARCHITECT MODE: call modify-roster endpoint ──
                with st.spinner("🏗️ Analyzing your request..."):
                    # Build conversation history for the endpoint (content only)
                    conv_hist = [
                        {"role": m["role"], "content": m["content"]}
                        for m in active_history[-8:]
                        if m.get("msg_type") != "roster_update"
                    ]
                    payload = {
                        "message": user_input,
                        "current_roster": roster,
                        "conversation_history": conv_hist,
                        "source_document": st.session_state.get("uploaded_filename"),
                        "clarification_count": st.session_state.get(
                            "architect_clarification_count", 0
                        ),
                    }
                    try:
                        resp = requests.post(
                            f"{API_BASE}/api/chat/modify-roster",
                            json=payload, timeout=120,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            resp_type = data.get("response_type", "message")

                            if resp_type == "roster_update":
                                # Save snapshot for undo BEFORE applying
                                st.session_state["roster_snapshots"].append(
                                    json.loads(json.dumps(roster))
                                )
                                # Apply the update
                                updated = data.get("updated_roster", roster)
                                st.session_state["roster"] = updated

                                # Add roster update message to history
                                active_history.append({
                                    "role": "assistant",
                                    "content": data.get("content", "Roster updated."),
                                    "msg_type": "roster_update",
                                    "changes": data.get("changes_summary", {}),
                                    "roster_after": json.dumps(updated),
                                })
                                # Reset clarification counter
                                st.session_state["architect_clarification_count"] = 0
                                st.session_state[active_history_key] = active_history

                                # Show success + refresh button
                                st.success(
                                    f"✅ {data.get('content', 'Roster updated!')} "
                                    "— All tabs now reflect the changes."
                                )
                                st.rerun()

                            else:
                                # Conversational reply
                                st.session_state["architect_clarification_count"] += 1
                                reply = data.get("content", "I'm not sure how to help.")
                                active_history.append({
                                    "role": "assistant",
                                    "content": reply,
                                    "msg_type": "text",
                                })
                                with st.chat_message("assistant", avatar="🤖"):
                                    st.markdown(reply)
                        else:
                            detail = resp.json().get("detail", f"Status {resp.status_code}")
                            err_msg = f"⚠️ Error: {detail}"
                            active_history.append({
                                "role": "assistant", "content": err_msg,
                                "msg_type": "text",
                            })
                            with st.chat_message("assistant", avatar="🤖"):
                                st.markdown(err_msg)
                    except requests.exceptions.ConnectionError:
                        err_msg = "❌ Cannot connect to API."
                        active_history.append({
                            "role": "assistant", "content": err_msg,
                            "msg_type": "text",
                        })
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(err_msg)
                    except Exception as e:
                        err_msg = f"⚠️ Error: {e}"
                        active_history.append({
                            "role": "assistant", "content": err_msg,
                            "msg_type": "text",
                        })
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(err_msg)

            else:
                # ── Q&A MODE: existing streaming chat ────────────
                with st.chat_message("assistant", avatar="🤖"):
                    rp = st.empty()
                    full = ""
                    payload = {
                        "message": user_input,
                        "session_id": st.session_state.get("session_id", ""),
                        "conversation_history": active_history[-20:],
                        "roster_json": roster,
                        "source_document": st.session_state.get("uploaded_filename"),
                    }
                    try:
                        resp = requests.post(
                            f"{API_BASE}/api/chat", json=payload,
                            stream=True, timeout=60,
                        )
                        if resp.status_code == 200:
                            for chunk in resp.iter_content(
                                chunk_size=None, decode_unicode=True
                            ):
                                if chunk:
                                    full += chunk
                                    rp.markdown(full + "▌")
                            rp.markdown(full)
                        else:
                            full = f"⚠️ Error: status {resp.status_code}"
                            rp.markdown(full)
                    except requests.exceptions.ConnectionError:
                        full = "❌ Cannot connect to API."
                        rp.markdown(full)
                    except Exception as e:
                        full = f"⚠️ Error: {e}"
                        rp.markdown(full)
                active_history.append({
                    "role": "assistant", "content": full, "msg_type": "text",
                })

            st.session_state[active_history_key] = active_history

            # Persist chat history to session
            sid = st.session_state.get("session_id")
            if sid:
                try:
                    plain_history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in active_history[-20:]
                    ]
                    requests.put(
                        f"{API_BASE}/api/v1/sessions/{sid}/chat",
                        json=plain_history, timeout=3,
                    )
                except Exception:
                    pass

# ── Tab 6: Simulate ─────────────────────────────────────────────────────────
with tab6:
    if "roster" not in st.session_state:
        st.info("📋 Run an analysis first from the **🏠 Analyze** tab.")
    else:
        import time as _time
        from app.services.simulation_generator import generate_simulation

        roster = st.session_state["roster"]

        # Always-visible simulation mode banner
        st.markdown(
            '<div style="background:rgba(217,119,6,0.15);border:1px solid #D97706;'
            'border-radius:8px;padding:10px 16px;color:#FCD34D;font-weight:600;'
            'text-align:center;margin-bottom:12px">'
            '📋 SIMULATION MODE — Not real execution (mock timings &amp; data)</div>',
            unsafe_allow_html=True,
        )

        st.subheader("▶️ Agent Pipeline Simulation")

        # ── Init session state ──────────────────────────────────
        if "sim_steps" not in st.session_state:
            st.session_state["sim_steps"] = []
        if "sim_current" not in st.session_state:
            st.session_state["sim_current"] = 0
        if "sim_running" not in st.session_state:
            st.session_state["sim_running"] = False
        if "sim_paused" not in st.session_state:
            st.session_state["sim_paused"] = False
        if "sim_log" not in st.session_state:
            st.session_state["sim_log"] = []
        if "sim_done" not in st.session_state:
            st.session_state["sim_done"] = False
        if "sim_hitl_decisions" not in st.session_state:
            st.session_state["sim_hitl_decisions"] = []

        # ── Controls ────────────────────────────────────────────
        ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 6])
        with ctrl1:
            if st.button("▶️ Start Simulation", type="primary", key="sim_start",
                         disabled=st.session_state["sim_running"]):
                st.session_state["sim_steps"] = generate_simulation(roster)
                st.session_state["sim_current"] = 0
                st.session_state["sim_running"] = True
                st.session_state["sim_paused"] = False
                st.session_state["sim_done"] = False
                st.session_state["sim_log"] = []
                st.session_state["sim_hitl_decisions"] = []
                st.rerun()
        with ctrl2:
            if st.button("🔄 Reset", key="sim_reset"):
                for k in ["sim_steps", "sim_current", "sim_running", "sim_paused",
                           "sim_log", "sim_done", "sim_hitl_decisions"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

        steps = st.session_state.get("sim_steps", [])
        current = st.session_state.get("sim_current", 0)

        # Progress bar
        if steps:
            st.progress(min(current / max(len(steps) - 1, 1), 1.0))
            st.caption(f"Step {current} / {len(steps) - 1}")

        # ── Active agent indicator ──────────────────────────────
        if st.session_state["sim_running"] and not st.session_state["sim_done"] and steps:
            active_name = steps[current]["agent_name"] if current < len(steps) else "—"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:8px 0">'
                f'<span style="display:inline-block;width:12px;height:12px;'
                f'background:#4F9FFF;border-radius:50%;'
                f'animation:pulse 1.2s infinite"></span>'
                f'<span style="color:#E2E8F0;font-weight:600">Currently active: {active_name}</span>'
                f'</div>'
                f'<style>@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}</style>',
                unsafe_allow_html=True,
            )

        # ── Terminal log ────────────────────────────────────────
        sim_log = st.session_state.get("sim_log", [])
        if sim_log:
            log_html = ""
            for entry in sim_log:
                clr = entry.get("color", "#94A3B8")
                log_html += f'<div style="color:{clr};margin:2px 0">{entry["text"]}</div>'
            st.markdown(
                f'<div style="background:#0D0D1A;border:1px solid #333355;border-radius:8px;'
                f'padding:12px;font-family:Consolas,monospace;font-size:0.82rem;'
                f'max-height:300px;overflow-y:auto">{log_html}</div>',
                unsafe_allow_html=True,
            )

        # ── HITL Pause Panel ────────────────────────────────────
        if st.session_state.get("sim_paused") and current < len(steps):
            step = steps[current]
            st.markdown(
                f'<div style="background:rgba(217,119,6,0.15);border:1px solid #D97706;'
                f'border-radius:8px;padding:14px;margin:10px 0">'
                f'<b style="color:#FCD34D">⏸️ HITL CHECKPOINT — Human Approval Required</b><br>'
                f'<span style="color:#E2E8F0">Agent: <b>{step["agent_name"]}</b></span><br>'
                f'<span style="color:#94A3B8">{step["hitl_message"]}</span><br>'
                f'<span style="color:#94A3B8">Checkpoints: '
                f'{", ".join(step["hitl_checkpoints"]) if step["hitl_checkpoints"] else "General review"}'
                f'</span></div>',
                unsafe_allow_html=True,
            )
            h1, h2, h3 = st.columns(3)
            with h1:
                if st.button("✅ Approve", key="sim_approve", type="primary"):
                    now = _time.strftime("%H:%M:%S")
                    st.session_state["sim_log"].append({
                        "text": f"[{now}] ✅ APPROVED — {step['agent_name']} continues",
                        "color": "#059669",
                    })
                    st.session_state["sim_hitl_decisions"].append(
                        {"agent": step["agent_name"], "decision": "approved"})
                    st.session_state["sim_paused"] = False
                    st.session_state["sim_current"] = current + 1
                    st.rerun()
            with h2:
                if st.button("❌ Reject", key="sim_reject"):
                    now = _time.strftime("%H:%M:%S")
                    st.session_state["sim_log"].append({
                        "text": f"[{now}] ❌ REJECTED — {step['agent_name']} output discarded",
                        "color": "#DC2626",
                    })
                    st.session_state["sim_hitl_decisions"].append(
                        {"agent": step["agent_name"], "decision": "rejected"})
                    st.session_state["sim_paused"] = False
                    st.session_state["sim_current"] = current + 1
                    st.rerun()
            with h3:
                if st.button("🔺 Escalate", key="sim_escalate"):
                    now = _time.strftime("%H:%M:%S")
                    st.session_state["sim_log"].append({
                        "text": f"[{now}] 🔺 ESCALATED — {step['agent_name']} sent to senior review",
                        "color": "#D97706",
                    })
                    st.session_state["sim_hitl_decisions"].append(
                        {"agent": step["agent_name"], "decision": "escalated"})
                    st.session_state["sim_paused"] = False
                    st.session_state["sim_current"] = current + 1
                    st.rerun()

        # ── Step animation engine ───────────────────────────────
        if (st.session_state.get("sim_running") and
                not st.session_state.get("sim_paused") and
                not st.session_state.get("sim_done") and
                steps and current < len(steps)):
            step = steps[current]
            now = _time.strftime("%H:%M:%S")

            # Determine color by step type
            type_colors = {
                "start": "#94A3B8", "end": "#059669",
                "agent_exec": "#E2E8F0", "agent_input": "#4F9FFF",
                "agent_output": "#FCD34D", "hitl": "#D97706",
            }
            clr = type_colors.get(step["type"], "#E2E8F0")
            icon = {"start": "🚀", "end": "🏁", "agent_exec": "🤖",
                    "agent_input": "📥", "agent_output": "📤", "hitl": "⏸️"
                    }.get(step["type"], "▸")

            dur_str = f" ({step['duration_ms']}ms)" if step["duration_ms"] else ""
            tok_str = f" [{step['tokens_estimated']} tokens]" if step["tokens_estimated"] else ""
            log_text = f"[{now}] {icon} {step['agent_name']} → {step['action']}{dur_str}{tok_str} ✓"

            st.session_state["sim_log"].append({"text": log_text, "color": clr})

            if step.get("hitl_pause"):
                st.session_state["sim_paused"] = True
                st.rerun()
            elif step["type"] == "end":
                st.session_state["sim_done"] = True
                st.session_state["sim_running"] = False
                st.rerun()
            else:
                st.session_state["sim_current"] = current + 1
                _time.sleep(0.8)
                st.rerun()

        # ── Completion Summary ──────────────────────────────────
        if st.session_state.get("sim_done") and steps:
            end_step = steps[-1]
            st.success("✅ Simulation Complete!")

            total_steps = len(steps)
            total_hitl = end_step.get("total_hitl", 0)
            total_auto = end_step.get("total_auto", 0)
            auto_rate = end_step.get("automation_rate", 0)
            total_tokens = sum(s.get("tokens_estimated", 0) for s in steps)
            total_duration = sum(s.get("duration_ms", 0) for s in steps)

            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("📌 Total Steps", total_steps)
            with m2: st.metric("🤖 Autonomous Steps", total_auto)
            with m3: st.metric("👤 Human Checkpoints", total_hitl)
            with m4: st.metric("⚡ Automation Rate", f"{auto_rate}%")

            st.divider()
            t1, t2 = st.columns(2)
            with t1: st.metric("🎫 Est. Tokens Used", f"{total_tokens:,}")
            with t2: st.metric("⏱️ Est. Duration", f"{total_duration / 1000:.1f}s")

            decisions = st.session_state.get("sim_hitl_decisions", [])
            if decisions:
                st.write("#### 📋 HITL Decisions Log")
                for d in decisions:
                    icon = {"approved": "✅", "rejected": "❌", "escalated": "🔺"}.get(d["decision"], "▸")
                    st.write(f"{icon} **{d['agent']}** — {d['decision']}")

            st.caption("⚠️ Simulation uses mock timings and token estimates. "
                       "Real performance will vary based on model, data, and infrastructure.")

# ── Tab 7: Export ────────────────────────────────────────────────────────────
with tab7:
    st.subheader("📥 Export & Download")
    if "roster" not in st.session_state:
        st.info("📋 Run an analysis first from the **🏠 Analyze** tab.")
    else:
        roster = st.session_state["roster"]
        boilerplate = st.session_state.get("generated_code", "")
        gen_fw = st.session_state.get("generated_framework", "")

        # Row 1: Reports
        st.write("#### 📄 Reports")
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            if st.button("📄 Generate PDF Report", type="primary", key="gen_pdf"):
                with st.spinner("Generating PDF..."):
                    from app.services.report_generator import generate_pdf_report
                    pdf_bytes = generate_pdf_report(roster, boilerplate)
                    st.session_state["pdf_report"] = pdf_bytes
                    st.success("PDF ready!")
            if "pdf_report" in st.session_state:
                st.download_button("⬇️ Download PDF Report",
                    data=st.session_state["pdf_report"],
                    file_name="agentifyx_report.pdf", mime="application/pdf", key="dl_pdf")

        with r1c2:
            if st.button("📝 Generate DOCX Report", type="primary", key="gen_docx"):
                with st.spinner("Generating DOCX..."):
                    from app.services.docx_generator import generate_docx_report
                    docx_bytes = generate_docx_report(roster, boilerplate)
                    st.session_state["docx_report"] = docx_bytes
                    st.success("DOCX ready!")
            if "docx_report" in st.session_state:
                st.download_button("⬇️ Download DOCX Report",
                    data=st.session_state["docx_report"],
                    file_name="agentifyx_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="dl_docx")

        st.divider()

        # Row 2: Code & Data
        st.write("#### 💻 Code & Data")
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            if boilerplate:
                st.download_button(f"🐍 Download {gen_fw} Boilerplate (.py)",
                    data=boilerplate, file_name=f"agentifyx_{gen_fw.lower()}.py",
                    mime="text/x-python", key="dl_code_tab7")
            else:
                st.info("Generate code in the **🔧 Generate** tab first.")
        with r2c2:
            st.download_button("📊 Download Agent Roster (.json)",
                data=json.dumps(roster, indent=2),
                file_name="agent_roster.json", mime="application/json", key="dl_json_tab7")

        st.divider()

        # Row 3: Diagrams
        st.write("#### 📐 Architecture Diagrams")
        flowchart = roster.get("mermaid_flowchart", "")
        sequence = roster.get("mermaid_sequence", "")
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            if flowchart:
                st.download_button("📐 Download Flowchart (.mmd)",
                    data=flowchart, file_name="agent_workflow.mmd",
                    mime="text/plain", key="dl_flow_tab7")
            else:
                st.caption("No flowchart generated.")
        with r3c2:
            if sequence:
                st.download_button("📐 Download Sequence (.mmd)",
                    data=sequence, file_name="agent_sequence.mmd",
                    mime="text/plain", key="dl_seq_tab7")
            else:
                st.caption("No sequence diagram generated.")