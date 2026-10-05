import os
from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
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

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "openai/gpt-oss-120b"


# ============================================================
# BASIC GROQ FUNCTION
# ============================================================

def ask_groq(prompt: str) -> str:
    """
    Send a prompt to Groq and return the generated response.
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


# ============================================================
# AI CAREER ANALYSIS
# ============================================================

def generate_job_analysis(
    match_result: dict,
    learning_plan: dict,
) -> str:
    """
    Generate a factual career analysis using only the
    structured results returned by the MCP tools.

    The MCP results are treated as the source of truth.
    """

    prompt = f"""
You are a professional AI career analysis assistant.

You are given structured results produced by an
MCP-based resume and job matching system.

The MCP results are the SOURCE OF TRUTH.

Your job is ONLY to explain these results clearly,
professionally, and concisely.

============================================================
STRICT GROUNDING RULES
============================================================

1. Do NOT invent skills.

2. Do NOT invent projects.

3. Do NOT invent work experience.

4. Do NOT invent certifications.

5. Do NOT invent education details.

6. Do NOT claim that the candidate built, deployed,
   fine-tuned, implemented, or used a technology unless
   that information is explicitly present in the supplied
   MCP results.

7. Do NOT change the match score.

8. Do NOT calculate a different match score.

9. Do NOT add skills that are not present in
   matched_skills or missing_skills.

10. Do NOT invent evidence.

11. Use the evidence dictionary exactly as provided.

12. Do NOT make hiring guarantees.

13. Do NOT say that the candidate will definitely get
    or not get the job.

14. Do NOT introduce technologies that are not present
    in the MCP results.

15. Do NOT redefine or explain MCP unless explicitly
    required by the supplied data.

16. If the supplied MCP results do not provide enough
    information to make a statement, say:

    "The available MCP analysis does not provide enough
    evidence to determine this."

17. Keep the response professional, concise, factual,
    and useful to the candidate.

============================================================
MCP MATCH RESULT
============================================================

{match_result}

============================================================
MCP LEARNING PLAN
============================================================

{learning_plan}

============================================================
REQUIRED RESPONSE FORMAT
============================================================

## 1. Overall Suitability

Explain the result using ONLY the MCP match result.

Mention:

- Match score
- Matched skill count
- Required skill count

Use the exact values supplied by MCP.

Do NOT modify or recalculate them.

Example:

"Match score: 55.56%
Matched skill count: 5
Required skill count: 9"

Do not add unsupported conclusions.

---

## 2. Current Strengths

Discuss ONLY the skills listed in:

matched_skills

Do not add any other skills.

For each matched skill:

- If evidence=True, say that the skill was detected
  in the resume.
- If evidence=False, do not describe it as detected.

Use wording such as:

"FastAPI was detected in the resume."

Do NOT say:

"The candidate has demonstrated experience with FastAPI."

Do NOT claim that the candidate built, deployed,
implemented, or worked with a technology unless that
information is explicitly contained in the MCP results.

---

## 3. Missing Skills

Discuss ONLY the skills listed in:

missing_skills

Do not add any additional skills.

Use wording such as:

"Docker was not detected in the resume."

Do NOT claim:

"The candidate has never used Docker."

The MCP analysis only tells us that the skill was not
detected in the supplied resume.

---

## 4. Learning Priority

Use ONLY the skills and actions provided in:

learning_plan

Preserve the priority order.

Do not invent additional learning topics.

For each item, use the skill and action supplied by
the MCP learning plan.

---

## 5. Final Recommendation

Give a short and practical recommendation based strictly
on the MCP results.

The recommendation may mention:

- Match score
- Matched skills
- Missing skills
- Learning plan

When referring to matched skills, say that they were
detected in the resume.

Do NOT use unsupported phrases such as:

- "demonstrates solid foundations"
- "has strong experience"
- "has demonstrated experience"
- "has successfully worked with"
- "is highly experienced"

unless that information is explicitly present in the
MCP results.

Do NOT predict that learning a missing skill will
increase the match score.

Do NOT make hiring predictions.

Do NOT claim that the candidate will get the job.

============================================================
OUTPUT STYLE
============================================================

Use exactly these five sections:

## 1. Overall Suitability

## 2. Current Strengths

## 3. Missing Skills

## 4. Learning Priority

## 5. Final Recommendation

Use short paragraphs and bullet points where appropriate.

Do not repeat the entire MCP JSON.

Do not add unrelated career advice.

Do not introduce skills or technologies that are absent
from the supplied MCP results.

============================================================
FINAL INSTRUCTION
============================================================

Your response must remain completely grounded in the
MCP results provided above.

If information is not present in the MCP results,
do not guess.

If you cannot determine something from the supplied
data, explicitly say that the available MCP analysis
does not provide enough evidence to determine it.
"""

    return ask_groq(prompt)