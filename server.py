import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP
from tools.codebase import ask_repo, search_code, get_file, repo_info, list_files
from tools.packages import search_packages, get_package_info, check_dependencies, find_alternatives
from tools.combined import audit_repo, repo_summary, compare

mcp = FastMCP("CodeLens")

# ─── Codebase Tools ────────────────────────────────────────────────────────────

@mcp.tool()
def tool_ask_repo(question: str, repo: str) -> str:
    """
    Answer a natural language question about any public GitHub repo.
    No indexing needed — searches and fetches code on the fly.

    Args:
        question: e.g. 'How does authentication work?'
        repo: e.g. 'tiangolo/fastapi'
    """
    return ask_repo(question, repo)


@mcp.tool()
def tool_search_code(query: str, repo: str, language: str = "") -> str:
    """
    Search for specific code patterns in a GitHub repo.

    Args:
        query: e.g. 'database connection pool'
        repo: e.g. 'tiangolo/fastapi'
        language: Optional filter e.g. 'python', 'javascript'
    """
    return search_code(query, repo, language if language else None)


@mcp.tool()
def tool_get_file(repo: str, file_path: str) -> str:
    """
    Fetch the full contents of a specific file from a GitHub repo.

    Args:
        repo: e.g. 'tiangolo/fastapi'
        file_path: e.g. 'fastapi/routing.py'
    """
    return get_file(repo, file_path)


@mcp.tool()
def tool_repo_info(repo: str) -> str:
    """
    Get metadata about a GitHub repository — stars, language, license, topics.

    Args:
        repo: e.g. 'tiangolo/fastapi'
    """
    return repo_info(repo)


@mcp.tool()
def tool_list_files(repo: str, extension: str = "") -> str:
    """
    List all files in a GitHub repository, optionally filtered by extension.

    Args:
        repo: e.g. 'tiangolo/fastapi'
        extension: Optional filter e.g. '.py', '.ts'
    """
    return list_files(repo, extension if extension else None)


# ─── Package Tools ─────────────────────────────────────────────────────────────

@mcp.tool()
def tool_search_packages(query: str, language: str = "") -> str:
    """
    Search for packages on Libraries.io.

    Args:
        query: e.g. 'http client python'
        language: Optional platform e.g. 'pypi', 'npm'
    """
    return search_packages(query, language if language else None)


@mcp.tool()
def tool_get_package_info(name: str, platform: str) -> str:
    """
    Get detailed info about a specific package.

    Args:
        name: e.g. 'requests'
        platform: e.g. 'pypi', 'npm', 'cargo'
    """
    return get_package_info(name, platform)


@mcp.tool()
def tool_check_dependencies(repo: str) -> str:
    """
    Check health of all dependencies in a GitHub repo.
    Fetches package files directly — no indexing needed.

    Args:
        repo: e.g. 'tiangolo/fastapi'
    """
    return check_dependencies(repo)


@mcp.tool()
def tool_find_alternatives(package_name: str, language: str = "") -> str:
    """
    Find alternative packages to replace a given dependency.

    Args:
        package_name: e.g. 'moment'
        language: Optional platform e.g. 'npm', 'pypi'
    """
    return find_alternatives(package_name, language if language else None)


# ─── Combined Tools ────────────────────────────────────────────────────────────

@mcp.tool()
def tool_audit_repo(repo: str) -> str:
    """
    Full repo audit — overview + dependency health report.
    Works on any public GitHub repo instantly, no indexing needed.

    Args:
        repo: e.g. 'tiangolo/fastapi' or full GitHub URL
    """
    return audit_repo(repo)


@mcp.tool()
def tool_repo_summary(repo: str) -> str:
    """
    High-level summary of any GitHub repo.
    Covers purpose, structure, technologies and dependency health.

    Args:
        repo: e.g. 'tiangolo/fastapi'
    """
    return repo_summary(repo)


@mcp.tool()
def tool_compare(item1: str, item2: str, platform: str = "") -> str:
    """
    Compare two GitHub repos or packages side by side.
    Auto-detects whether inputs are repos or packages.

    Args:
        item1: repo slug, GitHub URL, or package name e.g. 'express' or 'expressjs/express'
        item2: repo slug, GitHub URL, or package name e.g. 'fastify' or 'fastify/fastify'
        platform: optional platform hint e.g. 'npm', 'pypi', 'cargo'
    """
    return compare(item1, item2, platform if platform else None)



if __name__ == "__main__":
    mcp.run()