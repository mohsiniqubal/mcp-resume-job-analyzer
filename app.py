import asyncio

import tempfile

from pathlib import Path

from datetime import datetime

from io import BytesIO



import streamlit as st



from reportlab.lib import colors

from reportlab.lib.enums import TA_CENTER

from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (

    getSampleStyleSheet,

    ParagraphStyle,

)

from reportlab.lib.units import inch

from reportlab.platypus import (

    SimpleDocTemplate,

    Paragraph,

    Spacer,

    Table,

    TableStyle,

)



from src.pdf_parser import extract_text_from_pdf

from src.llm_mcp_agent import run_agent





# ============================================================

# PAGE CONFIG

# ============================================================



st.set_page_config(

    page_title="AI Resume & Job Analyzer",

    page_icon="",

    layout="wide",

    initial_sidebar_state="collapsed",

)





# ============================================================

# GLOBAL CSS

# ============================================================



st.markdown(

    """

<style>



html,

body,

[data-testid="stAppViewContainer"],

[data-testid="stAppViewContainer"] > .main {

    background-color: #f8fafc !important;

}



[data-testid="stHeader"] {

    background-color: #0f172a !important;

}



.block-container {

    max-width: 1450px !important;

    padding-top: 1.8rem !important;

    padding-bottom: 2rem !important;

}





/* ============================================================

   TEXT

\============================================================ */



h1,

h2,

h3,

h4,

h5,

h6 {

    color: #0f172a !important;

    opacity: 1 !important;

}



h1 {

    font-size: 2.35rem !important;

    font-weight: 800 !important;

}



h2 {

    font-size: 1.85rem !important;

    font-weight: 750 !important;

}



h3 {

    font-size: 1.35rem !important;

    font-weight: 700 !important;

}



.stMarkdown p,

.stMarkdown li,

.stMarkdown strong {

    color: #1e293b !important;

    opacity: 1 !important;

}



[data-testid="stCaptionContainer"],

[data-testid="stCaptionContainer"] * {

    color: #475569 !important;

    opacity: 1 !important;

}





/* ============================================================

   INPUTS

\============================================================ */



textarea,

input {

    color: #111827 !important;

    background-color: #ffffff !important;

    font-size: 15px !important;

    opacity: 1 !important;

}



textarea::placeholder,

input::placeholder {

    color: #64748b !important;

    opacity: 1 !important;

}



label,

label * {

    color: #334155 !important;

    opacity: 1 !important;

}





/* ============================================================

   FILE UPLOADER

\============================================================ */



[data-testid="stFileUploaderDropzone"] {

    background-color: #ffffff !important;

    border: 1px dashed #94a3b8 !important;

    border-radius: 10px !important;

}



[data-testid="stFileUploaderDropzone"] * {

    color: #334155 !important;

    opacity: 1 !important;

}



[data-testid="stFileUploaderDropzone"] button {

    background-color: #111827 !important;

    color: #ffffff !important;

}



[data-testid="stFileUploaderDropzone"] button * {

    color: #ffffff !important;

}





/* ============================================================

   MAIN BUTTON

\============================================================ */



div.stButton > button {

    background-color: #2563eb !important;

    color: #ffffff !important;

    border: 1px solid #2563eb !important;

    border-radius: 8px !important;

    min-height: 3rem !important;

    font-size: 15px !important;

    font-weight: 700 !important;

}



div.stButton > button *,

div.stButton > button p,

div.stButton > button span {

    color: #ffffff !important;

}



div.stButton > button:hover {

    background-color: #1d4ed8 !important;

    border-color: #1d4ed8 !important;

}





/* ============================================================

   DOWNLOAD BUTTON

\============================================================ */



div.stDownloadButton > button {

    background-color: #0f172a !important;

    color: #ffffff !important;

    border: 1px solid #0f172a !important;

    border-radius: 8px !important;

    min-height: 3rem !important;

    font-size: 15px !important;

    font-weight: 700 !important;

}



div.stDownloadButton > button *,

div.stDownloadButton > button p,

div.stDownloadButton > button span {

    color: #ffffff !important;

}



div.stDownloadButton > button:hover {

    background-color: #1e293b !important;

    border-color: #1e293b !important;

}





/* ============================================================

   METRICS

\============================================================ */



[data-testid="stMetric"] {

    background-color: #ffffff !important;

    border: 1px solid #e2e8f0 !important;

    border-radius: 10px !important;

    padding: 15px !important;

    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);

}



[data-testid="stMetricLabel"],

[data-testid="stMetricLabel"] * {

    color: #475569 !important;

}



[data-testid="stMetricValue"],

[data-testid="stMetricValue"] * {

    color: #0f172a !important;

    font-weight: 800 !important;

}





/* ============================================================

   CONTAINERS

\============================================================ */



[data-testid="stVerticalBlockBorderWrapper"] {

    background-color: #ffffff !important;

    border: 1px solid #e2e8f0 !important;

    border-radius: 10px !important;

}





/* ============================================================

   EXPANDERS

\============================================================ */



[data-testid="stExpander"] {

    background-color: #ffffff !important;

    border: 1px solid #e2e8f0 !important;

    border-radius: 10px !important;

}



[data-testid="stExpander"] summary,

[data-testid="stExpander"] summary *,

[data-testid="stExpander"] p {

    color: #1e293b !important;

}





/* ============================================================

   ALERTS

\============================================================ */



[data-testid="stAlert"] {

    opacity: 1 !important;

}



[data-testid="stAlert"] p,

[data-testid="stAlert"] span,

[data-testid="stAlert"] div {

    opacity: 1 !important;

}





/* ============================================================

   DIVIDER

\============================================================ */



hr {

    border-color: #cbd5e1 !important;

}





/* ============================================================

   HEADER

\============================================================ */



.main-title {

    text-align: center;

    color: #0f172a;

    font-size: 2.5rem;

    font-weight: 800;

    line-height: 1.2;

    margin: 0;

}



.main-subtitle {

    text-align: center;

    color: #475569;

    font-size: 1rem;

    margin-top: 8px;

    margin-bottom: 20px;

}





/* ============================================================

   FOOTER

\============================================================ */



.footer-text {

    text-align: center;

    color: #64748b;

    font-size: 0.9rem;

    margin-top: 25px;

    margin-bottom: 10px;

}



</style>

""",

    unsafe_allow_html=True,

)





# ============================================================

# SESSION STATE

# ============================================================



if "analysis_result" not in st.session_state:

    st.session_state.analysis_result = None



if "resume_text" not in st.session_state:

    st.session_state.resume_text = ""



if "job_description" not in st.session_state:

    st.session_state.job_description = ""



if "analysis_error" not in st.session_state:

    st.session_state.analysis_error = None



if "pdf_report" not in st.session_state:

    st.session_state.pdf_report = None





# ============================================================

# HEADER

# IMPORTANT:

# Keep these HTML elements on ONE LINE.

# Do not indent HTML inside a Markdown code block.

# ============================================================



st.markdown(

    '<div class="main-title">AI Resume &amp; Job Analyzer</div>',

    unsafe_allow_html=True,

)



st.markdown(

    '<div class="main-subtitle">LLM + MCP powered career intelligence system</div>',

    unsafe_allow_html=True,

)



st.write(

    "Analyze your resume against any job description, "

    "identify matching and missing skills, calculate job "

    "alignment, and generate a prioritized learning roadmap."

)



st.divider()





# ============================================================

# PDF REPORT GENERATOR

# ============================================================



def create_pdf_report(

    match_result,

    learning_plan,

    final_response,

    resume_text,

    job_description,

    selected_tool,

    evidence,

):



    buffer = BytesIO()



    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=45,

        leftMargin=45,

        topMargin=45,

        bottomMargin=45,

        title="AI Resume & Job Analysis Report",

        author="Mohsin",

    )



    styles = getSampleStyleSheet()



    title_style = ParagraphStyle(

        "ReportTitle",

        parent=styles["Title"],

        fontName="Helvetica-Bold",

        fontSize=20,

        leading=25,

        alignment=TA_CENTER,

        textColor=colors.HexColor("#0f172a"),

        spaceAfter=10,

    )



    subtitle_style = ParagraphStyle(

        "ReportSubtitle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=10,

        leading=14,

        alignment=TA_CENTER,

        textColor=colors.HexColor("#475569"),

        spaceAfter=15,

    )



    heading_style = ParagraphStyle(

        "ReportHeading",

        parent=styles["Heading2"],

        fontName="Helvetica-Bold",

        fontSize=14,

        leading=18,

        textColor=colors.HexColor("#0f172a"),

        spaceBefore=15,

        spaceAfter=8,

    )



    subheading_style = ParagraphStyle(

        "ReportSubheading",

        parent=styles["Heading3"],

        fontName="Helvetica-Bold",

        fontSize=11,

        leading=14,

        textColor=colors.HexColor("#1e293b"),

        spaceBefore=8,

        spaceAfter=5,

    )



    normal_style = ParagraphStyle(

        "ReportNormal",

        parent=styles["BodyText"],

        fontName="Helvetica",

        fontSize=9.5,

        leading=14,

        textColor=colors.HexColor("#334155"),

        spaceAfter=6,

    )



    small_style = ParagraphStyle(

        "ReportSmall",

        parent=styles["BodyText"],

        fontName="Helvetica",

        fontSize=8,

        leading=11,

        textColor=colors.HexColor("#64748b"),

    )



    bullet_style = ParagraphStyle(

        "ReportBullet",

        parent=normal_style,

        leftIndent=12,

        firstLineIndent=-8,

        spaceAfter=4,

    )



    story = []



    match_score = match_result.get(

        "match_score",

        0,

    )



    matched_skills = match_result.get(

        "matched_skills",

        [],

    )



    missing_skills = match_result.get(

        "missing_skills",

        [],

    )



    matched_count = match_result.get(

        "matched_skill_count",

        len(matched_skills),

    )



    required_count = match_result.get(

        "required_skill_count",

        len(matched_skills) + len(missing_skills),

    )



    priority_plan = learning_plan.get(

        "priority_plan",

        [],

    )



    # ========================================================

    # PDF TITLE

    # ========================================================



    story.append(

        Paragraph(

            "AI Resume & Job Analysis Report",

            title_style,

        )

    )



    story.append(

        Paragraph(

            "LLM + MCP powered career intelligence system",

            subtitle_style,

        )

    )



    story.append(

        Paragraph(

            "Created by Mohsin",

            subtitle_style,

        )

    )



    story.append(

        Paragraph(

            f"<b>Generated:</b> "

            f"{datetime.now().strftime('%d %B %Y, %I:%M %p')}",

            normal_style,

        )

    )



    story.append(

        Paragraph(

            f"<b>MCP Tool:</b> {selected_tool}",

            normal_style,

        )

    )



    # ========================================================

    # MATCH OVERVIEW

    # ========================================================



    story.append(

        Paragraph(

            "1. Match Overview",

            heading_style,

        )

    )



    score_table = Table(

        [

            [

                "Overall Match",

                "Matched Skills",

                "Required Skills",

            ],

            [

                f"{match_score}%",

                str(matched_count),

                str(required_count),

            ],

        ],

        colWidths=[

            2.1 * inch,

            2.1 * inch,

            2.1 * inch,

        ],

    )



    score_table.setStyle(

        TableStyle(

            [

                (

                    "BACKGROUND",

                    (0, 0),

                    (-1, 0),

                    colors.HexColor("#e2e8f0"),

                ),

                (

                    "FONTNAME",

                    (0, 0),

                    (-1, 0),

                    "Helvetica-Bold",

                ),

                (

                    "FONTNAME",

                    (0, 1),

                    (-1, 1),

                    "Helvetica-Bold",

                ),

                (

                    "TEXTCOLOR",

                    (0, 0),

                    (-1, -1),

                    colors.HexColor("#0f172a"),

                ),

                (

                    "ALIGN",

                    (0, 0),

                    (-1, -1),

                    "CENTER",

                ),

                (

                    "VALIGN",

                    (0, 0),

                    (-1, -1),

                    "MIDDLE",

                ),

                (

                    "BOX",

                    (0, 0),

                    (-1, -1),

                    0.7,

                    colors.HexColor("#cbd5e1"),

                ),

                (

                    "INNERGRID",

                    (0, 0),

                    (-1, -1),

                    0.5,

                    colors.HexColor("#e2e8f0"),

                ),

                (

                    "TOPPADDING",

                    (0, 0),

                    (-1, -1),

                    8,

                ),

                (

                    "BOTTOMPADDING",

                    (0, 0),

                    (-1, -1),

                    8,

                ),

            ]

        )

    )



    story.append(score_table)



    # ========================================================

    # MATCHED SKILLS

    # ========================================================



    story.append(

        Paragraph(

            "2. Matched Skills",

            heading_style,

        )

    )



    if matched_skills:



        for skill in matched_skills:



            story.append(

                Paragraph(

                    f"• <b>{skill.upper()}</b> — detected in resume",

                    bullet_style,

                )

            )



    else:



        story.append(

            Paragraph(

                "No matching skills were detected.",

                normal_style,

            )

        )



    # ========================================================

    # MISSING SKILLS

    # ========================================================



    story.append(

        Paragraph(

            "3. Missing Skills",

            heading_style,

        )

    )



    if missing_skills:



        for skill in missing_skills:



            story.append(

                Paragraph(

                    f"• <b>{skill.upper()}</b> — not detected in resume",

                    bullet_style,

                )

            )



    else:



        story.append(

            Paragraph(

                "No missing skills were detected.",

                normal_style,

            )

        )



    # ========================================================

    # AI CAREER ANALYSIS

    # ========================================================



    story.append(

        Paragraph(

            "4. AI Career Analysis",

            heading_style,

        )

    )



    if final_response:



        for line in final_response.splitlines():



            line = line.strip()



            if not line:



                story.append(

                    Spacer(1, 4)

                )



                continue



            safe_line = (

                line

                .replace("&", "&amp;")

                .replace("<", "&lt;")

                .replace(">", "&gt;")

            )



            if safe_line.startswith("## "):



                story.append(

                    Paragraph(

                        safe_line[3:],

                        subheading_style,

                    )

                )



            elif safe_line.startswith("# "):



                story.append(

                    Paragraph(

                        safe_line[2:],

                        subheading_style,

                    )

                )



            elif safe_line.startswith("- "):



                story.append(

                    Paragraph(

                        f"• {safe_line[2:]}",

                        bullet_style,

                    )

                )



            elif safe_line.startswith("* "):



                story.append(

                    Paragraph(

                        f"• {safe_line[2:]}",

                        bullet_style,

                    )

                )



            else:



                story.append(

                    Paragraph(

                        safe_line,

                        normal_style,

                    )

                )



    else:



        story.append(

            Paragraph(

                "No AI career analysis was returned.",

                normal_style,

            )

        )



    # ========================================================

    # LEARNING ROADMAP

    # ========================================================



    story.append(

        Paragraph(

            "5. Personalized Learning Roadmap",

            heading_style,

        )

    )



    if priority_plan:



        for index, item in enumerate(

            priority_plan,

            start=1,

        ):



            skill = item.get(

                "skill",

                "Unknown",

            )



            action = item.get(

                "action",

                "",

            )



            story.append(

                Paragraph(

                    f"{index}. {skill.upper()}",

                    subheading_style,

                )

            )



            if action:



                safe_action = (

                    action

                    .replace("&", "&amp;")

                    .replace("<", "&lt;")

                    .replace(">", "&gt;")

                )



                story.append(

                    Paragraph(

                        safe_action,

                        normal_style,

                    )

                )



    else:



        story.append(

            Paragraph(

                "No additional learning plan was generated.",

                normal_style,

            )

        )



    # ========================================================

    # MCP EVIDENCE

    # ========================================================



    story.append(

        Paragraph(

            "6. MCP Evidence",

            heading_style,

        )

    )



    if evidence:



        evidence_rows = [

            ["Skill", "Status"]

        ]



        for skill, detected in evidence.items():



            evidence_rows.append(

                [

                    skill.upper(),

                    (

                        "Detected"

                        if detected

                        else "Not detected"

                    ),

                ]

            )



        evidence_table = Table(

            evidence_rows,

            colWidths=[

                3.2 * inch,

                3.2 * inch,

            ],

        )



        evidence_table.setStyle(

            TableStyle(

                [

                    (

                        "BACKGROUND",

                        (0, 0),

                        (-1, 0),

                        colors.HexColor("#e2e8f0"),

                    ),

                    (

                        "FONTNAME",

                        (0, 0),

                        (-1, 0),

                        "Helvetica-Bold",

                    ),

                    (

                        "FONTSIZE",

                        (0, 0),

                        (-1, -1),

                        9,

                    ),

                    (

                        "BOX",

                        (0, 0),

                        (-1, -1),

                        0.7,

                        colors.HexColor("#cbd5e1"),

                    ),

                    (

                        "INNERGRID",

                        (0, 0),

                        (-1, -1),

                        0.5,

                        colors.HexColor("#e2e8f0"),

                    ),

                    (

                        "TOPPADDING",

                        (0, 0),

                        (-1, -1),

                        6,

                    ),

                    (

                        "BOTTOMPADDING",

                        (0, 0),

                        (-1, -1),

                        6,

                    ),

                ]

            )

        )



        story.append(

            evidence_table

        )



    else:



        story.append(

            Paragraph(

                "No MCP evidence was returned.",

                normal_style,

            )

        )



    # ========================================================

    # JOB DESCRIPTION

    # ========================================================



    story.append(

        Paragraph(

            "7. Job Description",

            heading_style,

        )

    )



    job_text = (

        job_description

        .replace("&", "&amp;")

        .replace("<", "&lt;")

        .replace(">", "&gt;")

        .replace("\n", "<br/>")

    )



    story.append(

        Paragraph(

            job_text,

            small_style,

        )

    )



    # ========================================================

    # EXTRACTED RESUME

    # ========================================================



    story.append(

        Paragraph(

            "8. Extracted Resume Text",

            heading_style,

        )

    )



    resume_display = (

        resume_text

        .replace("&", "&amp;")

        .replace("<", "&lt;")

        .replace(">", "&gt;")

        .replace("\n", "<br/>")

    )



    story.append(

        Paragraph(

            resume_display,

            small_style,

        )

    )



    document.build(story)



    buffer.seek(0)



    return buffer.getvalue()





# ============================================================

# INPUT SECTION

# ============================================================



st.header(

    "Resume and Job Description"

)



st.caption(

    "Upload your resume and paste the target job description."

)



resume_col, job_col = st.columns(

    2,

    gap="large",

)





# ============================================================

# RESUME

# ============================================================



with resume_col:



    st.subheader(

        "Resume"

    )



    st.caption(

        "Upload your latest resume in PDF format."

    )



    resume_file = st.file_uploader(

        "Upload Resume PDF",

        type=["pdf"],

        label_visibility="collapsed",

    )





# ============================================================

# JOB DESCRIPTION

# ============================================================



with job_col:



    st.subheader(

        "Job Description"

    )



    st.caption(

        "Paste the complete job description from LinkedIn, "

        "Naukri, or the company careers page."

    )



    job_description = st.text_area(

        "Job Description",

        height=190,

        placeholder=(

            "Example:\n\n"

            "We are hiring an AI Engineer Intern.\n\n"

            "Requirements:\n"

            "Python\n"

            "JavaScript\n"

            "Node.js\n"

            "FastAPI\n"

            "Docker\n"

            "MCP\n"

            "LLM\n"

            "Statistics"

        ),

        label_visibility="collapsed",

    )





# ============================================================

# ANALYZE BUTTON

# ============================================================



st.write("")



analyze_button = st.button(

    "Analyze Resume & Job Match",

    type="primary",

    use_container_width=True,

)





# ============================================================

# RUN ANALYSIS

# ============================================================



if analyze_button:



    if resume_file is None:



        st.error(

            "Please upload a resume PDF before starting the analysis."

        )



        st.stop()



    if not job_description.strip():



        st.error(

            "Please paste a job description before starting the analysis."

        )



        st.stop()



    temp_pdf_path = None



    try:



        with st.status(

            "Running AI and MCP analysis...",

            expanded=True,

        ) as status:



            st.write(

                "Extracting resume text..."

            )



            with tempfile.NamedTemporaryFile(

                delete=False,

                suffix=".pdf",

            ) as temp_file:



                temp_file.write(

                    resume_file.getbuffer()

                )



                temp_pdf_path = temp_file.name



            resume_text = extract_text_from_pdf(

                temp_pdf_path

            )



            if not resume_text.strip():



                status.update(

                    label="Analysis failed",

                    state="error",

                )



                st.error(

                    "No readable text was found in the uploaded PDF."

                )



                st.stop()



            st.session_state.resume_text = (

                resume_text

            )



            st.session_state.job_description = (

                job_description

            )



            st.write(

                "Connecting AI agent with MCP..."

            )



            st.write(

                "Discovering MCP tools..."

            )



            st.write(

                "Selecting the appropriate MCP tool..."

            )



            st.write(

                "Running resume and job matching..."

            )



            st.write(

                "Generating skill-gap learning plan..."

            )



            result = asyncio.run(

                run_agent(

                    resume_text=resume_text,

                    job_description=job_description,

                )

            )



            status.update(

                label="Analysis completed successfully",

                state="complete",

            )



        st.session_state.analysis_result = result

        st.session_state.analysis_error = None

        st.session_state.pdf_report = None



    except Exception as error:



        st.session_state.analysis_result = None

        st.session_state.analysis_error = str(error)



        st.error(

            "The analysis could not be completed."

        )



        with st.expander(

            "View Technical Error"

        ):



            st.exception(error)



    finally:



        if temp_pdf_path:



            try:



                Path(

                    temp_pdf_path

                ).unlink(

                    missing_ok=True

                )



            except Exception:



                pass





# ============================================================

# RESULTS

# ============================================================



result = st.session_state.analysis_result



if result:



    # ========================================================

    # RESULT DATA

    # ========================================================



    match_result = result.get(

        "match_result",

        {},

    )



    learning_plan = result.get(

        "learning_plan",

        {},

    )



    final_response = result.get(

        "final_response",

        "",

    )



    selected_tool = result.get(

        "selected_tool",

        "",

    )



    matched_skills = match_result.get(

        "matched_skills",

        [],

    )



    missing_skills = match_result.get(

        "missing_skills",

        [],

    )



    match_score = match_result.get(

        "match_score",

        0,

    )



    matched_count = match_result.get(

        "matched_skill_count",

        0,

    )



    required_count = match_result.get(

        "required_skill_count",

        0,

    )



    evidence = match_result.get(

        "evidence",

        {},

    )



    priority_plan = learning_plan.get(

        "priority_plan",

        [],

    )





    # ========================================================

    # ANALYSIS RESULTS

    # ========================================================



    st.divider()



    st.header(

        "Analysis Results"

    )



    st.caption(

        "Results generated through the Groq + MCP multi-step workflow."

    )





    # ========================================================

    # MCP WORKFLOW

    # ========================================================



    with st.container(border=True):



        st.subheader(

            "MCP Agent Workflow"

        )



        st.success(

            "MCP workflow executed successfully."

        )



        st.write(

            f"Selected MCP tool: \`{selected_tool}\`"

        )



        st.caption(

            "The MCP tool produced structured results which "

            "were used by the LLM to generate the final analysis."

        )





    # ========================================================

    # MATCH OVERVIEW

    # ========================================================



    st.subheader(

        "Match Overview"

    )



    metric1, metric2, metric3 = st.columns(

        3,

        gap="large",

    )



    with metric1:



        st.metric(

            "Overall Match",

            f"{match_score}%",

        )



    with metric2:



        st.metric(

            "Matched Skills",

            matched_count,

        )



    with metric3:



        st.metric(

            "Required Skills",

            required_count,

        )



    st.caption(

        f"Resume-to-job alignment: {match_score}%"

    )



    try:



        progress_value = (

            float(match_score) / 100

        )



    except (

        TypeError,

        ValueError,

    ):



        progress_value = 0



    progress_value = max(

        0.0,

        min(

            progress_value,

            1.0,

        ),

    )



    st.progress(

        progress_value

    )





    # ========================================================

    # SKILL ANALYSIS

    # ========================================================



    st.subheader(

        "Skill Analysis"

    )



    matched_col, missing_col = st.columns(

        2,

        gap="large",

    )





    # ========================================================

    # MATCHED SKILLS

    # ========================================================



    with matched_col:



        with st.container(border=True):



            st.subheader(

                "Matched Skills"

            )



            if matched_skills:



                for skill in matched_skills:



                    st.markdown(

                        f"**{skill.upper()}** — detected in resume"

                    )



                    st.divider()



            else:



                st.write(

                    "No matching skills were detected."

                )





    # ========================================================

    # MISSING SKILLS

    # ========================================================



    with missing_col:



        with st.container(border=True):



            st.subheader(

                "Missing Skills"

            )



            if missing_skills:



                for skill in missing_skills:



                    st.markdown(

                        f"**{skill.upper()}** — not detected in resume"

                    )



                    st.divider()



            else:



                st.write(

                    "No missing skills were detected."

                )





    # ========================================================

    # AI CAREER ANALYSIS

    # ========================================================



    st.subheader(

        "AI Career Analysis"

    )



    st.caption(

        "Final response generated by Groq using structured MCP results."

    )



    with st.container(border=True):



        if final_response:



            st.markdown(

                final_response

            )



        else:



            st.write(

                "No AI career analysis was returned."

            )





    # ========================================================

    # LEARNING ROADMAP

    # ========================================================



    st.subheader(

        "Personalized Learning Roadmap"

    )



    st.caption(

        "Priority actions generated from the MCP skill-gap analysis."

    )



    if priority_plan:



        for index, item in enumerate(

            priority_plan,

            start=1,

        ):



            skill = item.get(

                "skill",

                "Unknown",

            )



            action = item.get(

                "action",

                "",

            )



            with st.container(

                border=True

            ):



                st.markdown(

                    f"**{index}. {skill.upper()}**"

                )



                st.write(

                    action

                )



    else:



        st.write(

            "No additional learning plan was generated."

        )





    # ========================================================

    # MCP EVIDENCE

    # ========================================================



    with st.expander(

        "View MCP Evidence"

    ):



        if evidence:



            evidence_rows = []



            for skill, detected in evidence.items():



                evidence_rows.append(

                    {

                        "Skill": skill.upper(),

                        "Status": (

                            "Detected"

                            if detected

                            else "Not detected"

                        ),

                    }

                )



            st.dataframe(

                evidence_rows,

                use_container_width=True,

                hide_index=True,

            )



        else:



            st.write(

                "No evidence information was returned by MCP."

            )





    # ========================================================

    # PDF REPORT

    # ========================================================



    st.divider()



    st.subheader(

        "Download Analysis Report"

    )



    st.caption(

        "Generate a professional PDF containing the complete analysis."

    )



    generate_pdf_button = st.button(

        "Generate PDF Report",

        type="primary",

        use_container_width=True,

    )



    if generate_pdf_button:



        try:



            with st.spinner(

                "Generating PDF report..."

            ):



                pdf_bytes = create_pdf_report(

                    match_result=match_result,

                    learning_plan=learning_plan,

                    final_response=final_response,

                    resume_text=st.session_state.resume_text,

                    job_description=st.session_state.job_description,

                    selected_tool=selected_tool,

                    evidence=evidence,

                )



            st.session_state.pdf_report = pdf_bytes



            st.success(

                "PDF report generated successfully."

            )



        except Exception as error:



            st.session_state.pdf_report = None



            st.error(

                "The PDF report could not be generated."

            )



            with st.expander(

                "View PDF Technical Error"

            ):



                st.exception(error)





    # ========================================================

    # DOWNLOAD PDF

    # ========================================================



    if st.session_state.pdf_report:



        current_date = datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )



        st.download_button(

            label="Download PDF Analysis Report",

            data=st.session_state.pdf_report,

            file_name=(

                f"resume_job_analysis_{current_date}.pdf"

            ),

            mime="application/pdf",

            use_container_width=True,

        )





    # ========================================================

    # EXTRACTED RESUME

    # ========================================================



    with st.expander(

        "View Extracted Resume Text"

    ):



        st.text_area(

            "Extracted Resume",

            st.session_state.resume_text,

            height=350,

            disabled=True,

            label_visibility="collapsed",

        )





    # ========================================================

    # TECHNICAL MCP OUTPUT

    # ========================================================



    with st.expander(

        "View Technical MCP Output"

    ):



        st.json(

            {

                "selected_tool": selected_tool,

                "match_result": match_result,

                "learning_plan": learning_plan,

            }

        )





# ============================================================

# FOOTER

# ============================================================



st.divider()



st.markdown(

    '<div class="footer-text">Created by <strong>Mohsin</strong></div>',

    unsafe_allow_html=True,

)