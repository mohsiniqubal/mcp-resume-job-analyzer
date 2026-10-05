import asyncio
import json
from pathlib import Path

from mcp import Client, StdioServerParameters

from pdf_parser import extract_text_from_pdf


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXECUTABLE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
DATA_DIR = PROJECT_ROOT / "data"


async def main():

    # -------------------------------------------------
    # 1. Find resume PDF
    # -------------------------------------------------

    pdf_files = list(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF found in data folder.")
        return

    if len(pdf_files) > 1:
        print("Multiple PDFs found:")

        for pdf in pdf_files:
            print(f"- {pdf.name}")

        print()
        print("Keep only the resume PDF for this test.")
        return

    pdf_path = pdf_files[0]

    print("Resume:")
    print(pdf_path.name)
    print()

    # -------------------------------------------------
    # 2. Extract PDF text
    # -------------------------------------------------

    resume_text = extract_text_from_pdf(str(pdf_path))

    print("PDF text extracted successfully.")
    print(f"Characters extracted: {len(resume_text)}")
    print()

    # -------------------------------------------------
    # 3. Connect to MCP server
    # -------------------------------------------------

    server_params = StdioServerParameters(
        command=str(PYTHON_EXECUTABLE),
        args=["-m", "src.server"],
        cwd=str(PROJECT_ROOT),
    )

    print("Connecting to MCP server...")

    async with Client(server_params) as client:

        print("Connected successfully!")
        print()

        # -------------------------------------------------
        # 4. Call analyze_resume MCP tool
        # -------------------------------------------------

        print("Calling analyze_resume...")
        print()

        result = await client.call_tool(
            "analyze_resume",
            arguments={
                "resume_text": resume_text
            },
        )

        # -------------------------------------------------
        # 5. Check result
        # -------------------------------------------------

        if result.is_error:

            print("MCP tool returned an error:")
            print(result.content)
            return

        # -------------------------------------------------
        # 6. Parse JSON response
        # -------------------------------------------------

        response_text = result.content[0].text

        analysis = json.loads(response_text)

        # -------------------------------------------------
        # 7. Display analysis
        # -------------------------------------------------

        print("RESUME ANALYSIS")
        print("=" * 60)

        print()

        print("Technical Skills:")

        for skill in analysis.get("skills", []):
            print(f"  ✓ {skill}")

        print()

        print(f"Skill Count: {analysis.get('skill_count', 0)}")

        print()

        print("Sections Detected:")

        sections = {
            "Education": analysis.get("education_present"),
            "Experience": analysis.get("experience_present"),
            "Projects": analysis.get("projects_present"),
            "Certifications": analysis.get("certifications_present"),
        }

        for section, present in sections.items():

            status = "Found" if present else "Not Found"

            print(f"  {section}: {status}")


if __name__ == "__main__":
    asyncio.run(main())