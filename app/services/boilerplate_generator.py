"""
Boilerplate generator — renders framework-specific Python scripts from AgentRoster data
using Jinja2 templates.
"""

import ast
import os
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# Template directory
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

# Map framework names to template files
FRAMEWORK_TEMPLATES = {
    "CrewAI": "crewai_template.py.j2",
    "LangGraph": "langgraph_template.py.j2",
    "AutoGen": "autogen_template.py.j2",
}

SUPPORTED_FRAMEWORKS = list(FRAMEWORK_TEMPLATES.keys())


def generate_boilerplate(roster: dict, framework: str) -> str:
    """
    Render a framework-specific Python boilerplate script.

    Args:
        roster: AgentRoster dict with agents, readiness_scores, etc.
        framework: One of "CrewAI", "LangGraph", "AutoGen"

    Returns:
        Rendered Python code as a string.

    Raises:
        ValueError: If framework is not supported or rendered code has syntax errors.
    """
    if framework not in FRAMEWORK_TEMPLATES:
        raise ValueError(
            f"Unsupported framework: '{framework}'. "
            f"Supported: {SUPPORTED_FRAMEWORKS}"
        )

    template_name = FRAMEWORK_TEMPLATES[framework]

    try:
        template = _env.get_template(template_name)
    except Exception as e:
        raise ValueError(f"Failed to load template '{template_name}': {e}") from e

    # Wrap roster dict in a simple namespace for dot-access in Jinja2
    roster_obj = _DictNamespace(roster)
    rendered = template.render(roster=roster_obj)

    # Validate syntax
    try:
        ast.parse(rendered)
    except SyntaxError as e:
        logger.error("Generated %s code has syntax errors: %s", framework, e)
        logger.debug("Rendered code:\n%s", rendered)
        # Return with a warning comment instead of crashing
        return (
            f"# ⚠️ WARNING: Auto-generated code has a syntax issue on line {e.lineno}.\n"
            f"# Error: {e.msg}\n"
            f"# Please review and fix manually.\n\n"
            f"{rendered}"
        )

    return rendered


class _DictNamespace:
    """Wraps a dict so Jinja2 templates can use dot notation (roster.agents)."""

    def __init__(self, d: dict):
        for key, value in d.items():
            if isinstance(value, dict):
                setattr(self, key, _DictNamespace(value))
            elif isinstance(value, list):
                setattr(self, key, [
                    _DictNamespace(item) if isinstance(item, dict) else item
                    for item in value
                ])
            else:
                setattr(self, key, value)

    def __getattr__(self, name):
        return ""  # Return empty string for missing attributes

    def get(self, key, default=None):
        return getattr(self, key, default)

    def items(self):
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }.items()
