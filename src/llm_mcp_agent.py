from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from src.client import MCPClient, parse_mcp_json


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY was not found. "
        "Please add your Groq API key to the .env file."
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)

MODEL_NAME = "openai/gpt-oss-120b"


# ============================================================
# GROQ HELPER WITH RETRY
# ============================================================

def ask_groq(
    prompt: str,
    temperature: float = 0.2,
    max_retries: int = 3,
) -> str:
    """
    Send a prompt to Groq with automatic retry handling.

    Retries temporary failures such as:
    - HTTP 503
    - HTTP 429
    - model over capacity
    - temporary internal server errors
    """

    last_error = None

    for attempt in range(1, max_retries + 1):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=temperature,
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError(
                    "Groq returned an empty response."
                )

            return content

        except Exception as error:

            last_error = error

            error_text = str(error).lower()

            temporary_error = (
                "503" in error_text
                or "429" in error_text
                or "over capacity" in error_text
                or "rate limit" in error_text
                or "service unavailable" in error_text
                or "internal server error" in error_text
            )

            # Non-temporary errors should immediately stop.
            if not temporary_error:
                raise

            # No retries remaining.
            if attempt >= max_retries:
                break

            wait_seconds = 2 ** attempt

            print(
                f"\nGroq temporary error "
                f"(attempt {attempt}/{max_retries})."
            )

            print(
                f"Retrying in {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        "Groq request failed after "
        f"{max_retries} attempts.\n\n"
        f"Last error: {last_error}"
    )


# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_response(
    response: str,
) -> str:
    """
    Remove markdown code fences if Groq returns JSON
    inside ```json ... ``` or ``` ... ```.
    """

    response = response.strip()

    if response.startswith("```"):

        lines = response.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        response = "\n".join(lines).strip()

    return response


# ============================================================
# SAFE JSON PARSER
# ============================================================

def parse_groq_json(
    response: str,
) -> dict:
    """
    Safely parse a JSON response from Groq.
    """

    cleaned = clean_json_response(
        response
    )

    try:

        parsed = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            "Groq returned invalid JSON.\n\n"
            f"Raw response:\n{response}"
        ) from error

    if not isinstance(
        parsed,
        dict,
    ):
        raise RuntimeError(
            "Groq returned JSON, but it was not a JSON object."
        )

    return parsed


# ============================================================
# MCP TOOL DESCRIPTION
# ============================================================

def get_tool_descriptions(
    tools,
) -> list[dict[str, Any]]:
    """
    Convert MCP tool metadata into serializable dictionaries.
    """

    descriptions = []

    for tool in tools.tools:

        descriptions.append(
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.input_schema,
            }
        )

    return descriptions


# ============================================================
# FIND MCP TOOL
# ============================================================

def find_tool(
    tools,
    tool_name: str,
):
    """
    Find one MCP tool by name.
    """

    for tool in tools.tools:

        if tool.name == tool_name:
            return tool

    return None


# ============================================================
# FORMAT TOOL INFORMATION
# ============================================================

def format_tool_information(
    tool_descriptions: list[dict[str, Any]],
) -> str:
    """
    Format MCP tool descriptions for Groq.
    """

    formatted_tools = []

    for tool in tool_descriptions:

        formatted_tools.append(
            json.dumps(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"],
                },
                indent=2,
                default=str,
            )
        )

    return "\n\n".join(
        formatted_tools
    )


# ============================================================
# INITIAL TOOL SELECTION
# ============================================================

def select_initial_tool(
    resume_text: str,
    job_description: str,
    tool_descriptions: list[dict[str, Any]],
) -> str:
    """
    Ask Groq to select the first MCP tool.
    """

    tool_information = format_tool_information(
        tool_descriptions
    )

    prompt = f"""
You are the planning component of an AI Resume & Job Analyzer.

Your task is to select the single most appropriate MCP tool
for the user's current request.

AVAILABLE MCP TOOLS:

{tool_information}

RESUME:

{resume_text}

JOB DESCRIPTION:

{job_description}

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Select exactly one tool.
3. The selected tool MUST exist in the available MCP tools.
4. Do not invent a tool.
5. Prefer match_job when the task requires comparing a resume
   with a job description.
6. Prefer analyze_resume when the task is primarily about
   analyzing the resume itself.
7. Prefer calculate_match_score when the user explicitly
   asks for a score calculation.
8. Prefer get_learning_plan when the task is primarily about
   learning missing skills.
9. Prefer save_analysis only when the user's primary request
   is to save an existing analysis.
10. Do not select list_analyses for a new resume/job analysis.

RETURN EXACTLY:

{{
    "tool_name": "exact_mcp_tool_name",
    "reason": "short reason"
}}
"""

    response = ask_groq(
        prompt
    )

    decision = parse_groq_json(
        response
    )

    tool_name = decision.get(
        "tool_name"
    )

    if not tool_name:

        raise RuntimeError(
            "Groq did not return a tool_name."
        )

    valid_tool_names = {
        tool["name"]
        for tool in tool_descriptions
    }

    if tool_name not in valid_tool_names:

        raise RuntimeError(
            f"Groq selected invalid MCP tool: {tool_name}"
        )

    return tool_name


# ============================================================
# GENERATE TOOL ARGUMENTS
# ============================================================

def generate_tool_arguments(
    tool_name: str,
    tool_schema: dict[str, Any],
    resume_text: str,
    job_description: str,
    workflow_state: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Ask Groq to generate arguments that satisfy
    the selected MCP tool schema.
    """

    previous_results = json.dumps(
        workflow_state,
        indent=2,
        default=str,
    )

    prompt = f"""
You are generating arguments for an MCP tool.

MCP TOOL:

{tool_name}

INPUT SCHEMA:

{json.dumps(tool_schema, indent=2, default=str)}

RESUME:

{resume_text}

JOB DESCRIPTION:

{job_description}

PREVIOUS MCP WORKFLOW RESULTS:

{previous_results}

TASK:

Generate the arguments required by the MCP tool.

RULES:

1. Return ONLY valid JSON.
2. The JSON must follow the MCP input schema.
3. Do not add fields that are not supported by the schema.
4. Use information from the resume, job description,
   and previous MCP results.
5. Do not invent resume facts.
6. If the tool requires missing_skills, use the missing_skills
   returned by the MCP workflow.
7. If the tool requires resume_text, use the supplied resume.
8. If the tool requires job_description, use the supplied
   job description.
9. If the tool requires required_skills or candidate_skills,
   use values already returned by MCP whenever possible.
10. Do not fabricate values.
11. If the tool requires result_json for persistence,
    use the supplied workflow results and final analysis.
12. Do not include fields outside the MCP schema.

RETURN ONLY THE JSON OBJECT.
"""

    response = ask_groq(
        prompt
    )

    arguments = parse_groq_json(
        response
    )

    if not isinstance(
        arguments,
        dict,
    ):

        raise RuntimeError(
            "Generated MCP arguments are not a JSON object."
        )

    return arguments


# ============================================================
# DECIDE NEXT ACTION
# ============================================================

def decide_next_action(
    resume_text: str,
    job_description: str,
    tool_descriptions: list[dict[str, Any]],
    workflow_state: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Ask Groq whether another MCP tool should be called.
    """

    tool_information = format_tool_information(
        tool_descriptions
    )

    workflow_information = json.dumps(
        workflow_state,
        indent=2,
        default=str,
    )

    prompt = f"""
You are the controller of an AI Resume & Job Analyzer MCP agent.

The agent can call MCP tools and inspect their results.

AVAILABLE MCP TOOLS:

{tool_information}

RESUME:

{resume_text}

JOB DESCRIPTION:

{job_description}

CURRENT WORKFLOW RESULTS:

{workflow_information}

Your job is to decide what the agent should do NEXT.

You have exactly two possible actions:

1. call_tool
2. final

Use "call_tool" if another MCP tool would provide useful
information required to answer the user's task.

Use "final" if the available MCP results are sufficient
to produce the final answer.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Never invent a tool.
3. tool_name must be one of the available MCP tools.
4. Do not repeatedly call the same tool.
5. For a resume/job matching task:
   - match_job should normally be called first.
   - if match_job identifies missing skills and a learning
     roadmap would be useful, get_learning_plan may be called.
6. calculate_match_score should only be used when its inputs
   are available and the calculation is actually useful.
7. analyze_resume should only be called if resume-specific
   information is needed.
8. save_analysis is NOT required as a reasoning step because
   completed analyses are automatically persisted after the
   final response.
9. list_analyses is NOT required for the current analysis.
10. Do not call tools unnecessarily.
11. Stop once enough information exists for a grounded answer.

RETURN EXACTLY ONE OF THESE FORMATS:

{{
    "action": "call_tool",
    "tool_name": "exact_mcp_tool_name",
    "reason": "short reason"
}}

OR:

{{
    "action": "final",
    "reason": "short reason"
}}
"""

    response = ask_groq(
        prompt
    )

    decision = parse_groq_json(
        response
    )

    action = decision.get(
        "action"
    )

    if action not in {
        "call_tool",
        "final",
    }:

        raise RuntimeError(
            f"Invalid agent action: {action}"
        )

    if action == "call_tool":

        tool_name = decision.get(
            "tool_name"
        )

        valid_tool_names = {
            tool["name"]
            for tool in tool_descriptions
        }

        if tool_name not in valid_tool_names:

            raise RuntimeError(
                f"Agent selected invalid MCP tool: {tool_name}"
            )

    return decision


# ============================================================
# FINAL GROQ RESPONSE
# ============================================================

def generate_final_response(
    resume_text: str,
    job_description: str,
    workflow_state: list[dict[str, Any]],
) -> str:
    """
    Generate the final user-facing analysis.

    MCP results are treated as the source of truth.
    """

    workflow_information = json.dumps(
        workflow_state,
        indent=2,
        default=str,
    )

    prompt = f"""
You are the final response generator for an AI Resume &
Job Analyzer.

The MCP workflow has already completed.

Your answer MUST be based only on the supplied resume,
job description, and MCP results.

RESUME:

{resume_text}

JOB DESCRIPTION:

{job_description}

MCP WORKFLOW RESULTS:

{workflow_information}

STRICT GROUNDING RULES:

1. MCP results are the source of truth for match scores,
   matched skills, missing skills, evidence, and learning
   priorities.

2. Do NOT change the MCP match score.

3. Do NOT invent skills, projects, employment, education,
   certifications, technologies, or experience.

4. If a skill appears in matched_skills, say that it was
   detected in the resume.

5. If a skill appears in missing_skills, say that it was
   not detected in the resume.

6. Do not claim that a missing skill was "never used".
   Only state that it was not detected in the supplied resume.

7. Use learning actions from the MCP learning-plan result.

8. Do not invent learning actions.

9. Do not make hiring predictions.

10. Do not claim that the candidate will definitely get or
    not get the job.

11. Do not introduce facts that are absent from the sources.

12. Keep the response professional and concise.

FORMAT:

## 1. Overall Suitability

Give the MCP match score and matched/required skill count.

## 2. Current Strengths

List the matched skills.

## 3. Missing Skills

List the missing skills.

## 4. Learning Priority

Use the MCP learning plan if one exists.

## 5. Final Recommendation

Give a factual recommendation based only on the MCP results.

RETURN ONLY THE FINAL RESPONSE.
"""

    return ask_groq(
        prompt
    )


# ============================================================
# JOB TITLE EXTRACTION
# ============================================================

def extract_job_title(
    job_description: str,
) -> str:
    """
    Extract a simple job title from the job description.

    This is only used as a history label.
    It does not affect the analysis.
    """

    lines = [
        line.strip()
        for line in job_description.splitlines()
        if line.strip()
    ]

    title_keywords = (
        "engineer",
        "developer",
        "scientist",
        "analyst",
        "intern",
        "manager",
        "consultant",
        "specialist",
        "architect",
        "researcher",
        "designer",
    )

    # First look for a title-like line.
    for line in lines[:20]:

        cleaned = (
            line
            .replace("#", "")
            .replace("*", "")
            .strip()
        )

        lower_line = cleaned.lower()

        if any(
            keyword in lower_line
            for keyword in title_keywords
        ):

            if len(cleaned) <= 120:
                return cleaned

    # Then look for explicit labels.
    for line in lines[:20]:

        lower_line = line.lower()

        if (
            lower_line.startswith("position:")
            or lower_line.startswith("role:")
            or lower_line.startswith("job title:")
            or lower_line.startswith("title:")
        ):

            return line.split(
                ":",
                1
            )[1].strip()

    return "Job Analysis"


# ============================================================
# SAVE COMPLETED ANALYSIS
# ============================================================

async def save_completed_analysis(
    mcp_client: MCPClient,
    resume_text: str,
    job_description: str,
    match_result: dict[str, Any],
    learning_plan: dict[str, Any],
    final_response: str,
    workflow_state: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Persist a completed analysis through the existing
    save_analysis MCP tool.

    Persistence happens AFTER the analysis is complete.
    """

    job_title = extract_job_title(
        job_description
    )

    result_payload = {
        "resume_text": resume_text,
        "job_description": job_description,
        "match_result": match_result,
        "learning_plan": learning_plan,
        "final_response": final_response,
        "workflow": workflow_state,
    }

    result_json = json.dumps(
        result_payload,
        indent=2,
        default=str,
    )

    print(
        "\n[SAVE STEP] Saving completed analysis..."
    )

    try:

        save_result = await mcp_client.call_tool(
            "save_analysis",
            arguments={
                "job_title": job_title,
                "result_json": result_json,
                "db_path": "data/analyses.sqlite3",
            },
        )

        parsed_save_result = parse_mcp_json(
            save_result
        )

        print(
            "\nAnalysis save result:"
        )

        print(
            json.dumps(
                parsed_save_result,
                indent=2,
                default=str,
            )
        )

        return {
            "success": True,
            "job_title": job_title,
            "result": parsed_save_result,
        }

    except Exception as error:

        print(
            "\nWARNING: Analysis could not be saved."
        )

        print(
            f"Reason: {error}"
        )

        # The analysis itself remains successful.
        return {
            "success": False,
            "job_title": job_title,
            "error": str(error),
        }


# ============================================================
# DYNAMIC AGENT
# ============================================================

async def run_agent(
    resume_text: str,
    job_description: str,
    max_steps: int = 5,
) -> dict[str, Any]:
    """
    Run the complete AI + MCP dynamic workflow.

    Workflow:

        Streamlit
            ↓
        Groq
            ↓
        MCP tool selection
            ↓
        MCP Client
            ↓
        MCP Server
            ↓
        MCP result
            ↓
        Groq next-action decision
            ↓
        Optional additional MCP tool
            ↓
        Groq final response
            ↓
        save_analysis MCP tool
            ↓
        Streamlit
    """

    print(
        "=" * 70
    )

    print(
        "AI + MCP DYNAMIC AGENT"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not resume_text.strip():

        raise ValueError(
            "Resume text is empty."
        )

    if not job_description.strip():

        raise ValueError(
            "Job description is empty."
        )

    if max_steps < 1:

        raise ValueError(
            "max_steps must be at least 1."
        )

    # ========================================================
    # CONNECT MCP
    # ========================================================

    async with MCPClient() as mcp_client:

        # ----------------------------------------------------
        # DISCOVER MCP TOOLS
        # ----------------------------------------------------

        tools = await mcp_client.list_tools()

        tool_descriptions = get_tool_descriptions(
            tools
        )

        print(
            "\nAvailable MCP tools:"
        )

        for tool in tool_descriptions:

            print(
                f"- {tool['name']}"
            )

        available_tool_names = {
            tool["name"]
            for tool in tool_descriptions
        }

        if "save_analysis" not in available_tool_names:

            raise RuntimeError(
                "Required MCP tool 'save_analysis' "
                "was not found."
            )

        # ====================================================
        # WORKFLOW STATE
        # ====================================================

        workflow_state: list[dict[str, Any]] = []

        called_tools: set[str] = set()

        # ====================================================
        # INITIAL TOOL SELECTION
        # ====================================================

        print(
            "\n[STEP 1] Asking Groq to select the initial MCP tool..."
        )

        initial_tool = select_initial_tool(
            resume_text=resume_text,
            job_description=job_description,
            tool_descriptions=tool_descriptions,
        )

        print(
            f"Selected tool: {initial_tool}"
        )

        current_tool = initial_tool

        # ====================================================
        # DYNAMIC LOOP
        # ====================================================

        for step in range(
            1,
            max_steps + 1,
        ):

            print(
                f"\n[AGENT STEP {step}]"
            )

            # ------------------------------------------------
            # PREVENT REPEATED TOOL CALLS
            # ------------------------------------------------

            if current_tool in called_tools:

                print(
                    f"Tool '{current_tool}' was already called."
                )

                decision = {
                    "action": "final",
                    "reason": "Tool already used.",
                }

            else:

                # ============================================
                # FIND TOOL
                # ============================================

                tool = find_tool(
                    tools,
                    current_tool,
                )

                if tool is None:

                    raise RuntimeError(
                        f"MCP tool not found: {current_tool}"
                    )

                # ============================================
                # GENERATE ARGUMENTS
                # ============================================

                print(
                    f"Generating arguments for {current_tool}..."
                )

                arguments = generate_tool_arguments(
                    tool_name=current_tool,
                    tool_schema=tool.input_schema,
                    resume_text=resume_text,
                    job_description=job_description,
                    workflow_state=workflow_state,
                )

                print(
                    "\nGenerated arguments:"
                )

                print(
                    json.dumps(
                        arguments,
                        indent=2,
                        default=str,
                    )
                )

                # ============================================
                # CALL MCP TOOL
                # ============================================

                print(
                    f"\nCalling MCP tool: {current_tool}"
                )

                mcp_result = await mcp_client.call_tool(
                    current_tool,
                    arguments=arguments,
                )

                parsed_result = parse_mcp_json(
                    mcp_result
                )

                print(
                    "\nMCP result:"
                )

                print(
                    json.dumps(
                        parsed_result,
                        indent=2,
                        default=str,
                    )
                )

                # ============================================
                # SAVE WORKFLOW STATE
                # ============================================

                workflow_state.append(
                    {
                        "step": step,
                        "tool": current_tool,
                        "arguments": arguments,
                        "result": parsed_result,
                    }
                )

                called_tools.add(
                    current_tool
                )

                # ============================================
                # DECIDE NEXT ACTION
                # ============================================

                if step < max_steps:

                    print(
                        "\nAsking Groq whether another "
                        "MCP tool is required..."
                    )

                    try:

                        decision = decide_next_action(
                            resume_text=resume_text,
                            job_description=job_description,
                            tool_descriptions=tool_descriptions,
                            workflow_state=workflow_state,
                        )

                        print(
                            "Agent decision:"
                        )

                        print(
                            json.dumps(
                                decision,
                                indent=2,
                                default=str,
                            )
                        )

                    except Exception as error:

                        print(
                            "\nWARNING: Groq could not "
                            "determine the next action."
                        )

                        print(
                            f"Reason: {error}"
                        )

                        print(
                            "Using the MCP results "
                            "already collected."
                        )

                        decision = {
                            "action": "final",
                            "reason": (
                                "Groq next-action decision "
                                "failed. Using available "
                                "MCP results."
                            ),
                        }

                else:

                    decision = {
                        "action": "final",
                        "reason": (
                            "Maximum workflow steps reached."
                        ),
                    }

            # ------------------------------------------------
            # FINAL DECISION
            # ------------------------------------------------

            if decision["action"] == "final":

                print(
                    "\nAgent decided that enough "
                    "information is available."
                )

                break

            # ------------------------------------------------
            # NEXT MCP TOOL
            # ------------------------------------------------

            next_tool = decision.get(
                "tool_name"
            )

            if not next_tool:

                raise RuntimeError(
                    "Agent requested call_tool but did not "
                    "provide a tool_name."
                )

            if next_tool in called_tools:

                print(
                    f"Tool '{next_tool}' has already been called."
                )

                break

            current_tool = next_tool

        # ====================================================
        # SAFETY CHECK
        # ====================================================

        if not workflow_state:

            raise RuntimeError(
                "The MCP agent completed without calling "
                "any MCP tool."
            )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        print(
            "\n[FINAL STEP] Generating final AI response..."
        )

        try:

            final_response = generate_final_response(
                resume_text=resume_text,
                job_description=job_description,
                workflow_state=workflow_state,
            )

        except Exception as error:

            print(
                "\nWARNING: Groq final response generation failed."
            )

            print(
                f"Reason: {error}"
            )

            # Preserve the MCP data even if Groq has
            # a temporary outage during final generation.
            final_response = (
                "The MCP analysis completed successfully, "
                "but the AI-generated summary could not be "
                "generated because the Groq service was "
                "temporarily unavailable.\n\n"
                "Please review the MCP workflow results below."
            )

        print(
            "\n" + "=" * 70
        )

        print(
            "FINAL AI RESPONSE"
        )

        print(
            "=" * 70
        )

        print(
            final_response
        )

        # ====================================================
        # EXTRACT COMMON RESULTS
        # ====================================================

        match_result: dict[str, Any] = {}

        learning_plan: dict[str, Any] = {}

        selected_tool = (
            workflow_state[0]["tool"]
            if workflow_state
            else initial_tool
        )

        # ----------------------------------------------------
        # FIND MATCH JOB RESULT
        # ----------------------------------------------------

        for workflow_item in workflow_state:

            if workflow_item["tool"] == "match_job":

                match_result = workflow_item[
                    "result"
                ]

                break

        # ----------------------------------------------------
        # FIND LEARNING PLAN RESULT
        # ----------------------------------------------------

        for workflow_item in workflow_state:

            if workflow_item["tool"] == "get_learning_plan":

                learning_plan = workflow_item[
                    "result"
                ]

                break

        # ====================================================
        # AUTOMATIC PERSISTENCE
        # ====================================================

        save_status = await save_completed_analysis(
            mcp_client=mcp_client,
            resume_text=resume_text,
            job_description=job_description,
            match_result=match_result,
            learning_plan=learning_plan,
            final_response=final_response,
            workflow_state=workflow_state,
        )

        # ====================================================
        # RETURN RESULT TO STREAMLIT
        # ====================================================

        return {
            "selected_tool": selected_tool,
            "match_result": match_result,
            "learning_plan": learning_plan,
            "final_response": final_response,
            "workflow": workflow_state,
            "save_status": save_status,
        }


# ============================================================
# TEST MAIN
# ============================================================

async def main():
    """
    Standalone test for the dynamic agent.

    Run:

        python -m src.llm_mcp_agent
    """

    resume_text = """
Python developer with experience in FastAPI,
Machine Learning, SQL, PostgreSQL, LangChain,
LLM, RAG, React, TensorFlow and Git.
"""

    job_description = """
We are hiring an AI Engineer Intern.

Requirements:

Python
JavaScript
Node.js
FastAPI
Docker
MCP
LLM
Statistics
"""

    result = await run_agent(
        resume_text=resume_text,
        job_description=job_description,
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "RETURNED AGENT RESULT"
    )

    print(
        "=" * 70
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())