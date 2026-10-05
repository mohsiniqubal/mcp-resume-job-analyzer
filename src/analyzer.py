from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Iterable

SKILL_ALIASES = {
    "python": ["python"],
    "sql": ["sql"],
    "javascript": ["javascript", "js"],
    "node.js": ["node.js", "nodejs", "node js"],
    "fastapi": ["fastapi"],
    "docker": ["docker"],
    "podman": ["podman"],
    "mcp": ["mcp", "model context protocol"],
    "llm": ["llm", "large language model", "large language models"],
    "langchain": ["langchain"],
    "rag": ["rag", "retrieval augmented generation"],
    "postgresql": ["postgresql", "postgres"],
    "sqlite": ["sqlite"],
    "rest api": ["rest api", "restful api"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "xgboost": ["xgboost"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "statistics": ["statistics", "statistical analysis"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "react": ["react", "react.js"],
    "git": ["git", "github"],
}

EDUCATION_TERMS = ["mca", "master of computer application", "b.tech", "btech", "b.e", "bachelor"]
EXPERIENCE_TERMS = ["intern", "experience", "developer", "engineer", "consultant", "analyst"]
PROJECT_TERMS = ["project", "built", "developed", "implemented", "system", "application"]
CERTIFICATION_TERMS = ["certification", "certified", "certificate", "nptel", "iabac"]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_term(text: str, term: str) -> bool:
    # Avoid matching "js" inside unrelated words.
    if len(term) <= 3:
        return bool(re.search(rf"\b{re.escape(term)}\b", text))
    return term in text


def extract_skills(text: str) -> list[str]:
    normalized = normalize(text)
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(contains_term(normalized, alias) for alias in aliases):
            found.append(canonical)
    return sorted(found)


def extract_sections(text: str) -> dict:
    normalized = normalize(text)
    return {
        "education_present": any(term in normalized for term in EDUCATION_TERMS),
        "experience_present": any(term in normalized for term in EXPERIENCE_TERMS),
        "projects_present": any(term in normalized for term in PROJECT_TERMS),
        "certifications_present": any(term in normalized for term in CERTIFICATION_TERMS),
    }


def analyze_resume(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("resume_text cannot be empty")

    skills = extract_skills(text)
    sections = extract_sections(text)

    return {
        "skills": skills,
        "skill_count": len(skills),
        **sections,
    }


def match_job(resume_text: str, job_description: str) -> dict:
    if not resume_text.strip():
        raise ValueError("resume_text cannot be empty")
    if not job_description.strip():
        raise ValueError("job_description cannot be empty")

    resume_skills = set(extract_skills(resume_text))
    required_skills = set(extract_skills(job_description))

    matched = sorted(resume_skills & required_skills)
    missing = sorted(required_skills - resume_skills)

    score = round((len(matched) / len(required_skills)) * 100, 2) if required_skills else 0.0

    evidence = {
        skill: True
        for skill in matched
    }

    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "required_skill_count": len(required_skills),
        "matched_skill_count": len(matched),
        "evidence": evidence,
    }


def calculate_match_score(required_skills: Iterable[str], candidate_skills: Iterable[str]) -> dict:
    required = {normalize(s) for s in required_skills if s.strip()}
    candidate = {normalize(s) for s in candidate_skills if s.strip()}

    matched = sorted(required & candidate)
    missing = sorted(required - candidate)

    score = round((len(matched) / len(required)) * 100, 2) if required else 0.0

    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "required_count": len(required),
    }


def get_learning_plan(missing_skills: Iterable[str]) -> dict:
    missing = [s.strip() for s in missing_skills if s.strip()]

    priority_order = ["mcp", "llm", "rag", "fastapi", "docker", "podman", "node.js", "javascript"]

    def priority(skill: str) -> int:
        key = normalize(skill)
        return priority_order.index(key) if key in priority_order else len(priority_order)

    ordered = sorted(dict.fromkeys(missing), key=priority)

    plan = []
    for skill in ordered:
        key = normalize(skill)
        if key == "mcp":
            action = "Build and test an MCP server with multiple typed tools."
        elif key in {"docker", "podman"}:
            action = "Containerize the project and run the MCP server reproducibly."
        elif key in {"node.js", "javascript"}:
            action = "Build a small Node.js client and call an AI-facing API."
        elif key == "rag":
            action = "Implement retrieval, chunking, embeddings and grounded generation."
        elif key == "llm":
            action = "Practice model prompting, tool calling and structured outputs."
        elif key == "fastapi":
            action = "Create REST endpoints, request validation and health checks."
        else:
            action = f"Study {skill} and implement one small practical feature."

        plan.append({"skill": skill, "action": action})

    return {"priority_plan": plan, "count": len(plan)}


def save_analysis(db_path: str, job_title: str, result: dict) -> dict:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                match_score REAL NOT NULL,
                matched_skills TEXT NOT NULL,
                missing_skills TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO analyses(job_title, match_score, matched_skills, missing_skills)
            VALUES (?, ?, ?, ?)
            """,
            (
                job_title,
                float(result.get("match_score", result.get("score", 0))),
                ", ".join(result.get("matched_skills", [])),
                ", ".join(result.get("missing_skills", [])),
            ),
        )

    return {"saved": True, "database": str(path), "job_title": job_title}
