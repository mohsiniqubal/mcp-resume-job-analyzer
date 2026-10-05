import asyncio

from src.client import run_mcp_analysis
from src.groq_client import generate_job_analysis


# ============================================================
# TEST DATA
# ============================================================

RESUME_TEXT = """
Python developer with experience in FastAPI,
Machine Learning, SQL, PostgreSQL, LangChain,
LLM, RAG, React, TensorFlow and Git.
"""


JOB_DESCRIPTION = """
AI Engineer Intern

Requirements:

Python
JavaScript
Node.js
FastAPI
Docker
MCP
LLM
Statistics

Responsibilities:

Build AI applications.
Develop MCP tools.
Work with LLMs.
Build APIs using FastAPI.
"""


# ============================================================
# MAIN
# ============================================================

async def main():

    print("=" * 60)
    print("MCP + GROQ TEST")
    print("=" * 60)

    print()
    print("Step 1: Running MCP analysis...")
    print()

    result = await run_mcp_analysis(
        RESUME_TEXT,
        JOB_DESCRIPTION,
    )

    match_result = result["match_result"]

    learning_plan = result["learning_plan"]

    print("MCP analysis completed.")
    print()

    print(
        f"Match Score: "
        f"{match_result['match_score']}%"
    )

    print()

    print("Matched Skills:")

    for skill in match_result["matched_skills"]:
        print(f"  ✓ {skill}")

    print()

    print("Missing Skills:")

    for skill in match_result["missing_skills"]:
        print(f"  ✗ {skill}")

    print()

    # ========================================================
    # SEND MCP RESULTS TO GROQ
    # ========================================================

    print("=" * 60)
    print("Step 2: Sending MCP results to Groq...")
    print("=" * 60)

    print()

    ai_response = generate_job_analysis(
        match_result,
        learning_plan,
    )

    print("GROQ AI ANALYSIS")
    print("=" * 60)

    print(ai_response)

    print()

    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())