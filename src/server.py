from __future__ import annotations

import json

from mcp.server.mcpserver import MCPServer

from .analyzer import (
    analyze_resume as analyze_resume_logic,
    calculate_match_score as calculate_match_score_logic,
    get_learning_plan as get_learning_plan_logic,
    match_job as match_job_logic,
    save_analysis as save_analysis_logic,
)

mcp = MCPServer(
    "MCP Resume Job Analyzer",
    description=(
        "MCP tools for resume analysis, job matching, "
        "skill-gap analysis, and persistence."
    ),
    version="0.1.0",
)


# ============================================================
# RESUME ANALYSIS
# ============================================================

@mcp.tool()
def analyze_resume(resume_text: str) -> dict:
    """Analyze a resume and extract normalized technical skills and common sections."""
    return analyze_resume_logic(resume_text)


# ============================================================
# JOB MATCHING
# ============================================================

@mcp.tool()
def match_job(
    resume_text: str,
    job_description: str,
) -> dict:
    """Compare a resume with a job description and return matched and missing skills."""
    return match_job_logic(
        resume_text,
        job_description,
    )


# ============================================================
# MATCH SCORE
# ============================================================

@mcp.tool()
def calculate_match_score(
    required_skills: list[str],
    candidate_skills: list[str],
) -> dict:
    """Calculate a transparent skill-overlap score between 0 and 100."""
    return calculate_match_score_logic(
        required_skills,
        candidate_skills,
    )


# ============================================================
# LEARNING PLAN
# ============================================================

@mcp.tool()
def get_learning_plan(
    missing_skills: list[str],
) -> dict:
    """Generate a prioritized practical learning plan for missing skills."""
    return get_learning_plan_logic(
        missing_skills
    )


# ============================================================
# SAVE ANALYSIS
# ============================================================

@mcp.tool()
def save_analysis(
    job_title: str,
    result_json: str,
    db_path: str = "data/analyses.sqlite3",
) -> dict:
    """Save a completed resume-job analysis into SQLite."""

    result = json.loads(result_json)

    return save_analysis_logic(
        db_path,
        job_title,
        result,
    )


# ============================================================
# LIST ANALYSIS HISTORY
# ============================================================

@mcp.tool()
def list_analyses(
    limit: int = 20,
    db_path: str = "data/analyses.sqlite3",
) -> dict:
    """
    Return previously saved resume-job analyses.

    Results are ordered from newest to oldest.
    """

    from pathlib import Path
    import sqlite3

    database_path = Path(db_path)

    if not database_path.exists():
        return {
            "count": 0,
            "analyses": [],
        }

    connection = sqlite3.connect(
        database_path
    )

    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM analyses
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                max(1, min(limit, 100)),
            ),
        )

        rows = cursor.fetchall()

        analyses = []

        for row in rows:
            analyses.append(
                dict(row)
            )

        return {
            "count": len(analyses),
            "analyses": analyses,
        }

    finally:
        connection.close()


# ============================================================
# MCP RESOURCE
# ============================================================

@mcp.resource("project://skills")
def project_skills() -> str:
    """Return the canonical skill vocabulary used by the analyzer."""

    from .analyzer import SKILL_ALIASES

    return json.dumps(
        sorted(SKILL_ALIASES.keys()),
        indent=2,
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )