import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import run_agent
from src.tools import parse_repo
from src.compare import compare_with_readme

load_dotenv()

app = FastAPI(
    title="repo-navigator",
    description="Understand any GitHub codebase without reading the docs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyseRequest(BaseModel):
    repo_url: str
    compare: bool = False

class AnalyseResponse(BaseModel):
    repo: str
    report: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyse", response_model=AnalyseResponse)
def analyse(req: AnalyseRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    try:
        owner, repo_name = parse_repo(req.repo_url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid GitHub repo URL")

    report = run_agent(req.repo_url)

    if req.compare:
        comparison = compare_with_readme(owner, repo_name, report)
        report = report + comparison

    return AnalyseResponse(repo=f"{owner}/{repo_name}", report=report)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
