import streamlit as st
import requests
import json

st.set_page_config(page_title="AgentifyX Dashboard", layout="wide")
st.title("🚀 AgentifyX: Middleware Engine")
st.subheader("Transforming Conventional Solutions into Agentic AI Frameworks")

uploaded_file = st.file_uploader("Upload Legacy System Documentation (PDF)", type="pdf")

if uploaded_file is not None:
    if st.button("Analyze & Transform Architecture", type="primary"):
        with st.spinner("AgentifyX is analyzing workflows and generating a blueprint..."):

            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post("http://127.0.0.1:8000/api/v1/process-document", files=files)

            if response.status_code == 200:
                data = response.json()
                analysis_str = data["agentifyx_analysis"]

                clean_str = analysis_str.replace("```json", "").replace("```", "").strip()
                try:
                    analysis_json = json.loads(clean_str)
                    
                    st.success("Transformation Analysis Complete!")
                    st.divider()

                    col1, col2 = st.columns(2)
                    with col1:

                        st.metric(label="Agentic Readiness Score", value=f"{analysis_json.get('agentic_readiness_score', 'N/A')}/100")
                    with col2:
                        st.metric(label="Data Chunks Processed", value=data["pipeline_metrics"]["chunks_stored"])
                    
                    st.divider()

                    st.write("### 🚨 Identified Legacy Limitations")
                    for limit in analysis_json.get("current_limitations", []):
                        st.error(limit)
                        
                    st.divider()

                    st.write("### 🤖 Proposed Agentic Architecture")
                    for agent in analysis_json.get("proposed_agents", []):
                        with st.expander(f"Agent Role: {agent['role']}", expanded=True):
                            st.write(f"**Goal:** {agent['goal']}")
                            st.write(f"**Tools Required:** {', '.join(agent['tools_needed'])}")

                    st.divider()

                    st.write("### 📝 Transformation Summary")
                    st.info(analysis_json.get("transformation_summary", ""))

                    st.write("### 💻 Export Code")
                    
                    # Hit the second endpoint to get the file
                    dl_files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    dl_res = requests.post("http://127.0.0.1:8000/api/v1/download-blueprint", files=dl_files)
                    
                    if dl_res.status_code == 200:
                        st.download_button(
                            label="⬇️ Download CrewAI Boilerplate (.py)",
                            data=dl_res.content,
                            file_name="agentic_architecture.py",
                            mime="text/x-python"
                        )
                except Exception as e:
                    st.error(f"Failed to parse AI output: {e}")
            else:
                st.error("Failed to connect to AgentifyX API. Make sure FastAPI is running!")