import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.services.semantic_pipeline import collection

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3-flash-preview') 

def query_vector_db(query_text: str, n_results: int = 5) -> str:
    """Retrieves the most relevant chunks from ChromaDB."""
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    # Combine the retrieved chunks into a single context string
    if results['documents'] and len(results['documents']) > 0:
        context = "\n\n---\n\n".join(results['documents'][0])
        return context
    return "No relevant context found in the database."

def generate_agentic_blueprint(filename: str) -> dict:
    """Analyzes the document context and generates a transformation blueprint."""

    search_query = "system architecture workflows decision logic legacy limitations"
    context = query_vector_db(search_query)

    prompt = f"""
    You are AgentifyX, an expert AI middleware engine. Your task is to analyze the following extracted 
    system documentation and recommend how to transform it into an Agentic AI architecture using 
    frameworks like CrewAI or ReAct.

    DOCUMENT CONTEXT (Extracted from {filename}):
    {context}

    Provide your analysis strictly in the following JSON format:
    {{
        "agentic_readiness_score": <int between 1-100>,
        "current_limitations": ["list", "of", "limitations"],
        "proposed_agents": [
            {{"role": "Role Name", "goal": "Agent Goal", "tools_needed": ["tool1", "tool2"]}}
        ],
        "transformation_summary": "A short paragraph explaining the upgrade path."
    }}
    """

    try:
        response = model.generate_content(prompt)
        # In a production app, we would parse this JSON strictly. For the prototype, 
        # we will return the raw text block.
        return response.text
    except Exception as e:
        return f"LLM Generation Failed: {str(e)}"