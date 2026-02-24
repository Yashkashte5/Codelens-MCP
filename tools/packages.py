"""
Package tools: search_packages, get_package_info, check_dependencies, find_alternatives
Uses the Libraries.io API + GitHub API for package file fetching.
"""

import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from datetime import datetime, timezone

LIBRARIES_IO_KEY = os.getenv("LIBRARIES_IO_API_KEY", "")
LIBRARIES_IO_BASE = "https://libraries.io/api"

PACKAGE_FILES = {
    "package.json": "npm",
    "requirements.txt": "pypi",
    "go.mod": "go",
    "Cargo.toml": "cargo",
    "pom.xml": "maven",
    "Gemfile": "rubygems",
    "composer.json": "packagist",
}


def _api_get(endpoint: str, params: dict = {}) -> dict | list | None:
    if not LIBRARIES_IO_KEY:
        return {"error": "LIBRARIES_IO_API_KEY not set"}
    try:
        params["api_key"] = LIBRARIES_IO_KEY
        resp = requests.get(f"{LIBRARIES_IO_BASE}/{endpoint}", params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"API returned {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def _months_since(date_str: str) -> int | None:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return int((now - dt).days / 30)
    except Exception:
        return None


def search_packages(query: str, language: Optional[str] = None) -> str:
    """Search for packages on Libraries.io."""
    params = {"q": query}
    if language:
        params["platforms"] = language

    data = _api_get("search", params)
    if isinstance(data, dict) and "error" in data:
        return f"Error: {data['error']}"
    if not data:
        return f"No packages found for '{query}'."

    lines = [f"Package search results for '{query}':\n"]
    for pkg in data[:8]:
        months = _months_since(pkg.get("latest_release_published_at", ""))
        age_str = f"{months} months ago" if months is not None else "unknown"
        lines.append(
            f"  {pkg.get('name')} ({pkg.get('platform', '?')})\n"
            f"    Stars: {pkg.get('stars', 0):,} | Last release: {age_str}\n"
            f"    {pkg.get('description', 'N/A')[:80]}"
        )
    return "\n".join(lines)


def get_package_info(name: str, platform: str) -> str:
    """Get detailed info about a specific package."""
    data = _api_get(f"{platform}/{name}")
    if isinstance(data, dict) and "error" in data:
        return f"Error: {data['error']}"
    if not data:
        return f"Package '{name}' not found on {platform}."

    months = _months_since(data.get("latest_release_published_at", ""))
    age_str = f"{months} months ago" if months is not None else "unknown"
    deprecated = data.get("deprecated", False)
    unmaintained = months is not None and months > 12

    flags = []
    if deprecated:
        flags.append("DEPRECATED")
    if unmaintained:
        flags.append(f"No release in {months} months")

    return (
        f"Package: {data.get('name')} ({platform})\n"
        f"Description  : {data.get('description', 'N/A')}\n"
        f"Latest ver   : {data.get('latest_release_number', 'N/A')}\n"
        f"Last release : {age_str}\n"
        f"Stars        : {data.get('stars', 0):,}\n"
        f"Forks        : {data.get('forks', 0):,}\n"
        f"Open issues  : {data.get('open_issues', 0):,}\n"
        f"Contributors : {data.get('contributions_count', 0)}\n"
        f"Homepage     : {data.get('homepage', 'N/A')}\n"
        f"Repository   : {data.get('repository_url', 'N/A')}\n"
        + (f"Flags        : {' | '.join(flags)}" if flags else "Status       : Maintained")
    )


def check_dependencies(repo_name: str) -> str:
    """
    Fetch package files directly from GitHub and check each dependency
    against Libraries.io for health/maintenance status.
    """
    try:
        from github import get_package_files
        package_docs = get_package_files(repo_name)

        if not package_docs:
            return (
                f"No package files found in '{repo_name}'.\n"
                f"Supported: {', '.join(PACKAGE_FILES.keys())}"
            )

        all_results = []
        for filename, content in package_docs.items():
            platform = PACKAGE_FILES.get(filename)
            if not platform:
                continue

            packages = _extract_packages(filename, content)
            if not packages:
                continue

            all_results.append(f"\n{filename} ({platform}):")
            packages = packages[:20]

            def fetch_package(pkg_tuple, _platform=platform):
                pkg_name, version = pkg_tuple
                data = _api_get(f"{_platform}/{pkg_name}")
                return pkg_name, version, data

            with ThreadPoolExecutor(max_workers=10) as executor:
                fetch_results = list(executor.map(fetch_package, packages))

            risky, healthy = [], []
            for pkg_name, version, data in fetch_results:
                if isinstance(data, dict) and "error" in data:
                    all_results.append(f"  ? {pkg_name} — could not fetch info")
                    continue

                months = _months_since(data.get("latest_release_published_at", ""))
                deprecated = data.get("deprecated", False)
                contributors = data.get("contributions_count", 0)

                issues = []
                if deprecated:
                    issues.append("DEPRECATED")
                if months is not None and months > 12:
                    issues.append(f"no release in {months}mo")
                if contributors < 2:
                    issues.append("< 2 contributors")

                if issues:
                    risky.append(f"  [!] {pkg_name} {version} — {', '.join(issues)}")
                else:
                    healthy.append(f"  [ok] {pkg_name} {version}")

            all_results.extend(risky)
            all_results.extend(healthy)

        return f"Dependency health check for '{repo_name}':\n" + "\n".join(all_results)

    except Exception as e:
        return f"Error checking dependencies: {str(e)}"


def find_alternatives(package_name: str, language: Optional[str] = None) -> str:
    """Find alternative packages similar to the given one."""
    params = {"q": package_name}
    if language:
        params["platforms"] = language

    data = _api_get("search", params)
    if isinstance(data, dict) and "error" in data:
        return f"Error: {data['error']}"
    if not data:
        return f"No alternatives found for '{package_name}'."

    alternatives = [p for p in data if p.get("name", "").lower() != package_name.lower()]
    alternatives.sort(key=lambda x: x.get("stars", 0), reverse=True)

    lines = [f"Alternatives to '{package_name}':\n"]
    for pkg in alternatives[:6]:
        months = _months_since(pkg.get("latest_release_published_at", ""))
        age_str = f"{months} months ago" if months is not None else "unknown"
        maintained = "Active" if (months is not None and months < 12) else "Outdated"
        lines.append(
            f"  {pkg.get('name')} ({pkg.get('platform', '?')}) — {maintained}\n"
            f"    Stars: {pkg.get('stars', 0):,} | Last release: {age_str}\n"
            f"    {pkg.get('description', '')[:100]}"
        )
    return "\n".join(lines)


def _extract_packages(filename: str, content: str) -> list[tuple[str, str]]:
    """Extract package names and versions from common package file formats."""
    packages = []
    try:
        if filename == "package.json":
            json_start = content.find("{")
            if json_start == -1:
                return []
            data = json.loads(content[json_start:])
            for section in ["dependencies", "devDependencies"]:
                for name, version in data.get(section, {}).items():
                    packages.append((name, version))

        elif filename == "requirements.txt":
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    if "==" in line:
                        name, version = line.split("==", 1)
                        packages.append((name.strip(), f"=={version.strip()}"))
                    elif ">=" in line:
                        name, version = line.split(">=", 1)
                        packages.append((name.strip(), f">={version.strip()}"))
                    else:
                        packages.append((line.strip(), ""))

        elif filename == "Cargo.toml":
            in_deps = False
            for line in content.split("\n"):
                line = line.strip()
                if line in ("[dependencies]", "[dev-dependencies]"):
                    in_deps = True
                elif line.startswith("["):
                    in_deps = False
                elif in_deps and "=" in line:
                    name, version = line.split("=", 1)
                    packages.append((name.strip(), version.strip().strip('"')))

        elif filename == "go.mod":
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("//") and not line.startswith("module") and not line.startswith("go "):
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append((parts[0], parts[1]))

    except Exception:
        pass
    return packages