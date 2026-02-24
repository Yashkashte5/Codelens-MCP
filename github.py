import os
import base64
import requests
from typing import Optional

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_BASE = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _get(endpoint: str, params: dict = {}) -> dict | list | None:
    try:
        resp = requests.get(f"{GITHUB_BASE}/{endpoint}", headers=HEADERS, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"GitHub API {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def extract_search_term(question: str) -> str:
    """Extract the core search term from a natural language question."""
    stopwords = {
        "how", "does", "do", "what", "is", "are", "where", "which", "find",
        "show", "me", "the", "a", "an", "in", "this", "codebase", "repo",
        "repository", "all", "any", "give", "explain", "tell", "work", "works",
        "implemented", "handled", "used", "using", "code", "related"
    }
    words = question.lower().replace("?", "").replace(",", "").split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return " ".join(keywords[:3]) if keywords else question.split()[0]


def search_code(repo: str, query: str, language: Optional[str] = None) -> list[dict]:
    """Search for code in a specific GitHub repo."""
    q = f"{query} repo:{repo}"
    if language:
        q += f" language:{language}"

    data = _get("search/code", {"q": q, "per_page": 8})
    if isinstance(data, dict) and "error" in data:
        return [{"error": data["error"]}]

    results = []
    for item in data.get("items", []):
        results.append({
            "file_path": item.get("path"),
            "repo": item.get("repository", {}).get("full_name"),
            "url": item.get("html_url"),
            "sha": item.get("sha"),
        })
    return results


def get_file_content(repo: str, file_path: str) -> str:
    """Fetch the raw content of a file from a GitHub repo."""
    data = _get(f"repos/{repo}/contents/{file_path}")
    if isinstance(data, dict) and "error" in data:
        return f"Error fetching {file_path}: {data['error']}"
    if isinstance(data, dict) and data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return f"Could not decode {file_path}"


def get_repo_info(repo: str) -> dict:
    """Get basic repo metadata."""
    data = _get(f"repos/{repo}")
    if isinstance(data, dict) and "error" in data:
        return data
    return {
        "name": data.get("full_name"),
        "description": data.get("description"),
        "language": data.get("language"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "default_branch": data.get("default_branch"),
        "topics": data.get("topics", []),
        "license": data.get("license", {}).get("name") if data.get("license") else None,
    }


def get_repo_tree(repo: str, branch: str = "main") -> list[str]:
    """Get all file paths in a repo."""
    data = _get(f"repos/{repo}/git/trees/{branch}", {"recursive": "1"})
    if isinstance(data, dict) and "error" in data:
        data = _get(f"repos/{repo}/git/trees/master", {"recursive": "1"})
    if isinstance(data, dict) and "error" in data:
        return []
    return [item["path"] for item in data.get("tree", []) if item["type"] == "blob"]


def get_package_files(repo: str) -> dict[str, str]:
    """Fetch contents of known package files from the repo."""
    package_files = [
        "package.json", "requirements.txt", "go.mod",
        "Cargo.toml", "pom.xml", "Gemfile", "composer.json"
    ]
    found = {}
    for filename in package_files:
        content = get_file_content(repo, filename)
        if not content.startswith("Error"):
            found[filename] = content
    return found