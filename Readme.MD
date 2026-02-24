# CodeLens MCP

An MCP server that gives Claude Desktop complete intelligence about any public GitHub repository. Research libraries, compare packages, audit dependencies, and explore codebases through natural conversation.

---

## What it does

Most developers waste time switching between GitHub, npm, PyPI, and documentation tabs just to evaluate a library. CodeLens brings all of that into a single Claude Desktop conversation.

Ask things like:

- *"Is moment.js still worth using?"*
- *"Compare express and fastify for a new node project"*
- *"How does authentication work in tiangolo/fastapi?"*
- *"Are any dependencies in this repo unmaintained?"*
- *"What's a good alternative to axios?"*
- *"Give me a full audit of pallets/flask"*

No indexing. No local models. Every answer is pulled live from GitHub and Libraries.io.

---

## Requirements

- Python 3.11+
- Claude Desktop
- GitHub Personal Access Token (free)
- Libraries.io API Key (free)

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/Yashkashte5/Codelens-MCP
cd Codelens-MCP
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get your API keys

**GitHub Token**
1. Go to github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token, give it a name, check `repo` and `read:org`
3. Copy the token

**Libraries.io Key**
1. Go to [libraries.io/account](https://libraries.io/account)
2. Sign up and copy your API key

### 4. Configure Claude Desktop

Edit your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codelens-mcp": {
      "command": "python",
      "args": ["C:\\path\\to\\Codelens-MCP\\server.py"],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "LIBRARIES_IO_API_KEY": "your_libraries_io_key_here",
        "PYTHONPATH": "C:\\path\\to\\Codelens-MCP"
      }
    }
  }
}
```

Restart Claude Desktop. CodeLens will appear in your connectors.

---

## File Structure

```
Codelens-MCP/
├── server.py        — MCP entry point, all tools registered
├── github.py        — GitHub API client
├── tools/
│   ├── codebase.py  — repo exploration tools
│   ├── packages.py  — Libraries.io package tools
│   └── combined.py  — audit, summary, and compare tools
├── requirements.txt
└── .env
```

---

## Tools

| Tool | Description |
|------|-------------|
| `tool_ask_repo` | Answer natural language questions about any repo |
| `tool_search_code` | Search for specific code patterns in a repo |
| `tool_get_file` | Fetch the full contents of a specific file |
| `tool_repo_info` | Get repo metadata — stars, language, license, topics |
| `tool_list_files` | List all files in a repo, optionally filter by extension |
| `tool_search_packages` | Search Libraries.io for packages |
| `tool_get_package_info` | Get detailed info about a specific package |
| `tool_check_dependencies` | Audit all dependencies in a repo for health and maintenance |
| `tool_find_alternatives` | Find alternatives to a package ranked by stars |
| `tool_repo_summary` | High-level summary of any repo |
| `tool_audit_repo` | Full audit — overview + dependency health in one shot |
| `tool_compare` | Compare two repos or packages side by side |

---

## Example Prompts

**Exploring a repo**
```
How does routing work in tiangolo/fastapi?
List all python files in pallets/flask
Get the file fastapi/routing.py from tiangolo/fastapi
```

**Package research**
```
Is lodash still worth using?
Find alternatives to moment.js on npm
Get info about the httpx package on pypi
```

**Dependency health**
```
Check the dependencies of tiangolo/fastapi
Run a full audit on pallets/flask
```

**Comparing options**
```
Compare express and fastify
Compare requests vs httpx on pypi
Compare django and flask for a new project
```

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Interface | Claude Desktop |
| MCP SDK | `mcp` Python SDK |
| Code search | GitHub Code Search API |
| Package data | Libraries.io API |
| Language | Python 3.11+ |

---

## Limits

- GitHub API: 5,000 requests/hour with a token
- Libraries.io free tier: 60 requests/minute
- Works on public GitHub repos only
