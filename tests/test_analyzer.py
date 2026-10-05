from src.analyzer import (
    analyze_resume,
    calculate_match_score,
    get_learning_plan,
    match_job,
)


def test_extract_resume_skills():
    result = analyze_resume("Python SQL FastAPI LangChain RAG Docker")
    assert "python" in result["skills"]
    assert "fastapi" in result["skills"]
    assert "rag" in result["skills"]


def test_match_job():
    result = match_job(
        "Python FastAPI LangChain",
        "Python FastAPI Docker MCP"
    )
    assert result["match_score"] == 50.0
    assert result["matched_skills"] == ["fastapi", "python"]
    assert "docker" in result["missing_skills"]
    assert "mcp" in result["missing_skills"]


def test_score():
    result = calculate_match_score(
        ["Python", "MCP", "Docker"],
        ["Python", "MCP"]
    )
    assert result["score"] == 66.67


def test_learning_plan_prioritizes_mcp():
    result = get_learning_plan(["Docker", "MCP", "Node.js"])
    assert result["priority_plan"][0]["skill"] == "MCP"
