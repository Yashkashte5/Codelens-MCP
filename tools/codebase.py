"""
Codebase tools: ask_repo, search_code, get_file, repo_info, list_files
All powered by GitHub API — no indexing required.
"""

from typing import Optional
from github import (
    search_code as gh_search,
    get_file_content,
    get_repo_info,
    get_repo_tree,
    extract_search_term,
)


def ask_repo(question: str, repo: str) -> str:
    """
    Answer a natural language question about any public GitHub repo.
    Searches the repo for relevant code and returns it with file citations.

    Args:
        question: e.g. 'How does authentication work?'
        repo: e.g. 'tiangolo/fastapi'
    """
    try:
        search_term = extract_search_term(question)
        results = gh_search(repo, search_term)

        if not results or "error" in results[0]:
            error = results[0].get("error", "No results") if results else "No results"
            return f"Could not search repo '{repo}': {error}"

        context_parts = []
        for item in results[:4]:
            file_path = item["file_path"]
            content = get_file_content(repo, file_path)
            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"
            context_parts.append(
                f"File: {file_path}\n"
                f"{'─' * 40}\n"
                f"{content}"
            )

        context = "\n\n".join(context_parts)
        return (
            f"Relevant code from '{repo}' for: \"{question}\"\n"
            f"Search term used: '{search_term}'\n\n"
            f"{context}\n\n"
            f"Use the above code to answer the question with exact file citations."
        )

    except Exception as e:
        return f"Error: {str(e)}"


def search_code(query: str, repo: str, language: Optional[str] = None) -> str:
    """
    Search for specific code patterns in a GitHub repo.

    Args:
        query: e.g. 'database connection pool'
        repo: e.g. 'tiangolo/fastapi'
        language: optional filter e.g. 'python', 'javascript'
    """
    try:
        results = gh_search(repo, query, language)

        if not results or "error" in results[0]:
            error = results[0].get("error", "No results") if results else "No results"
            return f"Search failed for '{repo}': {error}"

        lines = [f"Search results for '{query}' in '{repo}':\n"]
        for i, item in enumerate(results, 1):
            lines.append(
                f"{i}. {item['file_path']}\n"
                f"   {item['url']}"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


def get_file(repo: str, file_path: str) -> str:
    """
    Fetch the full contents of a specific file from a GitHub repo.

    Args:
        repo: e.g. 'tiangolo/fastapi'
        file_path: e.g. 'fastapi/routing.py'
    """
    try:
        content = get_file_content(repo, file_path)
        if content.startswith("Error"):
            return content
        return f"{repo}/{file_path}\n{'─' * 40}\n{content}"
    except Exception as e:
        return f"Error: {str(e)}"


def repo_info(repo: str) -> str:
    """
    Get metadata about a GitHub repository.

    Args:
        repo: e.g. 'tiangolo/fastapi'
    """
    try:
        info = get_repo_info(repo)
        if "error" in info:
            return f"Error: {info['error']}"

        topics = ", ".join(info["topics"]) if info["topics"] else "none"
        return (
            f"{info['name']}\n"
            f"Description : {info['description']}\n"
            f"Language    : {info['language']}\n"
            f"Stars       : {info['stars']:,}\n"
            f"Forks       : {info['forks']:,}\n"
            f"Open issues : {info['open_issues']:,}\n"
            f"License     : {info['license'] or 'N/A'}\n"
            f"Topics      : {topics}"
        )
    except Exception as e:
        return f"Error: {str(e)}"


def list_files(repo: str, extension: Optional[str] = None) -> str:
    """
    List all files in a GitHub repository, optionally filtered by extension.

    Args:
        repo: e.g. 'tiangolo/fastapi'
        extension: optional filter e.g. '.py', '.ts'
    """
    try:
        info = get_repo_info(repo)
        branch = info.get("default_branch", "main") if "error" not in info else "main"
        files = get_repo_tree(repo, branch)

        if not files:
            return f"Could not fetch file tree for '{repo}'"

        if extension:
            ext = extension if extension.startswith(".") else f".{extension}"
            files = [f for f in files if f.endswith(ext)]

        total = len(files)
        shown = files[:50]
        lines = [f"Files in '{repo}' ({total} total):\n"]
        lines.extend([f"  {f}" for f in shown])
        if total > 50:
            lines.append(f"\n  ... and {total - 50} more")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"