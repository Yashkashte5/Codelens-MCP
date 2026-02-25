import re
from typing import Optional
from tools.codebase import ask_repo, repo_info
from tools.packages import check_dependencies, _api_get, _months_since
from github import get_repo_info


def repo_summary(repo: str) -> str:
    """
    High-level summary of any GitHub repo.
    Covers purpose, technologies, structure and dependency health.

    Args:
        repo: GitHub repo e.g. 'tiangolo/fastapi'
    """
    info = repo_info(repo)
    purpose = ask_repo("What is the main purpose and structure of this codebase?", repo)
    deps = check_dependencies(repo)

    return (
        f"Repo Summary: {repo}\n"
        f"{'=' * 40}\n\n"
        f"Info:\n{info}\n\n"
        f"Purpose & Structure:\n{purpose}\n\n"
        f"Dependency Health:\n{deps}"
    )


def audit_repo(repo: str) -> str:
    """
    Full audit of any GitHub repo — no indexing required.
    Returns code overview + dependency health report.

    Args:
        repo: GitHub repo e.g. 'tiangolo/fastapi' or full URL
    """
    repo = repo.strip().rstrip("/")
    if "github.com/" in repo:
        repo = repo.split("github.com/")[-1].replace(".git", "")

    lines = [f"CodeLens Audit: {repo}\n" + "=" * 40]

    lines.append("\nRepo Info:")
    lines.append(repo_info(repo))

    lines.append("\nCodebase Overview:")
    lines.append(ask_repo("What does this codebase do and how is it structured?", repo))

    lines.append("\nDependency Health:")
    lines.append(check_dependencies(repo))

    lines.append("\n" + "=" * 40)
    lines.append("Audit complete.")

    return "\n".join(lines)


# ─── Compare ───────────────────────────────────────────────────────────────────

def _is_repo(name: str) -> bool:
    name = name.strip()
    if "github.com" in name:
        return True
    return bool(re.match(r"^[\w.-]+/[\w.-]+$", name))


def _guess_platform(name: str) -> str:
    data = _api_get("search", {"q": name, "per_page": 1})
    if data and not isinstance(data, dict) and len(data) > 0:
        return data[0].get("platform", "npm").lower()
    return "npm"


def _package_snapshot(name: str, platform: str) -> dict:
    data = _api_get(f"{platform}/{name}")
    if not data or (isinstance(data, dict) and "error" in data):
        return {"error": f"Could not find '{name}' on {platform}"}
    months = _months_since(data.get("latest_release_published_at", ""))
    return {
        "name": data.get("name", name),
        "platform": platform,
        "description": data.get("description", "N/A"),
        "stars": data.get("stars", 0),
        "forks": data.get("forks", 0),
        "open_issues": data.get("open_issues", 0),
        "contributors": data.get("contributions_count", 0),
        "latest_version": data.get("latest_release_number", "N/A"),
        "months_since_release": months,
        "deprecated": data.get("deprecated", False),
        "homepage": data.get("homepage", "N/A"),
    }


def _repo_snapshot(repo: str) -> dict:
    repo = repo.strip()
    if "github.com/" in repo:
        repo = repo.split("github.com/")[-1].strip("/")
    data = get_repo_info(repo)
    if "error" in data:
        return {"error": data["error"]}
    return {
        "name": data.get("name", repo),
        "platform": "github",
        "description": data.get("description", "N/A"),
        "stars": data.get("stars", 0),
        "forks": data.get("forks", 0),
        "open_issues": data.get("open_issues", 0),
        "language": data.get("language", "N/A"),
        "license": data.get("license", "N/A"),
        "topics": data.get("topics", []),
    }


def _format_snapshot(snap: dict) -> str:
    if "error" in snap:
        return f"Error: {snap['error']}"

    lines = [f"{snap['name']} ({snap.get('platform', '?')})"]
    lines.append(f"  Description : {snap.get('description', 'N/A')}")
    lines.append(f"  Stars       : {snap.get('stars', 0):,}")
    lines.append(f"  Forks       : {snap.get('forks', 0):,}")
    lines.append(f"  Open issues : {snap.get('open_issues', 0):,}")

    if snap.get("platform") == "github":
        lines.append(f"  Language    : {snap.get('language', 'N/A')}")
        lines.append(f"  License     : {snap.get('license', 'N/A')}")
        topics = snap.get("topics", [])
        if topics:
            lines.append(f"  Topics      : {', '.join(topics)}")
    else:
        lines.append(f"  Contributors: {snap.get('contributors', 0):,}")
        lines.append(f"  Latest ver  : {snap.get('latest_version', 'N/A')}")
        months = snap.get("months_since_release")
        if months is not None:
            status = "Active" if months < 12 else f"No release in {months} months"
            lines.append(f"  Maintenance : {status}")
        if snap.get("deprecated"):
            lines.append("  Status      : DEPRECATED")
        lines.append(f"  Homepage    : {snap.get('homepage', 'N/A')}")

    return "\n".join(lines)


def compare(item1: str, item2: str, platform: Optional[str] = None) -> str:
    """
    Compare two GitHub repos or packages side by side.
    Auto-detects whether inputs are repos or packages.

    Args:
        item1: repo slug, GitHub URL, or package name e.g. 'express' or 'expressjs/express'
        item2: repo slug, GitHub URL, or package name e.g. 'fastify' or 'fastify/fastify'
        platform: optional platform hint e.g. 'npm', 'pypi', 'cargo'
    """
    if platform:
        snap1 = _package_snapshot(item1, platform)
        snap2 = _package_snapshot(item2, platform)
        mode = "package"
    elif _is_repo(item1) and _is_repo(item2):
        snap1 = _repo_snapshot(item1)
        snap2 = _repo_snapshot(item2)
        mode = "repo"
    elif not _is_repo(item1) and not _is_repo(item2):
        snap1 = _package_snapshot(item1, _guess_platform(item1))
        snap2 = _package_snapshot(item2, _guess_platform(item2))
        mode = "package"
    else:
        snap1 = _repo_snapshot(item1) if _is_repo(item1) else _package_snapshot(item1, _guess_platform(item1))
        snap2 = _repo_snapshot(item2) if _is_repo(item2) else _package_snapshot(item2, _guess_platform(item2))
        mode = "mixed"

    out = [
        f"Comparing: {item1} vs {item2}\n" + "=" * 40,
        _format_snapshot(snap1),
        "─" * 40,
        _format_snapshot(snap2),
        "=" * 40,
    ]

    if "error" not in snap1 and "error" not in snap2:
        winner_stars = item1 if snap1.get("stars", 0) >= snap2.get("stars", 0) else item2
        out.append(f"More popular        : {winner_stars}")
        if mode == "package":
            m1 = snap1.get("months_since_release")
            m2 = snap2.get("months_since_release")
            if m1 is not None and m2 is not None:
                out.append(f"More recently updated: {item1 if m1 <= m2 else item2}")

    return "\n".join(out)