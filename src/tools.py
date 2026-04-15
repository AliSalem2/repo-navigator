import requests
import base64
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GITHUB_API = "https://api.github.com"

def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def _headers() -> dict:
    token = os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h

def _get(url: str, params: dict = None) -> requests.Response:
    session = _session()
    for attempt in range(4):
        try:
            return session.get(url, headers=_headers(), params=params, timeout=15)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < 3:
                wait = 5 * (attempt + 1)
                time.sleep(wait)
            else:
                raise

def parse_repo(repo_url: str) -> tuple:
    url = repo_url.rstrip("/").replace("https://github.com/", "")
    parts = url.split("/")
    return parts[0], parts[1]

def list_directory(owner: str, repo: str, path: str = "") -> dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    r = _get(url)
    if r.status_code != 200:
        return {"error": f"Could not list path '{path}': {r.status_code}"}
    items = r.json()
    if not isinstance(items, list):
        return {"error": f"Path '{path}' is a file, not a directory"}
    result = []
    for item in items:
        result.append({
            "name": item["name"],
            "type": item["type"],
            "path": item["path"],
            "size": item.get("size", 0),
        })
    return {"path": path or "/", "items": result}

def read_file(owner: str, repo: str, path: str) -> dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    r = _get(url)
    if r.status_code != 200:
        return {"error": f"Could not read file '{path}': {r.status_code}"}
    data = r.json()
    if data.get("type") != "file":
        return {"error": f"'{path}' is not a file"}
    size = data.get("size", 0)
    if size > 50000:
        return {"error": f"File '{path}' is too large ({size} bytes). Skip it."}
    try:
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        lines = content.splitlines()
        # if len(lines) > 300:
        #     content = "\n".join(lines[:300]) + f"\n\n[truncated — {len(lines)} total lines]" ## Older line with more cost but great quality
        if len(lines) > 150:
            content = "\n".join(lines[:150]) + f"\n\n[truncated — {len(lines)} total lines]"
        return {"path": path, "content": content}
    except Exception as e:
        return {"error": f"Could not decode '{path}': {str(e)}"}

def search_code(owner: str, repo: str, query: str) -> dict:
    url = f"{GITHUB_API}/search/code"
    params = {"q": f"{query} repo:{owner}/{repo}", "per_page": 8}
    r = _get(url, params=params)
    if r.status_code == 403:
        return {"error": "Search rate limit hit. Skip this tool for now."}
    if r.status_code != 200:
        return {"error": f"Search failed: {r.status_code}"}
    items = r.json().get("items", [])
    return {
        "query": query,
        "results": [{"path": i["path"], "url": i["html_url"]} for i in items]
    }

TOOL_DEFINITIONS = [
    {
        "name": "list_directory",
        "description": (
            "List files and folders at a path in the repository. "
            "Use this to understand structure before deciding what to read. "
            "Start at root ('') then go deeper selectively."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list. Empty string for root."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "read_file",
        "description": (
            "Read the source code of a file. "
            "Prefer source files (.py, .ts, .js, .go, .rs) over docs. "
            "Do NOT read README.md, CHANGELOG, LICENSE, or .lock files. "
            "Files over 50kb are skipped automatically."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_code",
        "description": (
            "Search for a keyword across the codebase. "
            "Useful for finding where a pattern is defined or used — "
            "e.g. 'class App', 'def main', 'router', 'Depends'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword or short phrase to search for."}
            },
            "required": ["query"]
        }
    }
]
