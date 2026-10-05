import asyncio
import json
from pathlib import Path

from mcp import Client, StdioServerParameters

from pdf_parser import extract_text_from_pdf


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXECUTABLE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
DATA_DIR = PROJECT_ROOT / "data"


JOB_DESCRIPTION = """
AI Engineer Intern

We are looking for an AI Engineer Intern to work on
LLM applications, AI agents, and backend services.

Requirements:

- Python
- JavaScript
- Node.js
- FastAPI
- Docker
- MCP
- LLM
- Statistics

Responsibilities:

- Build AI-powered applications.
- Develop APIs using Python and FastAPI.
- Work with LLMs and AI agents.
- Build MCP tools and workflows.
- Work with Docker-based development environments.
"""


async def main():

    # =================================================
    # 1. Find resume
    # =================================================

    pdf_files = list(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No resume PDF found.")
        return

    resume_path = pdf_files[0]

    print("Resume:")
    print(resume_path.name)
    print()

    # =================================================
    # 2. Extract resume text
    # =================================================

    resume_text = extract_text_from_pdf(
        str(resume_path)
    )

    print("Resume PDF extracted successfully.")
    print(
        f"Resume characters: {len(resume_text)}"
    )
    print()

    # =================================================
    # 3. Start MCP server
    # =================================================

    server_params = StdioServerParameters(
        command=str(PYTHON_EXECUTABLE),
        args=["-m", "src.server"],
        cwd=str(PROJECT_ROOT),
    )

    print("Connecting to MCP server...")

    async with Client(server_params) as client:

        print("Connected successfully!")
        print()

        # =================================================
        # 4. Match resume with job
        # =================================================

        print("Step 1: Matching resume with job...")
        print()

        match_response = await client.call_tool(
            "match_job",
            arguments={
                "resume_text": resume_text,
                "job_description": JOB_DESCRIPTION,
            },
        )

        if match_response.is_error:
            print("match_job failed:")
            print(match_response.content)
            return

        match_result = json.loads(
            match_response.content[0].text
        )

        # =================================================
        # 5. Display matching result
        # =================================================

        print("=" * 60)
        print("JOB MATCHING RESULT")
        print("=" * 60)

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

        print(
            f"Skill Coverage: "
            f"{match_result['matched_skill_count']}/"
            f"{match_result['required_skill_count']}"
        )

        # =================================================
        # 6. Get missing skills
        # =================================================

        missing_skills = match_result[
            "missing_skills"
        ]

        if not missing_skills:

            print()
            print("No skill gaps found!")
            return

        # =================================================
        # 7. Call learning plan tool
        # =================================================

        print()
        print("=" * 60)
        print("Step 2: Generating learning plan...")
        print("=" * 60)
        print()

        learning_response = await client.call_tool(
            "get_learning_plan",
            arguments={
                "missing_skills": missing_skills
            },
        )

        if learning_response.is_error:
            print("get_learning_plan failed:")
            print(learning_response.content)
            return

        learning_plan = json.loads(
            learning_response.content[0].text
        )

        # =================================================
        # 8. Display learning plan
        # =================================================

        print("LEARNING PLAN")
        print("=" * 60)

        print()

        print(json.dumps(
            learning_plan,
            indent=2
        ))


if __name__ == "__main__":
    asyncio.run(main())