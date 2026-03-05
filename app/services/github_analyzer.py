"""
GitHub Repository Analyzer — fetches Python files from a repo and performs
AST analysis to identify agent candidates, imports, and code structure.
"""

import ast
import re
import logging
from urllib.parse import urlparse
from collections import Counter

from github import Github, GithubException, RateLimitExceededException

logger = logging.getLogger(__name__)

# Known stdlib modules (subset) to filter out from external imports
_STDLIB = {
    "os", "sys", "re", "json", "math", "time", "datetime", "collections",
    "functools", "itertools", "typing", "pathlib", "logging", "abc",
    "dataclasses", "enum", "copy", "io", "hashlib", "uuid", "random",
    "string", "textwrap", "shutil", "subprocess", "threading", "multiprocessing",
    "socket", "http", "urllib", "email", "csv", "sqlite3", "xml", "html",
    "argparse", "configparser", "unittest", "traceback", "warnings",
    "contextlib", "importlib", "inspect", "ast", "dis", "pickle",
    "struct", "codecs", "base64", "hmac", "secrets", "tempfile", "glob",
    "fnmatch", "stat", "gzip", "zipfile", "tarfile", "pdb", "profile",
    "cProfile", "pprint", "operator", "decimal", "fractions", "statistics",
    "array", "queue", "heapq", "bisect", "weakref", "types", "signal",
    "mmap", "ctypes", "concurrent", "asyncio", "selectors", "ssl",
    "platform", "sysconfig", "site",
}

URL_PATTERN = re.compile(r"https?://[^\s'\"]+")


# ═════════════════════════════════════════════════════════════════════════════
#  AST Analysis (Task 2)
# ═════════════════════════════════════════════════════════════════════════════
def _count_branches(node: ast.AST) -> int:
    """Count If/For/While nodes inside a function body."""
    count = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While)):
            count += 1
    return count


def analyze_python_file(filename: str, source_code: str) -> dict:
    """Analyze a single Python file using AST. Returns structured analysis."""
    result = {
        "file": filename,
        "functions": [],
        "classes": [],
        "external_imports": [],
        "detected_urls": [],
    }

    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as e:
        logger.warning("Syntax error in %s: %s", filename, e)
        return result

    # ── Functions ───────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node) or ""
            branch_count = _count_branches(node)
            result["functions"].append({
                "name": node.name,
                "line": node.lineno,
                "docstring": docstring[:200],  # truncate long docstrings
                "branch_count": branch_count,
                "is_candidate": branch_count > 8,
            })

    # ── Classes ─────────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(ast.dump(base))
            result["classes"].append({
                "name": node.name,
                "bases": bases,
            })

    # ── Imports ─────────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in _STDLIB:
                    result["external_imports"].append(top)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top not in _STDLIB:
                    result["external_imports"].append(top)

    result["external_imports"] = sorted(set(result["external_imports"]))

    # ── URLs in string literals ─────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            urls = URL_PATTERN.findall(node.value)
            result["detected_urls"].extend(urls)

    result["detected_urls"] = list(set(result["detected_urls"]))

    return result


def build_code_summary(file_analyses: list[dict]) -> dict:
    """Aggregate analysis across all files into a summary."""
    total_funcs = 0
    candidates = []
    all_imports = Counter()
    all_urls = set()

    for fa in file_analyses:
        for fn in fa.get("functions", []):
            total_funcs += 1
            if fn.get("is_candidate"):
                candidates.append({
                    "file": fa["file"],
                    "function": fn["name"],
                    "branch_count": fn["branch_count"],
                    "reason": f"High complexity: {fn['branch_count']} branches",
                })
        for imp in fa.get("external_imports", []):
            all_imports[imp] += 1
        for url in fa.get("detected_urls", []):
            all_urls.add(url)

    sorted_imports = sorted(set(all_imports.keys()))
    top_5 = [imp for imp, _ in all_imports.most_common(5)]

    return {
        "total_files_analyzed": len(file_analyses),
        "total_functions": total_funcs,
        "agent_candidate_functions": candidates,
        "all_external_imports": sorted_imports,
        "detected_api_endpoints": sorted(all_urls),
        "primary_frameworks": top_5,
        "complexity_summary": (
            f"{total_funcs} functions analyzed, "
            f"{len(candidates)} are strong agent candidates"
        ),
    }


# ═════════════════════════════════════════════════════════════════════════════
#  GitHub Integration (Task 1)
# ═════════════════════════════════════════════════════════════════════════════
def _parse_repo_info(repo_url: str) -> str:
    """Extract 'owner/repo' from various GitHub URL formats."""
    url = repo_url.strip().rstrip("/")

    # Handle github.com/owner/repo or https://github.com/owner/repo
    parsed = urlparse(url)
    path = parsed.path if parsed.scheme else url

    # Remove leading "github.com/" if no scheme
    if path.startswith("github.com/"):
        path = path[len("github.com/"):]

    # Remove leading slash
    path = path.lstrip("/")

    # Remove .git suffix
    if path.endswith(".git"):
        path = path[:-4]

    # Take only owner/repo (ignore /tree/main/..., etc.)
    parts = path.split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"

    raise ValueError(f"Could not parse GitHub repo from URL: {repo_url}")


def _get_python_files(repo, path: str = "") -> list:
    """Recursively get all Python files from a repo."""
    py_files = []
    try:
        contents = repo.get_contents(path)
    except GithubException:
        return py_files

    while contents:
        item = contents.pop(0)
        if item.type == "dir":
            # Skip common non-source directories
            skip_dirs = {"venv", ".venv", "env", "node_modules", "__pycache__",
                         ".git", ".tox", "dist", "build", "egg-info"}
            if item.name not in skip_dirs:
                try:
                    contents.extend(repo.get_contents(item.path))
                except GithubException:
                    pass
        elif item.name.endswith(".py"):
            py_files.append(item)

    return py_files


def analyze_github_repo(repo_url: str, pat: str = None) -> dict:
    """
    Analyze a GitHub repository's Python files.
    Returns: {"code_summary": {...}, "file_analyses": [...], "repo_name": str, "warning": str|None}
    """
    # Parse repo
    try:
        repo_path = _parse_repo_info(repo_url)
    except ValueError as e:
        return {"error": str(e)}

    # Init GitHub
    try:
        g = Github(pat) if pat else Github()
        repo = g.get_repo(repo_path)
    except RateLimitExceededException:
        return {
            "error": (
                "⏳ GitHub API rate limit exceeded (60 requests/hour for unauthenticated). "
                "Please provide a Personal Access Token (PAT) in the PAT field for "
                "5000 requests/hour. Create one at: "
                "https://github.com/settings/tokens/new (select 'repo' scope)"
            )
        }
    except GithubException as e:
        if e.status == 403:
            return {
                "error": (
                    "⏳ GitHub API rate limit exceeded. "
                    "Please provide a Personal Access Token (PAT) in the PAT field for "
                    "higher limits (5000 req/hr). Create one at: "
                    "https://github.com/settings/tokens/new"
                )
            }
        elif e.status == 401:
            return {"error": "Invalid PAT or private repo — please provide a valid PAT."}
        elif e.status == 404:
            return {"error": "Repository not found — check the URL."}
        else:
            return {"error": f"GitHub API error: {e}"}

    # Fetch Python files
    warning = None
    try:
        py_files = _get_python_files(repo)
    except Exception as e:
        return {"error": f"Error fetching files: {e}"}

    if not py_files:
        return {"error": "No Python files found in this repository."}

    # Truncate if too many files
    if len(py_files) > 50:
        py_files.sort(key=lambda f: f.size or 0, reverse=True)
        py_files = py_files[:25]
        warning = f"Repository has 50+ Python files. Analyzed the top 25 by size."

    # Analyze each file
    file_analyses = []
    for pf in py_files:
        try:
            source = pf.decoded_content.decode("utf-8")
            analysis = analyze_python_file(pf.path, source)
            file_analyses.append(analysis)
        except Exception as e:
            logger.warning("Skipping file %s: %s", pf.path, e)
            continue

    # Build summary
    code_summary = build_code_summary(file_analyses)

    return {
        "repo_name": repo_path,
        "code_summary": code_summary,
        "file_analyses": file_analyses,
        "warning": warning,
    }
