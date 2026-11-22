import os

# Suppress noisy transformers logging BEFORE any imports that trigger it
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_LOG_LEVEL"] = "error"

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)

import warnings
warnings.filterwarnings("ignore", message=".*Accessing `__path__`.*")
warnings.filterwarnings("ignore", message=".*Examining the path of.*")
warnings.filterwarnings("ignore", message=".*No module named 'torchvision'.*")

import json
import re
import tempfile
import logging
import os.path
import html
from logging.handlers import RotatingFileHandler

import streamlit as st
import plotly.graph_objects as go
import logging
import os.path
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
from pypdf.errors import PdfReadError
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
from scoring import score_resume, analyze_ats_gap, compute_job_fit_score

load_dotenv()

# -------------------------
# STRUCTURED LOGGING SETUP
# -------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "resume_app.json"

# Create a rotating file handler (max 5MB, keep 7 days worth)
rotating_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=7
)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

rotating_handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(rotating_handler)
logging.getLogger().setLevel(logging.INFO)

# -------------------------
# STARTUP VALIDATION
# -------------------------
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key or api_key.strip() == "":
    st.error(
        "❌ **API Key Missing**\n\n"
        "Set your OpenRouter API key before running this app:\n\n"
        "`OPENROUTER_API_KEY=sk-or-v1-xxxxx`\n\n"
        "[Get a free API key →](https://openrouter.ai/)"
    )
    st.stop()

# -------------------------
# LOGGING HELPERS
# -------------------------
def log_section(title):
    """Log a section header to console and JSON log."""
    separator = "=" * 80
    print(f"\n{separator}")
    print(title)
    print(separator)
    logging.info(json.dumps({"event": "section_start", "title": title}))

def log(message):
    """Log a message with timestamp to console and JSON log."""
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
    print(msg)
    logging.info(json.dumps({"event": "log", "message": message, "timestamp": datetime.now().isoformat()}))

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
# OPENROUTER CLIENT (with retry for free tier failures)
# -------------------------
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# Free models that are known to work for text generation (fallbacks)
FREE_MODELS = [
    "openrouter/free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "meta/llama-3.2-3b-instruct:free",
]

# -------------------------
# INPUT VALIDATION CONSTANTS
# -------------------------
MAX_FILE_SIZE_MB = 10
MAX_RESUME_CHARS = 50000
MAX_JOB_DESC_CHARS = 10000
MIN_RESUME_CHARS = 100

# -------------------------
# CUSTOM CSS — Figma "AI Workspace" Premium Design
# -------------------------
def inject_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ── Base ── */
        .stApp {
            background: #0A0A0A;
        }
        .main-header {
            display: none;
        }
        .stApp > header {
            background: rgba(15, 23, 42, 0.75) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
        }
        .st-bd, .st-be, .st-bf, .st-bg, .st-cb, .st-cc, .st-cd, .st-ce {
            background: transparent !important;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            background: transparent !important;
        }
        [data-testid="stSidebar"] .st-bq {
            background: transparent !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(90deg, #6366F1, #96A1F3, #94B5F2, #7BC5F0, #56D5EC, #06B6D4) !important;
            color: white !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            border: none !important;
            padding: 0.5rem 2rem !important;
            border-radius: 10px !important;
            height: 52px !important;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3) !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 25px rgba(6, 182, 212, 0.4) !important;
        }

        /* ── Radio / Toggle pills ── */
        [data-testid="stSidebar"] .stRadio label {
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
            background: rgba(15, 23, 42, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 14px !important;
            padding: 4px !important;
            gap: 0 !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
            border-radius: 10px !important;
            padding: 8px 0 !important;
            flex: 1 !important;
            text-align: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-selected="true"] {
            background: #314158 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-selected="true"] p {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
            color: #90A1B9 !important;
        }

        /* ── Text areas ── */
        [data-testid="stSidebar"] textarea {
            background: rgba(15, 23, 42, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 10px !important;
            color: #E2E8F0 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important;
            line-height: 1.5 !important;
        }
        [data-testid="stSidebar"] textarea:focus {
            border-color: #6366F1 !important;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.3) !important;
        }
        [data-testid="stSidebar"] textarea::placeholder {
            color: #62748E !important;
        }

        /* ── File uploader ── */
        [data-testid="stFileUploader"] {
            background: rgba(15, 23, 42, 0.3) !important;
            border: 1.6px dashed #45556C !important;
            border-radius: 16px !important;
            padding: 12px !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: rgba(6, 182, 212, 0.5) !important;
        }
        [data-testid="stFileUploader"] section {
            background: transparent !important;
            border: none !important;
        }

        /* ── Labels / captions ── */
        .st-bq label, .st-cx label, .st-c0 label {
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            color: #CAD5E2 !important;
            font-size: 13px !important;
        }

        /* ── Main content area ── */
        [data-testid="stAppViewContainer"] > .main {
            background: #0A0A0A !important;
        }
        [data-testid="stAppViewContainer"] > .main > div:first-child {
            background: #0F172A !important;
        }

        /* ── Score cards ── */
        .score-card {
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 16px !important;
            padding: 24px 16px 20px !important;
            text-align: center !important;
            transition: all 0.2s ease !important;
        }
        .score-card:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(0,0,0,0.3) !important;
        }
        .score-card .label {
            font-family: 'Inter', sans-serif !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            color: #64748B !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
        }
        .score-card .value {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 48px !important;
            font-weight: 700 !important;
            line-height: 1 !important;
            letter-spacing: -0.03em !important;
            margin: 8px 0 4px !important;
        }
        .score-card .value + div {
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
            color: #475569 !important;
        }

        /* ── Feedback cards ── */
        .feedback-card {
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            margin-bottom: 1rem !important;
            transition: all 0.2s ease !important;
        }
        .feedback-card:hover {
            box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
        }
        .feedback-card h4 {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            margin: 0 0 0.6rem 0 !important;
        }
        .feedback-card ul {
            margin: 0 !important;
            padding-left: 0 !important;
            list-style: none !important;
        }
        .feedback-card li {
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
            font-weight: 400 !important;
            line-height: 1.6 !important;
            margin-bottom: 8px !important;
            padding-left: 20px !important;
            position: relative !important;
            color: #CBD5E1 !important;
            white-space: normal !important;
            word-break: break-word !important;
            overflow-wrap: break-word !important;
        }
        .feedback-card li::before {
            content: "•" !important;
            position: absolute !important;
            left: 4px !important;
            color: inherit !important;
            opacity: 0.7 !important;
        }

        /* Strength (green) */
        .card-green {
            background: rgba(0, 188, 125, 0.08) !important;
            border-left: 4px solid #00BC7D !important;
            backdrop-filter: blur(8px) !important;
        }
        .card-green h4 { color: #00BC7D !important; }
        .card-green li { color: #CBD5E1 !important; }

        /* Weakness (rose) */
        .card-amber {
            background: rgba(255, 32, 86, 0.08) !important;
            border-left: 4px solid #FF2056 !important;
            backdrop-filter: blur(8px) !important;
        }
        .card-amber h4 { color: #FF2056 !important; }
        .card-amber li { color: #CBD5E1 !important; }

        /* Improvement (indigo) */
        .card-blue {
            background: rgba(97, 95, 255, 0.08) !important;
            border-left: 4px solid #615FFF !important;
            backdrop-filter: blur(8px) !important;
        }
        .card-blue h4 { color: #615FFF !important; }
        .card-blue li { color: #CBD5E1 !important; }

        /* ── Summary box ── */
        .summary-box {
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 16px !important;
            padding: 24px !important;
            margin-bottom: 1rem !important;
            position: relative !important;
        }
        .summary-box::before {
            content: "" !important;
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 4px !important;
            height: 100% !important;
            background: #00D3F3 !important;
            border-radius: 4px 0 0 4px !important;
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.5) !important;
        }
        .summary-box h4 {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            color: #E2E8F0 !important;
            margin: 0 0 0.5rem 0 !important;
        }
        .summary-box p {
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
            line-height: 1.75 !important;
            color: #90A1B9 !important;
            margin: 0 !important;
        }

        /* ── Success banner ── */
        .stAlert {
            background: rgba(0, 188, 125, 0.08) !important;
            border: 1px solid rgba(0, 188, 125, 0.15) !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
        }

        /* ── Dividers ── */
        hr {
            border-color: rgba(255, 255, 255, 0.06) !important;
            margin: 16px 0 !important;
        }

        /* ── Metrics ── */
        [data-testid="stMetricValue"] {
            font-family: 'Space Grotesk', sans-serif !important;
            font-weight: 700 !important;
            color: #E2E8F0 !important;
        }
        [data-testid="stMetricLabel"] {
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            color: #64748B !important;
        }

        /* ── Expander / accordion ── */
        .streamlit-expanderHeader {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            color: #E2E8F0 !important;
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 16px 16px 0 0 !important;
        }
        .streamlit-expanderContent {
            background: rgba(30, 41, 59, 0.4) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-top: none !important;
            border-radius: 0 0 16px 16px !important;
            padding: 0 24px 24px !important;
        }

        /* ── Keyword tags (ATS pills) ── */
        .keyword-tag {
            display: inline-flex !important;
            align-items: center !important;
            padding: 4px 10px !important;
            border-radius: 6px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            margin: 3px !important;
            transition: transform 0.15s ease !important;
            cursor: default !important;
        }
        .keyword-tag:hover {
            transform: translateY(-2px) !important;
        }
        .keyword-tag.matched {
            background: rgba(0, 188, 125, 0.12) !important;
            border: 1px solid rgba(0, 188, 125, 0.3) !important;
            color: #10B981 !important;
        }
        .keyword-tag.critical {
            background: rgba(244, 63, 94, 0.12) !important;
            border: 1px solid rgba(244, 63, 94, 0.3) !important;
            color: #F43F5E !important;
        }
        .keyword-tag.other {
            background: rgba(245, 158, 11, 0.12) !important;
            border: 1px solid rgba(245, 158, 11, 0.3) !important;
            color: #F59E0B !important;
        }

        /* ── Download buttons ── */
        .stButton button[kind="secondary"] {
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            color: #E2E8F0 !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            height: 48px !important;
            transition: all 0.2s ease !important;
        }
        .stButton button[kind="secondary"]:hover {
            background: rgba(30, 41, 59, 0.8) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def score_color(val):
    if val >= 70:
        return "#10B981"
    elif val >= 40:
        return "#F59E0B"
    return "#F43F5E"

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
        number={"font": {"color": "#E2E8F0", "family": "Space Grotesk", "size": 48}},
        gauge={
            "axis": {"range": [0, 100], "visible": True, "tickcolor": "#475569"},
            "bar": {"color": "#06B6D4", "thickness": 0.4},
            "steps": [
                {"range": [0, 40], "color": "rgba(244,63,94,0.15)"},
                {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                {"range": [70, 100], "color": "rgba(16,185,129,0.15)"},
            ],
            "threshold": {
                "line": {"color": "#F8FAFC", "width": 3},
                "thickness": 0.75,
                "value": score
            },
            "borderwidth": 0,
        }
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94A3B8", "size": 14, "family": "Inter"}
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
        line_color="#6366F1",
        fillcolor="rgba(99,102,241,0.25)"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10],
                          color="#64748B", gridcolor="rgba(255,255,255,0.06)"),
            angularaxis=dict(color="#94A3B8", gridcolor="rgba(255,255,255,0.06)"),
            bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=False,
        height=400,
        margin=dict(l=40, r=40, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94A3B8", "size": 12, "family": "Inter"}
    )

    st.plotly_chart(fig, width='stretch')


def render_styled_list(title, items, card_class, icon):
    """Render a styled list card with XSS protection (escaping items)."""
    if not items:
        return
    # Escape each item to prevent XSS from LLM-generated content
    escaped_items = [html.escape(str(item)) for item in items]
    items_html = "".join(f"<li>{item}</li>" for item in escaped_items)
    st.markdown(f"""
        <div class="feedback-card {card_class}">
            <h4>{icon} {title}</h4>
            <ul>{items_html}</ul>
        </div>
    """, unsafe_allow_html=True)


# -------------------------
# PDF REPORT
# -------------------------
def generate_pdf_report(result, mode, rubric_score=0):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    title = "Resume Analysis Report" if mode == "Resume Analysis" else "ATS Match Report"

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Score:</b> {rubric_score}/100", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(result.get("summary", ""), styles["BodyText"]))
    elements.append(Spacer(1, 15))

    def add_list(list_title, items):
        if not items:
            return
        # Strip ALL non-printable / non-ASCII characters that ReportLab
        # can't render; result is pure safe ASCII
        clean = lambda s: re.sub(r"[^\x20-\x7E]", "", s)

        elements.append(Paragraph(f"<b>{clean(list_title)}</b>", styles["Heading2"]))
        elements.append(Spacer(1, 6))

        for item in items:
            safe_item = clean(item)
            if safe_item.strip():
                elements.append(Paragraph(f"&#x2022; {safe_item}", styles["BodyText"]))

        elements.append(Spacer(1, 10))

    add_list("Strengths", result.get("strengths", []))

    # Reuse the same schema keys for both modes; rename only the label
    label_weak = "Missing Skills" if mode == "ATS Job Match" else "Weaknesses"
    label_imp  = "Recommendations" if mode == "ATS Job Match" else "Improvements"
    add_list(label_weak, result.get("weaknesses", []))
    add_list(label_imp,  result.get("improvements", []))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# -------------------------
# INPUT VALIDATION HELPERS
# -------------------------
def validate_resume_text(text, context="resume"):
    """Validate resume/job description text length."""
    if not text or not text.strip():
        return None, "Please provide a resume."
    
    if len(text) < MIN_RESUME_CHARS:
        return None, f"Resume too short. Minimum {MIN_RESUME_CHARS} characters."
    
    max_chars = MAX_JOB_DESC_CHARS if context == "job" else MAX_RESUME_CHARS
    if len(text) > max_chars:
        return None, f"{context.capitalize()} too long (>{max_chars} chars). Please shorten it."
    
    return text.strip(), None

def check_pdf_format(file_bytes):
    """Check if file is a valid PDF by magic bytes."""
    if not file_bytes or len(file_bytes) < 4:
        return False, "File too small to be a valid PDF."
    
    if not file_bytes.startswith(b'%PDF'):
        return False, "File header does not match PDF format. Ensure it's a valid PDF."
    
    return True, None

def validate_file_upload(uploaded_file):
    """Validate uploaded PDF file."""
    if not uploaded_file:
        return None, None
    
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return None, f"File too large ({file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB). Max size: {MAX_FILE_SIZE_MB}MB."
    
    # Check PDF format
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # Reset for later reading
    is_valid, error = check_pdf_format(file_bytes)
    if not is_valid:
        return None, error
    
    return uploaded_file, None

def extract_text(pdf_file):
    """Extract text from PDF file with proper error handling."""
    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_file.read())
            tmp_file.flush()
            
            try:
                reader = PdfReader(tmp_file.name)
            except PdfReadError as e:
                raise ValueError(f"PDF corrupted or unreadable: {str(e)}")
            except Exception as e:
                raise ValueError(f"Failed to read PDF: {str(e)}")
            
            if not reader.pages:
                raise ValueError("PDF has no pages.")
            
            text_parts = []
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    log(f"Warning: Could not extract page {i+1}: {e}")
                    continue
            
            extracted = "\n".join(text_parts)
            if not extracted.strip():
                raise ValueError("PDF has no extractable text.")
            
            return extracted
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise ValueError(f"Unexpected error reading PDF: {str(e)}")

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
error_message = ""

if uploaded_file:
    uploaded_file, file_error = validate_file_upload(uploaded_file)
    if file_error:
        error_message = f"❌ **File Error:** {file_error}"
    elif uploaded_file:
        with st.spinner("Extracting text from PDF..."):
            try:
                resume = extract_text(uploaded_file)
                resume, text_error = validate_resume_text(resume)
                if text_error:
                    error_message = f"❌ **Validation Error:** {text_error}"
            except ValueError as e:
                error_message = f"❌ **PDF Error:** {str(e)}"
            except Exception as e:
                error_message = f"❌ **Unexpected Error:** {str(e)}"
                log(f"Error extracting PDF: {e}")
elif text_resume.strip():
    resume, text_error = validate_resume_text(text_resume)
    if text_error:
        error_message = f"❌ **Validation Error:** {text_error}"

# Show validation errors
if error_message and run:
    st.error(error_message)
    st.stop()

# -------------------------
# PROMPT BUILDER
# -------------------------
def build_prompt(mode, resume, job_description, knowledge):

    schema = {
        "summary": "string (max 50 words)",
        "strengths": ["string"],
        "weaknesses": ["string"],
        "improvements": ["string"]
    }

    rules = """
You are a senior career advisor providing resume feedback.

RULES:
- Output ONLY valid JSON
- No markdown
- No explanation
- No extra keys
- No reasoning text
- No trailing commas

RESPONSE QUALITY (CRITICAL):
- Each item in strengths/weaknesses/improvements MUST be a complete sentence (8+ words)
- Single words or short phrases ("Communication", "Teamwork") are NOT acceptable
- Example good strength: "Strong verbal communication and de-escalation skills demonstrated in high-stress disability support settings"
- Example good weakness: "Limited quantifiable achievements — consider adding specific metrics like client caseload numbers or incident reduction percentages"
- Provide 4-5 items per category, each with specific reference to the resume content

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
    """Safely parse JSON with fallback regex extraction."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    except Exception:
        return None
    return None

def validate_json_schema(obj):
    """Validate that LLM response follows expected schema."""
    if not isinstance(obj, dict):
        return False
    
    required_keys = {"summary", "strengths", "weaknesses", "improvements"}
    if not required_keys.issubset(set(obj.keys())):
        return False
    
    # Validate types
    if not isinstance(obj.get("summary"), str):
        return False
    if not isinstance(obj.get("strengths"), list) or not all(isinstance(s, str) for s in obj.get("strengths", [])):
        return False
    if not isinstance(obj.get("weaknesses"), list) or not all(isinstance(w, str) for w in obj.get("weaknesses", [])):
        return False
    if not isinstance(obj.get("improvements"), list) or not all(isinstance(i, str) for i in obj.get("improvements", [])):
        return False
    
    return True


# Persist session-state keys so download clicks don't clear results
for _k, _v in [
    ("_last_result", None),
    ("_last_mode", "Resume Analysis"),
    ("_last_resume", ""),
    ("_last_job_desc", ""),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Treat download/clicks WITHOUT the Analyze button as: show cached results
show_cached = bool(st.session_state["_last_result"]) and not run

if show_cached:
    # Rebuild locally so we have the right names in this block
    result  = st.session_state["_last_result"]
    mode    = st.session_state["_last_mode"]
    resume  = st.session_state["_last_resume"]
    job_description_validated = st.session_state["_last_job_desc"]

    rubric        = score_resume(resume)
    rubric_score  = rubric["rubric_score"]
    rb            = rubric["breakdown"]
    fmt_val       = rb.get("formatting", {}).get("score", 0) * 10
    ats_val       = rb.get("ats_readiness", {}).get("score", 0) * 10
    ach_val       = rb.get("achievement_density", {}).get("score", 0) * 10
    radar_data    = {
        "Formatting":   rb.get("formatting", {}).get("score", 0),
        "ATS Match":    rb.get("ats_readiness", {}).get("score", 0),
        "Experience":   rb.get("experience_quality", {}).get("score", 0),
        "Achievements": rb.get("achievement_density", {}).get("score", 0),
        "Skills":       rb.get("skills_relevance", {}).get("score", 0),
    }

    st.caption("🔄 Showing cached results — re-upload or click Analyze for new results.")


# ── LIVE ANALYSIS PATH (only when user clicks Analyze) ──
if run:

    if not resume.strip():
        st.error("❌ Please provide a resume (minimum 100 characters)")
        st.stop()

    job_description_validated = ""
    if mode == "ATS Job Match":
        if not job_description.strip():
            st.error("❌ Please provide a job description")
            st.stop()
        
        job_description_validated, jd_error = validate_resume_text(job_description, context="job")
        if jd_error:
            st.error(f"❌ Job Description Error: {jd_error}")
            st.stop()
    else:
        job_description_validated = ""

    # BUILD PROMPT
    retrieved_knowledge = rag_engine.retrieve(resume, top_k=3)
    if not retrieved_knowledge:
        retrieved_knowledge = "No specific knowledge chunks matched the resume. Use general best practices."

    prompt = build_prompt(mode, resume, job_description_validated, retrieved_knowledge)

    # DEBUG LOGGING
    log_section("RESUME ANALYSIS STARTED")
    log(f"Mode: {mode}")
    log(f"Resume Length: {len(resume)}")
    if mode == "ATS Job Match":
        log(f"Job Description Length: {len(job_description)}")
    log_section("PROMPT START")
    print(prompt)
    logging.info(prompt)
    log_section("PROMPT END")

    # API CALL
    log("Sending API request...")

    with st.spinner("🤖 AI is analyzing your resume..."):
        response = None
        used_model = None
        model_statuses = []
        
        for attempt, model_id in enumerate(FREE_MODELS, 1):
            status_msg = f"🔄 **Attempt {attempt}/3:** Trying {model_id.split('/')[-1]}..."
            st.write(status_msg)
            
            try:
                log(f"Trying model: {model_id} (attempt {attempt}/3)")
                resp = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = resp.choices[0].message.content
                if content and len(content) > 50:
                    if safe_parse_json(content) is not None:
                        response = resp
                        used_model = model_id
                        log(f"Model {model_id} returned valid JSON")
                        model_statuses.append((model_id, "✅ Success"))
                        st.success(f"✅ **Success!** Using {model_id.split('/')[-1]}")
                        break
                    log(f"Model {model_id} returned non-JSON content, trying next")
                    model_statuses.append((model_id, "⚠️ Invalid JSON"))
                else:
                    log(f"Model {model_id} returned short/empty content, trying next")
                    model_statuses.append((model_id, "⚠️ Empty response"))
            except (ValueError, KeyError, AttributeError, TypeError) as api_error:
                log(f"Model {model_id} failed with error: {type(api_error).__name__}: {str(api_error)}")
                model_statuses.append((model_id, f"❌ {type(api_error).__name__}"))
            except Exception as api_error:
                log(f"Model {model_id} failed with unexpected error: {type(api_error).__name__}: {str(api_error)}")
                model_statuses.append((model_id, f"❌ Error"))

        if response is None:
            st.error("❌ **All free AI models failed.** This is a temporary issue with the free tier service. Please try again in a few moments.\n\n**Tip:** Check your internet connection and verify your OpenRouter API key is valid.")
            with st.expander("📋 Model Status Details"):
                for model_name, status in model_statuses:
                    st.write(f"{status} — {model_name}")
            st.stop()

        log(f"Successfully used model: {used_model}")
        log("API response received")

    # FULL RESPONSE LOG
    try:
        response_json = response.model_dump_json(indent=2)
        log_section("FULL API RESPONSE OBJECT")
        print(response_json)
        logging.info("FULL RESPONSE START")
        logging.info(response_json)
        logging.info("FULL RESPONSE END")
    except (AttributeError, TypeError, ValueError) as log_error:
        log(f"Could not dump full response: {type(log_error).__name__}: {log_error}")

    # RAW OUTPUT
    raw_output = response.choices[0].message.content
    log_section("RAW OUTPUT START")
    print(raw_output)
    logging.info("RAW OUTPUT START")
    logging.info(raw_output)
    logging.info("RAW OUTPUT END")
    log_section("RAW OUTPUT END")

    if raw_output is None:
        log_section("NULL RESPONSE ERROR")
        logging.error("Model returned null content (likely image-only response)")
        st.error("The model returned an image instead of text. Try a different model or resume.")
        st.stop()

    # CLEANING
    cleaned = re.sub(r"```json|```", "", raw_output).strip()
    log_section("CLEANED OUTPUT START")
    print(cleaned)
    logging.info("CLEANED OUTPUT START")
    logging.info(cleaned)
    logging.info("CLEANED OUTPUT END")

    # JSON PARSE & VALIDATION
    log("Attempting JSON parse")
    result = safe_parse_json(cleaned)

    if not result:
        log_section("JSON PARSE ERROR")
        logging.error(f"Failed to parse JSON from: {cleaned}")
        st.error("❌ Model returned invalid JSON. Try again.")
        st.stop()

    if not validate_json_schema(result):
        log_section("JSON SCHEMA VALIDATION ERROR")
        logging.error(f"Schema validation failed for: {json.dumps(result)}")
        st.error("❌ Model response did not match expected format. Try again.")
        st.stop()

    log("JSON parse and schema validation successful")
    st.success("✅ Resume analysis complete")

    # Persist result so download button clicks don't clear the page
    st.session_state["_last_result"] = result
    st.session_state["_last_mode"] = mode
    st.session_state["_last_resume"] = resume
    st.session_state["_last_job_desc"] = job_description_validated

# ── RENDER RESULTS (runs for both live analysis AND cached) ──
if (run or show_cached) and st.session_state.get("_last_result"):
    result = st.session_state["_last_result"]
    mode = st.session_state["_last_mode"]
    resume = st.session_state["_last_resume"]
    job_description_validated = st.session_state["_last_job_desc"]

    rubric = score_resume(resume)
    rubric_score = rubric["rubric_score"]
    rb = rubric["breakdown"]

    # Map rubric breakdown to readable metric names for the score cards
    fmt_val = rb.get("formatting", {}).get("score", 0) * 10
    ats_val = rb.get("ats_readiness", {}).get("score", 0) * 10
    exp_val = rb.get("experience_quality", {}).get("score", 0) * 10
    ach_val = rb.get("achievement_density", {}).get("score", 0) * 10
    skill_val = rb.get("skills_relevance", {}).get("score", 0) * 10

    # Compute canonical Job Fit Score for ATS mode
    job_fit = None
    job_fit_breakdown = None
    if mode == "ATS Job Match" and job_description_validated.strip():
        _last_gap = st.session_state.get("_last_gap")
        _last_sem = _last_gap.get("semantic_matches", []) if _last_gap else []
        if _last_gap and _last_sem:
            try:
                jf = compute_job_fit_score(
                    resume_text=resume,
                    job_description=job_description_validated,
                    gap_result=_last_gap,
                    semantic_matches=_last_sem,
                )
                job_fit = jf["job_fit_score"]
                job_fit_breakdown = jf["breakdown"]
            except Exception as e:
                log(f"Job fit computation failed: {e}")

    # Prepare radar chart data
    radar_data = {
        "Formatting": rb.get("formatting", {}).get("score", 0),
        "ATS Match": rb.get("ats_readiness", {}).get("score", 0),
        "Experience": rb.get("experience_quality", {}).get("score", 0),
        "Achievements": rb.get("achievement_density", {}).get("score", 0),
        "Skills": rb.get("skills_relevance", {}).get("score", 0),
    }

    # Build score cards based on mode to avoid misleading labels
    if mode == "ATS Job Match" and job_description_validated.strip():
        if job_fit is not None:
            # ATS mode: single Job Fit Score + resume quality sub-scores
            fit_color = score_color(job_fit)
            card1_label, card1_val, card1_color = "Job Fit Score", job_fit, fit_color
            card2_label, card2_val, card2_color = "Resume Quality", rubric_score, score_color(rubric_score)
            card3_label, card3_val, card3_color = "Formatting", fmt_val, score_color(fmt_val)
            card4_label, card4_val, card4_color = "Achievements", ach_val, score_color(ach_val)
        else:
            # Fallback without semantic data
            coverage_val = int(gap.get("keyword_coverage", 0)) if 'gap' in dir() else 0
            card1_label, card1_val, card1_color = "Resume Quality", rubric_score, score_color(rubric_score)
            card2_label, card2_val, card2_color = "Keyword Coverage", coverage_val, score_color(coverage_val)
            card3_label, card3_val, card3_color = "Formatting", fmt_val, score_color(fmt_val)
            card4_label, card4_val, card4_color = "Achievements", ach_val, score_color(ach_val)
    else:
        # Resume Analysis mode: keep original labels
        card1_label, card1_val, card1_color = "Overall Score", rubric_score, score_color(rubric_score)
        card2_label, card2_val, card2_color = "ATS Match", ats_val, score_color(ats_val)
        card3_label, card3_val, card3_color = "Formatting", fmt_val, score_color(fmt_val)
        card4_label, card4_val, card4_color = "Achievements", ach_val, score_color(ach_val)

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(f'<div class="score-card" style="border-top-color: {card1_color};"><div class="label">{card1_label}</div><div class="value" style="color: {card1_color};">{card1_val}</div><div>/ 100</div></div>', unsafe_allow_html=True)
    with mcol2:
        st.markdown(f'<div class="score-card" style="border-top-color: {card2_color};"><div class="label">{card2_label}</div><div class="value" style="color: {card2_color};">{card2_val}</div><div>/ 100</div></div>', unsafe_allow_html=True)
    with mcol3:
        st.markdown(f'<div class="score-card" style="border-top-color: {card3_color};"><div class="label">{card3_label}</div><div class="value" style="color: {card3_color};">{card3_val}</div><div>/ 100</div></div>', unsafe_allow_html=True)
    with mcol4:
        st.markdown(f'<div class="score-card" style="border-top-color: {card4_color};"><div class="label">{card4_label}</div><div class="value" style="color: {card4_color};">{card4_val}</div><div>/ 100</div></div>', unsafe_allow_html=True)

    st.divider()

    gauge_col, radar_col = st.columns(2)
    with gauge_col:
        render_score_gauge(rubric_score)
    with radar_col:
        render_radar(radar_data)

    with st.expander("📏 Rubric Scoring (deterministic — weighted criteria)", expanded=True):
        st.markdown("**How the score is calculated:**")
        st.markdown(f"**Overall Score = {rubric_score}/100** — purely structural. No AI involvement in scoring.")
        st.markdown("The rubric measures resume structure, formatting, experience depth, achievement density, and skill relevance using deterministic rules.")
        st.divider()
        rcols = st.columns(len(rubric["breakdown"]))
        for i, (key, cat) in enumerate(rubric["breakdown"].items()):
            with rcols[i]:
                label = key.replace("_", " ").title()
                weight = f"{int(cat['weight']*100)}%"
                st.metric(label=f"{label} ({weight})", value=f"{cat['score']}/10")
        st.divider()
        st.markdown("**📋 Resume Statistics:**")
        display_stats = {k: v for k, v in rubric["stats"].items() if not isinstance(v, list)}
        scols = st.columns(len(display_stats))
        for i, (key, val) in enumerate(display_stats.items()):
            with scols[i]:
                st.metric(label=key.replace("_", " ").title(), value=val)
        if "sections_detected" in rubric["stats"]:
            sections = rubric["stats"]["sections_detected"]
            if sections:
                st.markdown(f"**Sections Found:** {', '.join(sections)}")
        st.divider()
        st.markdown("**📝 Rubric Notes:**")
        for note in rubric["all_notes"]:
            st.markdown(f"- {note}")

    st.divider()

    summary_text = html.escape(result.get("summary", ""))
    st.markdown(f'<div class="summary-box"><h4>📌 Executive Summary</h4><p>{summary_text}</p></div>', unsafe_allow_html=True)

    render_styled_list("Strengths", result.get("strengths", []), "card-green", "💪")
    render_styled_list("Weaknesses", result.get("weaknesses", []), "card-amber", "⚠️")
    render_styled_list("Improvements", result.get("improvements", []), "card-blue", "🚀")

    if mode == "ATS Job Match" and job_description_validated.strip():
        st.divider()
        st.markdown("## 🔍 ATS Keyword Gap Analysis")
        st.caption("Deterministic keyword matching between your resume and the job description (no AI involved)")
        log_section("ATS GAP ANALYSIS STARTED")
        with st.spinner("🧮 Computing keyword match..."):
            gap = analyze_ats_gap(resume, job_description_validated)

        # Semantic matching layer (explanation-only, uses existing BGE embedder)
        if gap.get("semantic_matches") is None:
            gap["semantic_matches"] = []
        if not gap["semantic_matches"] and rag_engine:
            try:
                semantic = compute_semantic_matches(
                    resume, job_description_validated,
                    embed_fn=rag_engine.embedder.encode,
                    threshold=0.70,
                )
                gap["semantic_matches"] = semantic
                log(f"Semantic matches found: {len(semantic)}")
            except Exception as sem_error:
                log(f"Semantic matching failed: {type(sem_error).__name__}: {sem_error}")

        # Cache gap for score card computation above
        st.session_state["_last_gap"] = gap
        log(f"ATS Coverage: {gap['keyword_coverage']}%")
        log(f"Matched: {gap['matched_count']}, Missing: {gap['missing_count']}")
        log(f"Total job keywords: {gap['total_job_keywords']}")

        coverage = gap["keyword_coverage"]
        coverage_color = "#10B981" if coverage >= 60 else ("#F59E0B" if coverage >= 30 else "#F43F5E")
        gcol1, gcol2, gcol3 = st.columns(3)
        with gcol1:
            st.markdown(f'<div class="score-card" style="border-top-color: {coverage_color};"><div class="label">Keyword Coverage</div><div class="value" style="color: {coverage_color};">{coverage}%</div><div>{gap["matched_count"]} matched · {gap["missing_count"]} missing</div></div>', unsafe_allow_html=True)
        with gcol2:
            st.markdown(f'<div class="score-card" style="border-top-color: #10B981;"><div class="label">Matched Keywords</div><div class="value" style="color: #10B981;">{gap["matched_count"]}</div><div>out of {gap["total_job_keywords"]} job keywords</div></div>', unsafe_allow_html=True)
        with gcol3:
            missing_color = "#F43F5E" if gap["missing_count"] > 10 else "#F59E0B"
            st.markdown(f'<div class="score-card" style="border-top-color: {missing_color};"><div class="label">Missing Keywords</div><div class="value" style="color: {missing_color};">{gap["missing_count"]}</div><div>need to add to resume</div></div>', unsafe_allow_html=True)

        # Concept-level coverage (ontology layer)
        concept_cov = gap.get("concept_coverage", 0)
        concept_matched_count = len(gap.get("concept_matched", []))
        concept_missing_count = len(gap.get("concept_missing", []))
        concept_total = concept_matched_count + concept_missing_count
        concept_color = "#10B981" if concept_cov >= 60 else ("#F59E0B" if concept_cov >= 30 else "#F43F5E")
        ccol1, ccol2, ccol3 = st.columns(3)
        with ccol1:
            st.markdown(f'<div class="score-card" style="border-top-color: {concept_color};"><div class="label">Concept Coverage</div><div class="value" style="color: {concept_color};">{concept_cov}%</div><div>normalized skill concepts</div></div>', unsafe_allow_html=True)
        with ccol2:
            st.markdown(f'<div class="score-card" style="border-top-color: #6366F1;"><div class="label">Matched Concepts</div><div class="value" style="color: #6366F1;">{concept_matched_count}</div><div>shared skill areas</div></div>', unsafe_allow_html=True)
        with ccol3:
            st.markdown(f'<div class="score-card" style="border-top-color: #F59E0B;"><div class="label">Missing Concepts</div><div class="value" style="color: #F59E0B;">{concept_missing_count}</div><div>gaps in skill areas</div></div>', unsafe_allow_html=True)

        st.divider()
        if gap["critical_missing"]:
            critical_html = "".join(f'<span class="keyword-tag critical">⚠ {kw}</span>' for kw in gap["critical_missing"])
            st.markdown(f'<div style="background: rgba(244,63,94,0.08); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #F43F5E;"><h4 style="color: #F43F5E; margin: 0 0 0.5rem 0;">🔴 Critical Missing Keywords</h4><p style="color: #CBD5E1; font-size: 0.85rem; margin: 0 0 0.5rem 0;">These keywords appear multiple times in the job description but are absent from your resume. Adding them significantly improves ATS ranking.</p><div>{critical_html}</div></div>', unsafe_allow_html=True)

        if gap["other_missing"]:
            other_html = "".join(f'<span class="keyword-tag other">{kw}</span>' for kw in gap["other_missing"])
            st.markdown(f'<div style="background: rgba(245,158,11,0.08); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #F59E0B;"><h4 style="color: #F59E0B; margin: 0 0 0.5rem 0;">🟡 Other Missing Keywords</h4><p style="color: #CBD5E1; font-size: 0.85rem; margin: 0 0 0.5rem 0;">These keywords appear in the job description but not in your resume. Consider adding relevant ones.</p><div>{other_html}</div></div>', unsafe_allow_html=True)

        if gap["matched_keywords"]:
            matched_html = "".join(f'<span class="keyword-tag matched">✓ {kw}</span>' for kw in gap["matched_keywords"])
            st.markdown(f'<div style="background: rgba(0,188,125,0.08); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #00BC7D;"><h4 style="color: #00BC7D; margin: 0 0 0.5rem 0;">✅ Matched Keywords</h4><p style="color: #CBD5E1; font-size: 0.85rem; margin: 0 0 0.5rem 0;">These keywords appear in both your resume and the job description.</p><div>{matched_html}</div></div>', unsafe_allow_html=True)

        if gap["missing_count"] > 0:
            st.info(f"💡 **Tip:** Aim for at least 60% keyword coverage. Your current coverage is **{coverage}%**. Review the missing keywords above and incorporate relevant ones into your resume's Skills, Experience, and Summary sections.")
        else:
            st.success("✅ **Excellent keyword coverage!** Your resume contains all detected keywords from the job description.")

        # Semantic Matches (AI-understood equivalences) — insight badge, not a score
        st.divider()
        semantic_matches = gap.get("semantic_matches", [])
        if semantic_matches:
            hard_matches = [m for m in semantic_matches if m.get("type") == "HARD_MATCH"]
            soft_matches = [m for m in semantic_matches if m.get("type") == "SOFT_MATCH"]

            st.markdown("## 🧠 AI-Detected Equivalences")
            st.caption("These JD phrases match concepts in your resume — even when the keywords differ. This is an explanation layer, not a score.")

            # Summary line
            st.markdown(
                f"**{len(hard_matches)} strong** and **{len(soft_matches)} partial** semantic matches found "
                f"across **{gap.get('total_job_keywords', 0)}** JD concepts."
            )

            if hard_matches:
                st.markdown("**Strong equivalences:**")
                hard_html = "".join(
                    f'<span style="display: inline-flex; align-items: center; background: rgba(0,188,125,0.1); color: #10B981; '
                    f'padding: 0.3rem 0.7rem; margin: 0.2rem; border-radius: 6px; font-size: 0.85rem; border: 1px solid rgba(0,188,125,0.25);">'
                    f'<b>{html.escape(m["job"])}</b> → {html.escape(m["resume"])} <span style="opacity:0.7; font-size:0.75rem;">({m["score"]})</span></span>'
                    for m in hard_matches[:8]
                )
                st.markdown(f'<div style="margin-bottom: 0.8rem;">{hard_html}</div>', unsafe_allow_html=True)

            if soft_matches:
                st.markdown("**Partial equivalences:**")
                soft_html = "".join(
                    f'<span style="display: inline-flex; align-items: center; background: rgba(99,102,241,0.1); color: #818CF8; '
                    f'padding: 0.3rem 0.7rem; margin: 0.2rem; border-radius: 6px; font-size: 0.85rem; border: 1px solid rgba(99,102,241,0.25);">'
                    f'<b>{html.escape(m["job"])}</b> → {html.escape(m["resume"])} <span style="opacity:0.7; font-size:0.75rem;">({m["score"]})</span></span>'
                    for m in soft_matches[:8]
                )
                st.markdown(f'<div style="margin-bottom: 0.8rem;">{soft_html}</div>', unsafe_allow_html=True)

    st.divider()
    st.caption("💾 Use the download buttons at the bottom of this page.")

    log_section("PIPELINE COMPLETE")
    log("All processing finished successfully")

# -------------------------
# PERSISTENT DOWNLOAD BUTTONS (outside run block)
# These render from session_state so clicking them doesn't clear the page
# -------------------------
_cached_result = st.session_state.get("_last_result")
if _cached_result:
    _cached_mode = st.session_state.get("_last_mode", "Resume Analysis")
    _cached_resume = st.session_state.get("_last_resume", "")
    _cached_rubric = score_resume(_cached_resume)
    _cached_rubric_score = _cached_rubric["rubric_score"]
    st.divider()
    _dl_col1, _dl_col2 = st.columns(2)
    with _dl_col1:
        _pdf_bytes = generate_pdf_report(_cached_result, _cached_mode, _cached_rubric_score)
        st.download_button(
            label="📥 Download PDF Report",
            data=_pdf_bytes,
            file_name=f"resume_{_cached_mode.lower().replace(' ', '_')}_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="persistent_pdf_download",
        )
    with _dl_col2:
        if LOG_FILE.exists():
            with open(LOG_FILE, "r") as _log_file:
                _log_data = _log_file.read()
            st.download_button(
                label="📋 Download Debug Logs",
                data=_log_data,
                file_name=f"debug_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                key="persistent_logs_download",
            )
