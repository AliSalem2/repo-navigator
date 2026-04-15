# repo-navigator

An AI agent that understands any GitHub codebase by reading source code — not documentation.

Point it at a repo. It autonomously explores the codebase, traces call paths, identifies patterns, and produces a structured onboarding document. It deliberately ignores the README so it can tell you what the code *actually* does, not what the author claims it does.

![demo](demo.gif)

```bash
python main.py --repo https://github.com/pallets/click --output onboarding.md --compare
```

---

## Why this exists

READMEs are written by authors who already understand their own code. They skip the gotchas, gloss over internal patterns, and go stale. This agent reads the source directly and surfaces what documentation misses.

The `--compare` flag produces a **README vs reality** section — a diff between what the README claims and what the code actually does.

---

## How it works

The agent runs an autonomous loop powered by Claude's tool use API:

1. **Explore** — lists directory structure to map the codebase shape
2. **Decide** — plans which source files are worth reading based on what it finds
3. **Read** — fetches file contents directly from GitHub API (no cloning required)
4. **Search** — finds where key patterns are defined and used across the codebase
5. **Synthesise** — stops when it has enough signal and writes the onboarding doc

It caps at 14 tool calls by default. On large repos it prioritises depth over breadth — better to understand 6 files well than skim 20.

---

## Output format

Every run produces a structured markdown document:

- **What this repo actually does** — inferred from source, not marketing copy
- **How to run it locally** — extracted from config files and entry points
- **Architecture: how the pieces connect** — traced from actual call paths
- **Core files to read first** — ranked by importance with one-line explanations
- **Key patterns and conventions** — idioms that repeat across the codebase
- **What is undocumented or surprising** — the things no README mentions
- **Where to go next** — deeper areas worth exploring
- **README vs reality** *(with `--compare`)* — what the docs miss or get wrong

---

## Setup

```bash
git clone https://github.com/your-username/repo-navigator
cd repo-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add your ANTHROPIC_API_KEY to .env
```

**Requirements:**
- Python 3.12+
- Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)
- GitHub token (optional) — increases rate limits from 60 to 5000 req/hour

---

## Usage

**Basic analysis:**
```bash
python main.py --repo https://github.com/owner/repo
```

**Save to file:**
```bash
python main.py --repo https://github.com/owner/repo --output onboarding.md
```

**With README comparison:**
```bash
python main.py --repo https://github.com/owner/repo --output onboarding.md --compare
```

**As an API:**
```bash
python api.py
# POST http://localhost:8080/analyse
# { "repo_url": "https://github.com/owner/repo", "compare": true }
```

---

## API

```http
POST /analyse
Content-Type: application/json

{
  "repo_url": "https://github.com/pallets/click",
  "compare": true
}
```

```http
GET /health
→ { "status": "ok" }
```

---

## Deploy to Cloud Run

```bash
gcloud run deploy repo-navigator \
  --source . \
  --region europe-west1 \
  --set-env-vars ANTHROPIC_API_KEY=your_key \
  --allow-unauthenticated
```

---

## Cost

Each run costs approximately **$0.05–0.20** depending on repo size, using Claude Sonnet. A typical analysis of a medium-sized repo (like `pallets/click`) runs in under 2 minutes.

---

## Tech stack

- **Claude API** — tool use + agentic loop (Anthropic)
- **GitHub API** — file fetching without cloning
- **FastAPI** — REST wrapper for deployment
- **Rich** — terminal output
- **Cloud Run** — serverless deployment target

---

## Project status

Session 1 — core agent loop ✓  
Session 2 — README comparison, context trimming, FastAPI wrapper ✓  
Session 3 — polish, deployment ✓  

Planned: streaming output, private repo support via GitHub App auth, frontend UI
