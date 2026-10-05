# MCP Resume & Job Analyzer

A portfolio-ready Model Context Protocol (MCP) project that exposes resume/job-analysis capabilities as tools an AI host can call.

## What this project demonstrates

- MCP server development with the current MCP Python SDK v2
- Typed MCP tools and structured outputs
- Resume text/PDF extraction
- Deterministic skill matching and gap analysis
- Job-fit scoring
- Learning-plan generation
- SQLite persistence
- Unit testing
- Docker-ready architecture

## Architecture

```text
User / AI Host
      |
      | MCP
      v
+-----------------------------+
| MCP Resume Job Analyzer     |
|                             |
| analyze_resume              |
| match_job                   |
| calculate_match_score       |
| get_learning_plan           |
| save_analysis               |
+-------------+---------------+
              |
       +------+------+
       |             |
   Analyzer      SQLite DB
```

## Project structure

```text
mcp_resume_job_analyzer/
├── src/
│   ├── __init__.py
│   ├── analyzer.py
│   └── server.py
├── data/
│   ├── sample_resume.txt
│   └── sample_job.txt
├── tests/
│   └── test_analyzer.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

## Setup

Python 3.10+ is required.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the MCP server

```bash
python -m src.server
```

The server uses stdio transport, which is suitable for local MCP hosts.

## Test with MCP Inspector

With the MCP CLI installed:

```bash
uv run mcp dev src/server.py
```

Then inspect the exposed tools.

## Available MCP tools

### `analyze_resume`

Extracts known skills, education, experience, projects and certifications from supplied resume text.

### `match_job`

Compares a resume against a job description and returns matched skills, missing skills and evidence.

### `calculate_match_score`

Calculates a transparent skill-based match score.

### `get_learning_plan`

Creates a prioritized learning plan from missing skills.

### `save_analysis`

Persists an analysis result into SQLite.

## Example tool flow

```text
1. analyze_resume(resume_text)
2. match_job(resume_text, job_description)
3. calculate_match_score(...)
4. get_learning_plan(missing_skills)
5. save_analysis(...)
```

## Example result

```json
{
  "match_score": 72.0,
  "matched_skills": ["Python", "FastAPI", "LLM", "RAG"],
  "missing_skills": ["MCP", "Docker", "Node.js"],
  "recommendations": [
    "Build an MCP server",
    "Learn Docker fundamentals",
    "Learn Node.js basics"
  ]
}
```

## Next phases

- Phase 2: connect an LLM and build an MCP client/agent
- Phase 3: add FastAPI gateway
- Phase 4: Docker Compose
- Phase 5: evaluation and logging
- Phase 6: GitHub polish + demo screenshots

## Resume positioning

Suggested project title:

**MCP-Based AI Resume & Job Analyzer | Python, MCP, FastAPI, LLM, Docker**

Do not claim LLM integration or Docker deployment on the resume until those phases are actually implemented and tested.
