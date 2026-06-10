import os
import json
import re
import warnings
import streamlit as st
import plotly.graph_objects as go
import logging
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

# Suppress noisy transformers path warnings (Streamlit watcher scans all submodules)
warnings.filterwarnings("ignore", message=".*Accessing `__path__`.*")
warnings.filterwarnings("ignore", message=".*Examining the path of.*")
warnings.filterwarnings("ignore", message=".*No module named 'torchvision'.*")

from rag_engine import get_engine

load_dotenv()

# -------------------------
# LOGGING HELPERS
# -------------------------
def log_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    logging.info("=" * 80)
    logging.info(title)
    logging.info("=" * 80)

def log(message):
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
    print(msg)
    logging.info(msg)

# -------------------------
# RAG ENGINE (replaces static knowledge loading)
# -------------------------
@st.cache_resource
def init_rag():
    """Initialize the RAG engine once and cache it."""
    engine = get_engine()
    with st.spinner("🧠 Building knowledge index (first run only)..."):
        engine.build_index()
    return engine

# Initialize on module load — cached by Streamlit so it only runs once
rag_engine = init_rag()

# -------------------------
# OPENROUTER CLIENT
# -------------------------
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# -------------------------
# CUSTOM CSS
# -------------------------
def inject_css():
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .main-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        .main-header p {
            margin: 0.3rem 0 0 0;
            opacity: 0.9;
            font-size: 0.95rem;
        }
        .score-card {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            border-top: 4px solid #3b82f6;
        }
        .score-card .label {
            font-size: 0.85rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .score-card .value {
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0.2rem 0;
        }
        .feedback-card {
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .feedback-card h4 {
            margin: 0 0 0.6rem 0;
            font-size: 1.1rem;
        }
        .feedback-card ul {
            margin: 0;
            padding-left: 1.2rem;
        }
        .feedback-card li {
            margin-bottom: 0.3rem;
            line-height: 1.5;
        }
        .card-green {
            background: #f0fdf4;
            border-left: 5px solid #22c55e;
        }
        .card-green h4 { color: #15803d; }
        .card-amber {
            background: #fffbeb;
            border-left: 5px solid #f59e0b;
        }
        .card-amber h4 { color: #b45309; }
        .card-blue {
            background: #eff6ff;
            border-left: 5px solid #3b82f6;
        }
        .card-blue h4 { color: #1d4ed8; }
        .summary-box {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1rem;
            border-left: 5px solid #64748b;
        }
        .stButton > button {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 0.5rem 2rem !important;
            border-radius: 8px !important;
            transition: transform 0.2s !important;
        }
        .stButton > button:hover {
            transform: scale(1.02) !important;
            box-shadow: 0 4px 14px rgba(45, 106, 159, 0.4) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def score_color(val):
    if val >= 70:
        return "#22c55e"
    elif val >= 40:
        return "#f59e0b"
    return "#ef4444"

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(
    page_title="AI Resume Assistant",
    page_icon="📄",
    layout="wide"
)

inject_css()

# Custom header
st.markdown("""
    <div class="main-header">
        <h1>📄 AI Resume Assistant</h1>
        <p>Resume analysis · ATS matching · AI feedback for career growth</p>
    </div>
""", unsafe_allow_html=True)

# -------------------------
# VISUALS
# -------------------------
def render_score_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Resume Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#3b82f6"},
            "steps": [
                {"range": [0, 40], "color": "#ef4444"},
                {"range": [40, 70], "color": "#f59e0b"},
                {"range": [70, 100], "color": "#22c55e"},
            ],
        }
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#1e293b", "size": 14}
    )
    st.plotly_chart(fig, width='stretch')


def render_radar(breakdown):
    labels = list(breakdown.keys())
    values = list(breakdown.values())

    labels += [labels[0]]
    values += [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        line_color="#3b82f6",
        fillcolor="rgba(59,130,246,0.3)"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10]),
            bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=False,
        height=400,
        margin=dict(l=40, r=40, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#1e293b", "size": 12}
    )

    st.plotly_chart(fig, width='stretch')


def render_styled_list(title, items, card_class, icon):
    if not items:
        return
    items_html = "".join(f"<li>{item}</li>" for item in items)
    st.markdown(f"""
        <div class="feedback-card {card_class}">
            <h4>{icon} {title}</h4>
            <ul>{items_html}</ul>
        </div>
    """, unsafe_allow_html=True)


# -------------------------
# PDF REPORT
# -------------------------
def generate_pdf_report(result, mode):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    title = "Resume Analysis Report" if mode == "Resume Analysis" else "ATS Match Report"

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))

    score = result.get("score") or result.get("match_score", 0)

    elements.append(Paragraph(f"<b>Score:</b> {score}/100", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(result.get("summary", ""), styles["BodyText"]))
    elements.append(Spacer(1, 15))

    def add_list(title, items):
        if items:
            elements.append(Paragraph(title, styles["Heading2"]))
            elements.append(
                ListFlowable(
                    [ListItem(Paragraph(i, styles["BodyText"])) for i in items]
                )
            )
            elements.append(Spacer(1, 10))

    add_list("Strengths", result.get("strengths", []))

    if mode == "Resume Analysis":
        add_list("Weaknesses", result.get("weaknesses", []))
        add_list("Improvements", result.get("improvements", []))
    else:
        add_list("Missing Skills", result.get("missing_skills", []))
        add_list("Recommendations", result.get("recommendations", []))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# -------------------------
# HELPERS
# -------------------------
def extract_text(pdf_file):
    reader = PdfReader(pdf_file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

# -------------------------
# UI INPUTS
# -------------------------
col_mode, col_input = st.columns([1, 3])

with col_mode:
    mode = st.radio(
        "Choose mode",
        ["Resume Analysis", "ATS Job Match"],
        horizontal=False
    )

with col_input:
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    text_resume = st.text_area("Or paste your resume", height=180)

    job_description = ""
    if mode == "ATS Job Match":
        job_description = st.text_area("Job description", height=150)

    run = st.button("🚀 Analyze Resume", use_container_width=True)

# -------------------------
# BUILD INPUT
# -------------------------
resume = ""
if uploaded_file:
    with st.spinner("Extracting text from PDF..."):
        resume = extract_text(uploaded_file)
elif text_resume.strip():
    resume = text_resume

# -------------------------
# PROMPT BUILDER
# -------------------------
def build_prompt(mode, resume, job_description, knowledge):

    schema = {
        "score": "integer (0-100)",
        "summary": "string (max 50 words)",
        "breakdown": {
            "skills": "0-10",
            "experience": "0-10",
            "clarity": "0-10",
            "impact": "0-10",
            "ats_match": "0-10"
        },
        "strengths": ["string"],
        "weaknesses": ["string"],
        "improvements": ["string"]
    }

    rules = """
You are a strict resume evaluation engine.

RULES:
- Output ONLY valid JSON
- No markdown
- No explanation
- No extra keys
- No reasoning text
- No trailing commas
- All scores MUST be numbers
- breakdown values must be integers 0-10
- score MUST be 0-100 and consistent with breakdown
- Score must strictly reflect the actual quality — do NOT inflate scores.
  A score of 70+ should represent genuinely strong, well-quantified resumes.
  Most average resumes should score in the 40-69 range.
  Poorly formatted or thin resumes should score below 40.

RESPONSE QUALITY (CRITICAL):
- Each item in strengths/weaknesses/improvements MUST be a complete sentence (8+ words)
- Single words or short phrases ("Communication", "Teamwork") are NOT acceptable
- Example good strength: "Strong verbal communication and de-escalation skills demonstrated in high-stress disability support settings"
- Example good weakness: "Limited quantifiable achievements — consider adding specific metrics like client caseload numbers or incident reduction percentages"
- Provide 4-5 items per category, each with specific reference to the resume content

SCORING LOGIC:
- skills: keyword match + relevance (0-10)
- experience: depth + years + roles (0-10)
- clarity: formatting + readability (0-10)
- impact: measurable outcomes (0-10)
- ats_match: ATS keyword density (0-10)

"""

    base_json = json.dumps(schema, indent=2)

    if mode == "Resume Analysis":
        return f"""
{rules}

EXPECTED OUTPUT FORMAT:
{base_json}

KNOWLEDGE:
{knowledge}

RESUME:
{resume}
"""

    else:
        return f"""
{rules}

EXPECTED OUTPUT FORMAT:
{base_json}

RESUME:
{resume}

JOB DESCRIPTION:
{job_description}
"""


def safe_parse_json(text):
    try:
        return json.loads(text)
    except:
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            return None
    return None


def normalize_score(result):
    b = result.get("breakdown", {})

    values = [int(v) for v in b.values() if isinstance(v, (int, float))]

    if not values:
        return result

    breakdown_avg = (sum(values) / len(values)) * 10

    model_score = result.get("score", 0)

    result["score"] = int((model_score + breakdown_avg) / 2)

    return result


# -------------------------
# RUN
# -------------------------
if run:

    if not resume.strip():
        st.warning("Please provide a resume")
        st.stop()

    if mode == "ATS Job Match" and not job_description.strip():
        st.warning("Please provide job description")
        st.stop()

    # -------------------------
    # BUILD PROMPT
    # -------------------------
    # Retrieve relevant knowledge chunks using RAG (instead of dumping ALL files)
    retrieved_knowledge = rag_engine.retrieve(resume, top_k=3)
    if not retrieved_knowledge:
        retrieved_knowledge = "No specific knowledge chunks matched the resume. Use general best practices."

    prompt = build_prompt(mode, resume, job_description, retrieved_knowledge)

    # -------------------------
    # DEBUG LOGGING
    # -------------------------
    log_section("RESUME ANALYSIS STARTED")
    log(f"Mode: {mode}")
    log(f"Resume Length: {len(resume)}")

    if mode == "ATS Job Match":
        log(f"Job Description Length: {len(job_description)}")

    log_section("PROMPT START")
    print(prompt)
    logging.info(prompt)
    log_section("PROMPT END")

    # -------------------------
    # API CALL
    # -------------------------
    log("Sending API request...")

    with st.spinner("🤖 AI is analyzing your resume..."):

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}]
        )

    log("API response received")

    # -------------------------
    # FULL RESPONSE LOG
    # -------------------------
    try:
        response_json = response.model_dump_json(indent=2)
        log_section("FULL API RESPONSE OBJECT")
        print(response_json)
        logging.info("FULL RESPONSE START")
        logging.info(response_json)
        logging.info("FULL RESPONSE END")
    except Exception as e:
        log(f"Could not dump full response: {e}")

    # -------------------------
    # RAW OUTPUT
    # -------------------------
    raw_output = response.choices[0].message.content

    log_section("RAW OUTPUT START")
    print(raw_output)
    logging.info("RAW OUTPUT START")
    logging.info(raw_output)
    logging.info("RAW OUTPUT END")
    log_section("RAW OUTPUT END")

    # Guard against null response (e.g. model returned image only)
    if raw_output is None:
        log_section("NULL RESPONSE ERROR")
        logging.error("Model returned null content (likely image-only response)")
        st.error("The model returned an image instead of text. Try a different model or resume.")
        st.stop()

    # -------------------------
    # CLEANING
    # -------------------------
    cleaned = re.sub(r"```json|```", "", raw_output).strip()

    log_section("CLEANED OUTPUT START")
    print(cleaned)
    logging.info("CLEANED OUTPUT START")
    logging.info(cleaned)
    logging.info("CLEANED OUTPUT END")

    # -------------------------
    # JSON PARSE
    # -------------------------
    try:
        log("Attempting JSON parse")
        result = safe_parse_json(cleaned)

        if not result:
            log_section("JSON PARSE ERROR")
            logging.error(cleaned)

            st.error("Model returned invalid JSON")
            st.text(cleaned)
            st.stop()

        log("JSON parse successful")

        # Normalize score — average model score with breakdown average
        result = normalize_score(result)

        st.success("✅ Resume analysis complete")

        # -------------------------
        # TOP METRICS (all normalized to 0-100)
        # -------------------------
        b = result.get("breakdown", {})
        score = result.get("score", 0)
        ats_match = b.get("ats_match", 0) * 10
        clarity = b.get("clarity", 0) * 10

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)

        with mcol1:
            c = score_color(score)
            st.markdown(f"""
                <div class="score-card" style="border-top-color: {c};">
                    <div class="label">Overall Score</div>
                    <div class="value" style="color: {c};">{score}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">/ 100</div>
                </div>
            """, unsafe_allow_html=True)

        with mcol2:
            c = score_color(ats_match)
            st.markdown(f"""
                <div class="score-card" style="border-top-color: {c};">
                    <div class="label">ATS Match</div>
                    <div class="value" style="color: {c};">{ats_match}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">/ 100</div>
                </div>
            """, unsafe_allow_html=True)

        with mcol3:
            c = score_color(clarity)
            st.markdown(f"""
                <div class="score-card" style="border-top-color: {c};">
                    <div class="label">Clarity</div>
                    <div class="value" style="color: {c};">{clarity}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">/ 100</div>
                </div>
            """, unsafe_allow_html=True)

        with mcol4:
            skills = b.get("skills", 0) * 10
            c = score_color(skills)
            st.markdown(f"""
                <div class="score-card" style="border-top-color: {c};">
                    <div class="label">Skills</div>
                    <div class="value" style="color: {c};">{skills}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">/ 100</div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        # -------------------------
        # VISUALS
        # -------------------------
        gauge_col, radar_col = st.columns(2)

        with gauge_col:
            render_score_gauge(score)

        with radar_col:
            render_radar(b)

        # Breakdown expander with raw 0-10 values
        with st.expander("📊 View detailed breakdown (0-10 scale)"):
            bcols = st.columns(5)
            for i, (key, val) in enumerate(b.items()):
                with bcols[i]:
                    st.metric(label=key.replace("_", " ").title(), value=val)

        st.divider()

        # -------------------------
        # SUMMARY
        # -------------------------
        st.markdown("""
            <div class="summary-box">
                <h4 style="margin: 0 0 0.3rem 0; color: #334155;">📌 Summary</h4>
                <p style="margin: 0; color: #475569; font-size: 1.05rem;">
        """ + result.get("summary", "") + "</p></div>", unsafe_allow_html=True)

        # -------------------------
        # DETAILED FEEDBACK as styled cards
        # -------------------------
        render_styled_list("Strengths", result.get("strengths", []), "card-green", "💪")
        render_styled_list("Weaknesses", result.get("weaknesses", []), "card-amber", "⚠️")
        render_styled_list("Improvements", result.get("improvements", []), "card-blue", "🚀")

        # -------------------------
        # PDF DOWNLOAD
        # -------------------------
        st.divider()
        pdf_bytes = generate_pdf_report(result, mode)
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=f"resume_{mode.lower().replace(' ', '_')}_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    except Exception as e:
        log_section("JSON PARSE ERROR")
        print("Error:", str(e))
        print(cleaned)
        logging.error(f"JSON Parse Error: {e}")
        logging.error(cleaned)

        st.error("Model returned invalid JSON")
        st.text(cleaned)
        st.stop()

    log_section("PIPELINE COMPLETE")
    log("All processing finished successfully")