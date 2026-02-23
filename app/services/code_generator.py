import json

def generate_crewai_script(agentifyx_json_str: str) -> str:
    """Parses the LLM JSON output and generates a CrewAI boilerplate script."""
    try:
        # Clearing Markdown formatting the LLM usually adds
        clean_str = agentifyx_json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_str)
        
        agents = data.get("proposed_agents", [])

        script = 'from crewai import Agent, Crew, Process, Task\n\n'
        
        agent_names = []
        for i, agent in enumerate(agents):
            role = agent.get("role", f"Agent_{i}")
            # Create a clean variable name (like for e.g., "Intent & Sentiment Analyst" -> "intent_and_sentiment_analyst")
            var_name = role.lower().replace(" ", "_").replace("&", "and")
            agent_names.append(var_name)
            
            script += f'# --- {role} ---\n'
            script += f'{var_name} = Agent(\n'
            script += f'    role="{role}",\n'
            script += f'    goal="{agent.get("goal", "")}",\n'
            script += f'    backstory="You are a senior {role}. You execute your goals flawlessly.",\n'
            script += f'    verbose=True,\n'
            script += f'    allow_delegation=False\n'
            script += ')\n\n'
            
        script += '# --- Assemble the Crew ---\n'
        script += 'agentifyx_crew = Crew(\n'
        script += f'    agents=[{", ".join(agent_names)}],\n'
        script += '    tasks=[], # TODO: Define tasks based on the legacy workflow\n'
        script += '    process=Process.sequential,\n'
        script += '    verbose=True\n'
        script += ')\n\n'
        
        script += 'if __name__ == "__main__":\n'
        script += '    print("Starting Agentic Workflow...")\n'
        script += '    # result = agentifyx_crew.kickoff()\n'
        script += '    # print(result)\n'
        
        return script
        
    except Exception as e:
        return f"# Error generating script: {str(e)}\n# Raw input was:\n# {agentifyx_json_str}"