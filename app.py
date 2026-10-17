import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from services.model_service import load_model_and_scaler
from services.review_analysis import review_summary
from services.report_service import (
    build_indicator_contributions,
    build_review_report_data,
    count_review_comparisons,
    summarize_history,
)
import json
from pathlib import Path
from services.risk_service import get_model_probabilities
from services.data_service import append_history, load_history

st.set_page_config(
    page_title="Trustline | Seller Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- DESIGN SYSTEM --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&family=Playfair+Display:wght@600;700&display=swap');
:root {
  --app-bg:#F8F3F2;
  --surface:#FFFCFB;
  --surface-white:#FFFFFF;
  --text-primary:#211516;
  --text-secondary:#777078;
  --text-muted:#989098;
  --border:#F0E3E5;
  --rose-primary:#BE5B7B;
  --rose-hover:#9F3458;
  --rose-soft:#F9E6EA;
  --lavender-soft:#EAEAFF;
  --mint-soft:#DDF5EB;
  --success:#10B981;
  --warning:#F3B64B;
  --danger:#F06472;
}
html, body, [class*="css"] {font-family:'DM Sans',Arial,sans-serif;}
[data-testid="stAppViewContainer"], .stApp {background:var(--app-bg);color:var(--text-primary);}
[data-testid="stMainBlockContainer"] {color:var(--text-primary);}
[data-testid="stHeader"] {background:var(--app-bg);}
[data-testid="stSidebar"] {background:var(--surface);border-right:1px solid var(--border);}
@media(min-width:701px){[data-testid="stSidebar"] {width:288px!important;min-width:288px!important;}}
[data-testid="stSidebar"] > div:first-child {padding-top:1.35rem;}
[data-testid="stSidebar"] * {font-family:'DM Sans',Arial,sans-serif;}
[data-testid="stSidebar"] h5 {font-size:13px!important;font-weight:700!important;letter-spacing:1.5px;color:var(--text-muted)!important;text-transform:uppercase;}
.block-container {max-width:1420px;padding-top:2rem;padding-bottom:4rem;padding-left:2rem;padding-right:2rem;}
h1,h2,h3,h4 {font-family:'Playfair Display','DM Serif Display',Georgia,serif!important;color:var(--text-primary);letter-spacing:-.35px;line-height:1.2;}
h1 {font-size:34px!important;font-weight:700!important;margin-bottom:.35rem!important;}
h2 {font-size:26px!important;font-weight:700!important;margin-top:.35rem!important;}
h3 {font-size:24px!important;font-weight:700!important;}
h4 {font-size:24px!important;font-weight:600!important;}
p, label, [data-testid="stCaptionContainer"] {color:var(--text-primary);font-size:17px;}
[data-testid="stCaptionContainer"] p {color:var(--text-secondary)!important;line-height:1.55;font-size:14px!important;}
[data-testid="stMarkdownContainer"] p {line-height:1.55;font-size:17px;}
[data-testid="stWidgetLabel"] p {font-size:17px!important;}
[data-testid="stVerticalBlock"] {gap:.85rem;}
[data-testid="stHorizontalBlock"] {gap:1rem;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {line-height:1.55;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border-radius:12px;padding:.62rem .75rem;color:var(--text-secondary)!important;
  font-weight:600;transition:background-color .15s ease,color .15s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {display:none;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] p {color:var(--text-secondary)!important;}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:var(--rose-soft);}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
[data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]) {
  background:var(--rose-soft);color:var(--rose-hover)!important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has([aria-checked="true"]) p {color:var(--rose-hover)!important;}
[data-testid="stMetric"] {
  background:var(--surface);border:1px solid var(--border);border-radius:17px;
  padding:18px 20px;box-shadow:0 4px 16px rgba(90,45,58,.03);
}
[data-testid="stMetricLabel"] {
  color:var(--text-secondary)!important;font-size:14px;font-weight:600;line-height:1.3;
  white-space:normal!important;overflow:visible!important;text-overflow:clip!important;
  overflow-wrap:anywhere;
}
[data-testid="stMetricValue"] {color:var(--text-primary)!important;font-weight:700;font-size:30px;}
[data-testid="stMetricDelta"] {color:var(--text-secondary)!important;}
[data-testid="stMetricDelta"] {font-size:.75rem;}
.hero {
  background:linear-gradient(112deg,#fffefd 0%,#fffcfb 100%);
  border:1px solid var(--border);border-radius:26px;padding:32px 36px;margin-bottom:20px;
  box-shadow:0 8px 24px rgba(90,45,58,.035);
}
.eyebrow,.section-kicker {
  color:var(--rose-hover);font-size:13px;font-weight:700;letter-spacing:1.5px;
  text-transform:uppercase;margin-bottom:10px;
}
.hero-title {font-family:'Playfair Display',Georgia,serif!important;font-size:clamp(31px,3.4vw,46px);
  line-height:1.1;color:var(--text-primary);margin:0 0 13px;font-weight:700;letter-spacing:-1.1px;}
.hero-copy {font-size:17px;line-height:1.65;color:var(--text-secondary);max-width:650px;margin-bottom:14px;}
.hero-aside {background:var(--surface);border:1px solid var(--border);
  border-radius:19px;padding:20px 21px;box-shadow:0 5px 18px rgba(90,45,58,.03);}
.hero-aside-title {font-family:'Playfair Display',Georgia,serif;font-size:19px;font-weight:700;
  color:var(--text-primary);margin-bottom:12px;}
.hero-signal {display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:9px 0;border-top:1px solid var(--border);font-size:14px;color:var(--text-primary);}
.hero-signal-label {font-weight:600;}
.hero-signal-note {display:block;color:var(--text-muted);font-size:13px;font-weight:400;margin-top:2px;}
.hero-tag {flex:0 0 auto;background:var(--rose-soft);border-radius:999px;padding:4px 8px;
  color:var(--rose-hover);font-size:12px;font-weight:700;letter-spacing:.4px;}
.hero-tag.neutral {background:#f2eeeb;color:#706866;}
.sidebar-brand {display:flex;align-items:center;gap:8px;font-family:'Playfair Display','DM Serif Display',Georgia,serif;font-size:26px;font-weight:700;color:var(--text-primary);letter-spacing:-.5px;line-height:1.1;}
.sidebar-brand-icon {display:inline-flex;align-items:center;justify-content:center;font-family:'DM Sans',Arial,sans-serif;font-size:24px;line-height:1;flex:0 0 24px;}
.sidebar-subtitle {font-size:12px;letter-spacing:1.25px;color:var(--text-muted);font-weight:700;margin:4px 0 12px 40px;}
.sidebar-status {background:var(--surface-white);border:1px solid var(--border);border-radius:13px;padding:12px;
  color:var(--text-secondary);font-size:15px;line-height:1.55;}
.panel-title {font-size:13px;font-weight:700;letter-spacing:1.5px;color:var(--text-muted);text-transform:uppercase;}
div[data-testid="stVerticalBlockBorderWrapper"] {
  background:var(--surface);border:1px solid var(--border);border-radius:20px;
  box-shadow:0 5px 18px rgba(90,45,58,.03);
  padding:4px;
}
div[data-testid="stExpander"] {background:var(--surface);border:1px solid var(--border);border-radius:12px;}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button {
  background:var(--surface-white);color:var(--text-primary);
  border-radius:12px;min-height:42px;font-weight:600;border:1px solid var(--border);
  transition:all .15s ease;
}
.stButton>button:not([kind="primary"]):not(:disabled):hover,
.stDownloadButton>button:not(:disabled):hover,
.stFormSubmitButton>button:not([kind="primary"]):not(:disabled):hover {
  background:var(--rose-soft);color:var(--rose-hover);border-color:var(--border);
}
.stButton>button:disabled,.stDownloadButton>button:disabled,
.stFormSubmitButton>button:disabled {
  background:#F7F2F1;color:var(--text-muted);border-color:var(--border);
  opacity:1;cursor:not-allowed;
}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"] {
  background:var(--rose-primary);color:white;border:1px solid var(--rose-primary);
}
.stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primary"]:hover {
  background:var(--rose-hover);color:white;border-color:var(--rose-hover);
}
[data-testid="stTextInput"] [data-baseweb="input"]>div,
[data-testid="stNumberInput"] [data-baseweb="input"]>div,
[data-testid="stSelectbox"] [data-baseweb="select"]>div,
[data-testid="stMultiSelect"] [data-baseweb="select"]>div,
[data-testid="stTextArea"] [data-baseweb="textarea"]>div {
  background:var(--surface-white)!important;
  border:1px solid var(--border)!important;border-radius:10px!important;
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
  color:var(--text-primary)!important;background-color:var(--surface-white)!important;
  caret-color:var(--rose-primary);
}
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stSelectbox"] [data-baseweb="select"]>div,
[data-testid="stMultiSelect"] [data-baseweb="select"]>div {
  color:var(--text-primary)!important;background:var(--surface-white)!important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] [role="combobox"],
[data-testid="stMultiSelect"] [data-baseweb="select"] [role="combobox"] {
  color:var(--text-primary)!important;background:transparent!important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stMultiSelect"] [data-baseweb="select"] * {
  color:var(--text-primary)!important;background-color:transparent!important;
}
.st-key-history-status-filter [data-baseweb="select"],
.st-key-history-status-filter [data-baseweb="select"] *,
.st-key-history-category-filter [data-baseweb="select"],
.st-key-history-category-filter [data-baseweb="select"] * {
  color:#211516!important;background-color:#FFFFFF!important;
}
.st-key-history-status-filter [data-baseweb="select"]>div,
.st-key-history-category-filter [data-baseweb="select"]>div {
  border:1px solid #F0E3E5!important;border-radius:10px!important;
}
.st-key-history-status-filter [data-baseweb="select"]:focus-within>div,
.st-key-history-category-filter [data-baseweb="select"]:focus-within>div {
  border-color:#BE5B7B!important;
  box-shadow:0 0 0 2px rgba(190,91,123,.16)!important;
}
.st-key-history-html-table [data-testid="stMarkdownContainer"] {
  max-width:100%;overflow-x:auto;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stNumberInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {color:var(--text-muted)!important;opacity:1;}
[data-testid="stTextInput"] [data-baseweb="input"]>div:focus-within,
[data-testid="stNumberInput"] [data-baseweb="input"]>div:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"]>div:focus-within,
[data-testid="stMultiSelect"] [data-baseweb="select"]>div:focus-within,
[data-testid="stTextArea"] [data-baseweb="textarea"]>div:focus-within {
  border-color:var(--rose-primary)!important;
  box-shadow:0 0 0 2px rgba(190,91,123,.16);
}
[data-testid="stTextInput"]:has([aria-invalid="true"]) [data-baseweb="input"]>div,
[data-testid="stNumberInput"]:has([aria-invalid="true"]) [data-baseweb="input"]>div,
[data-testid="stSelectbox"]:has([aria-invalid="true"]) [data-baseweb="select"]>div,
[data-testid="stMultiSelect"]:has([aria-invalid="true"]) [data-baseweb="select"]>div,
[data-testid="stTextArea"]:has([aria-invalid="true"]) [data-baseweb="textarea"]>div {
  border-color:var(--danger)!important;
  box-shadow:0 0 0 2px rgba(240,100,114,.12);
}
[data-testid="stTextInput"] input:disabled,
[data-testid="stNumberInput"] input:disabled,
[data-testid="stTextArea"] textarea:disabled,
[data-testid="stSelectbox"] [aria-disabled="true"],
[data-testid="stMultiSelect"] [aria-disabled="true"] {
  color:var(--text-muted)!important;background-color:#F7F2F1!important;
  -webkit-text-fill-color:var(--text-muted);
}
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [role="listbox"] {
  background:var(--surface-white)!important;border:1px solid var(--border);
  border-radius:10px;box-shadow:0 8px 22px rgba(90,45,58,.08);
}
[data-baseweb="popover"] [role="option"] {color:var(--text-primary)!important;}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"],
[data-baseweb="popover"] [data-baseweb="menu-item"]:hover,
[data-baseweb="popover"] [data-baseweb="menu-item"][aria-selected="true"] {
  background:var(--rose-soft)!important;color:var(--rose-hover)!important;
}
[data-testid="stTextInput"] input:focus-visible,
[data-testid="stNumberInput"] input:focus-visible,
[data-testid="stTextArea"] textarea:focus-visible,
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible,
.stFormSubmitButton>button:focus-visible {
  outline:2px solid rgba(190,91,123,.55);outline-offset:2px;
}
[data-testid="stDataFrame"] {
  color:var(--text-primary);background:var(--surface);
  border:1px solid var(--border);border-radius:12px;overflow:hidden;
}
[data-testid="stTable"] {
  color:var(--text-primary);background:var(--surface);
  border:1px solid var(--border);border-radius:12px;overflow:hidden;
}
[data-testid="stTable"] th {
  color:var(--text-primary);background:var(--app-bg);
  border-color:var(--border);
}
[data-testid="stTable"] td {
  color:var(--text-primary);background:var(--surface);
  border-color:var(--border);
}
[data-testid="stAlert"] {
  background:var(--surface);border:1px solid var(--border);border-radius:12px;
  box-shadow:0 3px 12px rgba(90,45,58,.025);
}
hr {border-color:var(--border);}
div[data-testid="stRadio"] label {font-size:.94rem;}
.report-banner {background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:22px 24px;}
.report-label {font-size:10px;font-weight:700;letter-spacing:1.8px;color:#287557;text-transform:uppercase;}
.pill {display:inline-block;border-radius:20px;padding:5px 10px;font-size:11px;font-weight:700;}
.pipeline-step {background:var(--surface);border:1px solid var(--border);border-radius:15px;padding:16px;text-align:center;min-height:100px;}
.pipeline-number {color:#8974d4;font-size:11px;font-weight:700;letter-spacing:1px;}
.pipeline-title {font-weight:700;color:#302a43;margin:7px 0 4px;}
.pipeline-copy {font-size:12px;color:#77718a;line-height:1.5;}
.block-container:has(.dashboard-page-marker) {padding-top:1.35rem;padding-bottom:2.25rem;}
.block-container:has(.dashboard-page-marker) > [data-testid="stVerticalBlock"] {gap:.6rem;}
.block-container:has(.dashboard-page-marker) .st-key-dashboard_hero {
  background:
    radial-gradient(ellipse at 82% 52%,rgba(247,225,215,.48) 0%,rgba(255,252,251,0) 44%),
    linear-gradient(112deg,#fffefd 0%,#fffcfb 100%);
  border:1px solid var(--border);border-radius:26px;padding:30px 34px;
  box-shadow:0 8px 24px rgba(90,45,58,.035);overflow:hidden;
}
.block-container:has(.dashboard-page-marker) .st-key-dashboard_hero [data-testid="stVerticalBlock"] {gap:.55rem;}
.block-container:has(.dashboard-page-marker) .st-key-dashboard_hero .hero-title {font-size:clamp(34px,3.2vw,46px);max-width:690px;}
.block-container:has(.dashboard-page-marker) .st-key-dashboard_hero .hero-copy {max-width:660px;}
.block-container:has(.dashboard-page-marker) .st-key-dashboard_hero [data-testid="stImage"] {
  display:flex;align-items:center;justify-content:center;height:100%;overflow:hidden;border-radius:19px;
}
.block-container:has(.dashboard-page-marker) .st-key-dashboard_hero [data-testid="stImage"] img {
  display:block;width:100%;height:auto;max-height:270px;object-fit:contain;border-radius:19px;
  -webkit-mask-image:radial-gradient(ellipse 78% 90% at 68% 50%,#000 48%,rgba(0,0,0,.94) 60%,transparent 100%);
  mask-image:radial-gradient(ellipse 78% 90% at 68% 50%,#000 48%,rgba(0,0,0,.94) 60%,transparent 100%);
  -webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;
  -webkit-mask-size:100% 100%;mask-size:100% 100%;
}
.block-container:has(.dashboard-page-marker) [data-testid="stMetric"] {
  min-height:104px;height:100%;box-sizing:border-box;padding:16px 17px;
  background:var(--surface);border:1px solid var(--border);border-radius:18px;
  box-shadow:0 4px 16px rgba(90,45,58,.03);
}
.block-container:has(.dashboard-page-marker) [data-testid="stMetricLabel"] {font-size:15px;line-height:1.35;}
.block-container:has(.dashboard-page-marker) [data-testid="stMetricValue"] {font-size:30px;line-height:1.2;}
.block-container:has(.dashboard-page-marker) .dashboard-section-heading {
  display:flex;align-items:baseline;gap:12px;margin:3px 0 1px;
}
.block-container:has(.dashboard-page-marker) .dashboard-section-heading .section-kicker {margin:0;}
.block-container:has(.dashboard-page-marker) .dashboard-section-title {
  font-family:'Playfair Display',Georgia,serif;font-size:23px;font-weight:700;
  color:var(--text-primary);letter-spacing:-.35px;
}
.block-container:has(.dashboard-page-marker) .st-key-dashboard_recent_panel,
.block-container:has(.dashboard-page-marker) .st-key-dashboard_capability_panel {
  height:100%;box-sizing:border-box;padding:11px 13px;border-radius:20px!important;
  background:var(--surface);border:1px solid var(--border)!important;
  box-shadow:0 5px 18px rgba(90,45,58,.03);
}
.block-container:has(.dashboard-page-marker) .empty-state {
  background:var(--surface);border:1px solid var(--border);border-radius:15px;padding:19px 18px;
  color:var(--text-secondary);font-size:15px;line-height:1.6;
}
.block-container:has(.dashboard-page-marker) .empty-state strong {
  display:block;color:var(--text-primary);font-size:17px;margin-bottom:4px;
}
[data-testid="stAlert"] p {color:var(--text-primary)!important;}
@media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.hero{padding:30px 26px}}
@media(max-width:700px){
  .hero{padding:25px 22px}.block-container{padding-top:1rem}.hero-title{font-size:31px!important}
  h1{font-size:32px!important}h2{font-size:24px!important}h3{font-size:24px!important}
  [data-testid="stMetricValue"]{font-size:29px!important}
  .block-container:has(.dashboard-page-marker) .st-key-dashboard_hero {padding:23px 20px;border-radius:21px;}
  .block-container:has(.dashboard-page-marker) .st-key-dashboard_hero [data-testid="stImage"] img {max-height:220px;}
}
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE --------------------
for key, default in {
    "history": [],
    "history_load_error": None,
    "last_review_result": None,
    "last_report": None,
    "last_score_details": None,
    "model_load_status": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------- HELPERS --------------------
def chart_style(fig, height=320):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#51484b", size=15),
        title=None, height=height,
        margin=dict(l=20, r=20, t=22, b=22),
        legend=dict(font=dict(color="#51484b", size=15))
    )
    gridcolor = "#DCCAD0" if page in ("Analytics", "History") else "#ece7f3"
    fig.update_xaxes(title=None, showline=False, showgrid=True, gridcolor=gridcolor,
                     zeroline=False, tickfont=dict(color="#51484b", size=15))
    fig.update_yaxes(showgrid=True, gridcolor=gridcolor, zeroline=False,
                     tickfont=dict(color="#51484b", size=15))
    return fig

ROOT = Path(__file__).parent
SAMPLES_PATH = ROOT / "models" / "demo_samples.json"
METRICS_PATH = ROOT / "models" / "model_metrics.json"
EXPERIMENTS_PATH = ROOT / "models" / "experiments.json"
HISTORY_PATH = ROOT / "data" / "history.csv"

@st.cache_resource
def get_model():
    return load_model_and_scaler()

@st.cache_data
def load_samples():
    return json.loads(SAMPLES_PATH.read_text(encoding="utf-8")) if SAMPLES_PATH.exists() else []

@st.cache_data
def load_metrics():
    return json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else None

def concern_band(score):
    if score >= 70: return "Low concern", "#258363", "#e0f2e9"
    if score >= 40: return "Moderate concern", "#a8730f", "#f8efd9"
    return "High concern", "#b4414f", "#f8e2e8"

def render_model_demo():
    samples = load_samples()
    with st.container(border=True):
        st.markdown("#### Try the model on a real YelpChi test sample")
        st.caption("Dataset demonstration: the model receives only the 32 numerical features. It is not analysing a seller, a URL or review text.")
        if not samples:
            st.info("Add models/demo_samples.json (from the Kaggle export cell) to enable this demo.")
            return
        idx = st.selectbox("YelpChi test sample", range(len(samples)), key="demo_sample",
                           format_func=lambda i: f"Sample {samples[i]['id']} (test row {samples[i]['test_index']})")
        if st.button("Run model on this sample", type="primary", key="run_demo"):
            try:
                model, scaler = get_model()
                sample = samples[idx]
                out = get_model_probabilities(sample["features"], model, scaler)
            except Exception as exc:
                st.error(f"Could not run the model: {exc}")
                return
            pred = int(out["class_1_probability"] >= out["class_0_probability"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Predicted class", f"class_{pred}")
            c2.metric("Class 1 score", f"{out['class_1_probability']:.1%}")
            c3.metric("Dataset label (not given to model)", f"class_{sample['true_label']}")
            st.progress(out["class_1_probability"])
            if pred == sample["true_label"]:
                st.success("The prediction matches the dataset label for this sample.")
            else:
                st.warning("The prediction differs from the dataset label. Precision is modest; see Analytics.")
            st.caption(out["notice"])

def page_header(kicker, title, description):
    st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)

def compute_provisional_indicator(review_result, account_age, rating, review_count, price):
    """
    Transparent, unvalidated heuristic indicator (0-100).
    This is NOT a trained seller-fraud prediction and must be labelled as provisional.
    Higher values mean more reassuring submitted signals, not proof of trustworthiness.
    """
    score = 50.0
    reasons = []
    total_reviews = int(review_result.get("total_reviews", 0))
    pairs = int(review_result.get("similar_pair_count", 0))
    possible_pairs = total_reviews * (total_reviews - 1) / 2
    if total_reviews >= 2 and possible_pairs:
        ratio = pairs / possible_pairs
        penalty = min(30.0, ratio * 100)
        score -= penalty
        if pairs:
            reasons.append(("Caution", f"{pairs} similar review pair(s) were found among {int(possible_pairs)} compared pairs.", -penalty))
        else:
            reasons.append(("Neutral", "No submitted review pairs crossed the similarity threshold.", 0))
    else:
        reasons.append(("Missing data", "At least two reviews are needed for a similarity signal.", 0))
    if account_age > 0:
        bonus = min(12.0, (account_age / 365.0) * 4.0)
        score += bonus
        reasons.append(("Submitted detail", f"Account age entered as {account_age} days; a small age-based adjustment was applied.", bonus))
    else:
        reasons.append(("Missing data", "Account age was not provided.", 0))
    if rating > 0:
        adjustment = max(-5.0, min(5.0, (rating - 3.0) * 2.5))
        score += adjustment
        reasons.append(("Submitted detail", f"Entered rating is {rating:.1f}/5; ratings are user-provided and unverified.", adjustment))
    else:
        reasons.append(("Missing data", "Average rating was not provided.", 0))
    if review_count > 0:
        bonus = min(3.0, review_count / 500.0)
        score += bonus
        reasons.append(("Submitted detail", f"Entered review count is {review_count}; this is not independently verified.", bonus))
    if price > 0:
        reasons.append(("Not assessed", "Price was entered, but no reliable market-price comparison is connected.", 0))
    score = max(0.0, min(100.0, score))
    confidence = "Low" if total_reviews < 2 or (account_age == 0 and rating == 0 and review_count == 0) else "Limited"
    return round(score), confidence, reasons

def status_for_result(result, score, confidence):
    if result.get("similar_pair_count", 0) > 0:
        return "Review recommended"
    if confidence == "Low":
        return "Insufficient evidence"
    return "No similarity signal found"

def make_history_frame(records):
    if not records:
        return pd.DataFrame(columns=["date", "seller", "category", "reviews", "similar_pairs", "status", "indicator"])
    return pd.DataFrame(records)

def go_to_detection():
    # Called before Streamlit reruns and instantiates the keyed sidebar radio.
    st.session_state["active_page"] = "Detection"

if "history_loaded" not in st.session_state:
    st.session_state["history_loaded"] = True
    try:
        st.session_state.history = load_history(HISTORY_PATH)
    except Exception as exc:
        st.session_state.history_load_error = str(exc)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand"><span class="sidebar-brand-icon">🛡️</span><span>Trustline</span></div><div class="sidebar-subtitle">SELLER INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-status">🟢 <b>Interface ready</b><br>AI-assisted consumer awareness<br><span style="color:#9188a5">Research prototype · Evidence-led screening</span></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("##### WORKSPACE")
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "Dashboard"
    page = st.radio("Main menu", ["Dashboard", "Detection", "Analytics", "History", "Model"],
                    key="active_page", label_visibility="collapsed")
    st.divider()
    st.caption("Designed to support informed purchasing decisions.")
    st.caption("Not a verified fraud verdict.")

if st.session_state.history_load_error:
    st.error(
        f"Could not load saved history from {HISTORY_PATH}: "
        f"{st.session_state.history_load_error}. "
        "History for this session starts empty."
    )

# -------------------- DASHBOARD --------------------
if page == "Dashboard":
    st.markdown('<div class="dashboard-page-marker"></div>', unsafe_allow_html=True)
    with st.container(key="dashboard_hero"):
        hero_copy, hero_artwork = st.columns([1.7, 1], gap="large")
        with hero_copy:
            st.markdown('<div class="eyebrow">WELCOME BACK</div><div class="hero-title">Shop smarter.<br>Look beyond the stars.</div>', unsafe_allow_html=True)
            st.markdown('<div class="hero-copy">Compare submitted reviews and seller details; marketplace data is not connected. Use this as a screening aid, not a verdict.</div>', unsafe_allow_html=True)
            st.button("Start Detection  →", type="primary", key="dashboard_start_detection",
                      on_click=go_to_detection)
        with hero_artwork:
            st.image(ROOT / "assets" / "trustline_hero.png", width="stretch")

    records = st.session_state.history
    checks = len(records)
    reviews_total = sum(int(r.get("reviews", 0)) for r in records)
    pairs_total = sum(int(r.get("similar_pairs", 0)) for r in records)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Analyses", checks)
    c2.metric("Reviews", reviews_total)
    c3.metric("Pair matches", pairs_total)
    c4.metric("Model input features", 32)
    st.markdown('<div class="dashboard-section-heading"><span class="section-kicker">YOUR WORKSPACE</span><span class="dashboard-section-title">Detection overview</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.12, .98], gap="large")
    with left:
        with st.container(key="dashboard_recent_panel", border=True):
            st.markdown("#### Recent review checks")
            st.caption("Similar review pairs found in each actual session")
            if records:
                df = pd.DataFrame(records).tail(10).copy()
                df["check"] = [f"Check {i+1}" for i in range(len(df))]
                fig = px.bar(df, x="check", y="similar_pairs", hover_data=["seller", "reviews", "category"],
                             color_discrete_sequence=["#BE5B7B"])
                fig.update_traces(marker_line_width=0, opacity=.9)
                fig.update_yaxes(title="Similar pairs", rangemode="tozero", gridcolor="#efe4e1",
                                 tickfont=dict(color="#77696b"))
                fig.update_xaxes(tickfont=dict(color="#77696b"))
                fig = chart_style(fig, 215)
                fig.update_layout(font=dict(family="DM Sans, sans-serif", color="#54484b", size=12))
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            else:
                st.markdown('<div class="empty-state"><strong>No saved review checks yet</strong>Your recent activity will appear here after you compare reviews from a listing.</div>', unsafe_allow_html=True)
                st.markdown("**Start with a review comparison**")
                st.write("Open Detection, enter a seller name, and paste at least two reviews from the same listing.")
                st.button("Go to Detection", type="primary", key="empty_dashboard_detection",
                          on_click=go_to_detection)
    with right:
        with st.container(key="dashboard_capability_panel", border=True):
            st.markdown("#### What Trustline checks")
            st.caption("Available capabilities in this prototype")
            modules = pd.DataFrame({"Module": ["Review similarity", "Seller information", "Research model"], "Status": [1, 1, 1]})
            fig = px.pie(modules, names="Module", values="Status", hole=.68,
                         color="Module", color_discrete_map={"Review similarity":"#BE5B7B","Seller information":"#DDA17F","Research model":"#82A493"})
            fig.update_traces(textinfo="none", hovertemplate="%{label}<extra></extra>",
                              marker=dict(line=dict(color="#FFFCFB", width=4)))
            fig.add_annotation(text="<b>3</b><br><span style='font-size:10px'>components</span>", showarrow=False,
                               font=dict(size=22, color="#211516"))
            fig = chart_style(fig, 215)
            fig.update_layout(showlegend=True, font=dict(family="DM Sans, sans-serif", color="#54484b", size=11),
                              legend=dict(orientation="h", y=-.08, x=.5, xanchor="center",
                                          font=dict(color="#777078", size=10)),
                              margin=dict(l=10, r=10, t=8, b=28))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.caption("This is a component overview, not a seller-risk distribution.")

# -------------------- DETECTION --------------------
elif page == "Detection":
    page_header("SELLER SCREENING", "Analyse a seller", "Enter the information you have. Trustline will clearly separate observed review patterns from details that have not been verified.")
    form_col, guide_col = st.columns([1.55, 1], gap="large")
    with form_col:
        with st.container(border=True):
            st.markdown("#### 01 · Seller information")
            with st.form("seller_form", clear_on_submit=False):
                seller = st.text_input("Seller name or ID", placeholder="e.g. Example Electronics")
                st.markdown("#### 02 · Product details")
                product_url = st.text_input("Product URL (optional)", placeholder="https://...")
                category = st.selectbox("Product category", ["Electronics", "Fashion", "Beauty", "Home & Kitchen", "Sports", "Other"])
                n1, n2 = st.columns(2)
                with n1:
                    account_age = st.number_input("Account age (days, if known)", min_value=0, value=0, step=1)
                    rating = st.number_input("Average rating (if known)", min_value=0.0, max_value=5.0, value=0.0, step=.1)
                with n2:
                    review_count = st.number_input("Total review count (if known)", min_value=0, value=0, step=1)
                    product_price = st.number_input("Product price (optional)", min_value=0.0, value=0.0, step=1.0)
                st.markdown("#### 03 · Customer reviews")
                reviews_text = st.text_area("Paste one review per line", placeholder="Review 1...\nReview 2...\nReview 3...", height=190)
                submitted = st.form_submit_button("Analyse submitted evidence  →", type="primary", use_container_width=True)
    with guide_col:
        with st.container(border=True):
            st.markdown("#### Before you analyse")
            st.markdown("**What works now**")
            st.write("✓ Similarity comparison between submitted review texts")
            st.write("✓ Evidence summary from the details you enter")
            st.write("✓ Practical consumer precautions")
            st.markdown("**Not connected yet**")
            st.write("○ Live marketplace data")
            st.write("○ Reliable market-price comparison")
            st.write("○ Product-image originality model")
            st.write("○ Calibrated seller-fraud prediction")
            st.divider()
            st.markdown("#### How to get a useful result")
            st.write("Paste several reviews, ideally copied from the same listing. One review per line.")
            st.caption("Review similarity is a screening signal, not proof of fake reviews.")

    if submitted:
        if not seller.strip():
            st.error("Please enter a seller name or ID.")
        else:
            reviews = [line.strip() for line in reviews_text.splitlines() if line.strip()]
            if reviews:
                result = review_summary(reviews)
            else:
                result = {"total_reviews":0, "similar_pair_count":0, "similar_pairs":[],
                          "repeated_text_groups":[], "notice":"No reviews were provided for similarity analysis."}
            result["comparison_count"] = count_review_comparisons(reviews)
            score, confidence, score_reasons = compute_provisional_indicator(result, account_age, rating, review_count, product_price)
            status = status_for_result(result, score, confidence)
            evidence = {
                "Review similarity": f"{result['similar_pair_count']} similar pair(s) among {result['total_reviews']} submitted review(s)." if reviews else "Not assessed — no reviews supplied.",
                "Seller history": f"Account age entered: {account_age} days. This was not independently verified." if account_age else "Not assessed — account age not provided.",
                "Rating and review volume": f"Rating entered: {rating:.1f}/5; review count entered: {review_count}. These values were not independently verified." if rating > 0 or review_count > 0 else "Not assessed — rating and review count not provided.",
                "Pricing": f"Price entered: {product_price:.2f}. No market comparison is connected." if product_price > 0 else "Not assessed — no price supplied.",
                "Product link": product_url.strip() if product_url.strip() else "No product link supplied."
            }
            if result["similar_pair_count"]:
                precautions = [
                    "Inspect the flagged review pairs below in context; similarity warrants a closer look but does not prove fraud."
                ]
            elif result["total_reviews"] < 2:
                precautions = [
                    "Fewer than two reviews were available, so no review-pair comparison could be made."
                ]
            else:
                precautions = [
                    "No submitted review pair crossed the threshold; this does not verify the seller or establish that reviews are genuine."
                ]
            if not account_age or not rating or not review_count:
                precautions.append(
                    "Where possible, verify any missing account-age, rating, or review-volume details directly with the seller or marketplace."
                )
            precautions.extend([
                "Read recent negative reviews and detailed customer experiences.",
                "Verify seller identity and return, refund, and warranty policies where possible.",
                "Compare prices with reputable sellers when reliable comparison information is available.",
                "Use payment methods with buyer protection and avoid off-platform payment requests.",
                "Keep order confirmations, receipts, and tracking information."
            ])
            report = {
                "seller":seller.strip(), "category":category, "evidence":evidence,
                "precautions":precautions,
                "inputs": {
                    "account_age_days":account_age or None,
                    "rating":rating or None,
                    "review_count":review_count or None,
                    "price":product_price or None,
                    "product_url_provided":bool(product_url.strip()),
                },
            }
            history_record = {
                "date":datetime.now().strftime("%Y-%m-%d %H:%M"), "seller":seller.strip(),
                "category":category, "reviews":result["total_reviews"], "similar_pairs":result["similar_pair_count"],
                "status":status, "indicator":score
            }
            try:
                updated_history = append_history(
                    st.session_state.history, history_record, HISTORY_PATH
                )
            except Exception as exc:
                st.error(
                    f"Analysis results could not be saved to {HISTORY_PATH}: {exc}. "
                    "The report was not added to session history."
                )
            else:
                st.session_state.last_review_result = result
                st.session_state.last_report = report
                st.session_state.last_score_details = {
                    "score":score,"confidence":confidence,"reasons":score_reasons,"status":status
                }
                st.session_state.history = updated_history
                st.success("Analysis completed. Review the evidence report below.")

    result = st.session_state.last_review_result
    report = st.session_state.last_report
    score_details = st.session_state.last_score_details
    if result and report and score_details:
        st.write("")
        st.markdown('<div class="section-kicker">ANALYSIS REPORT</div>', unsafe_allow_html=True)
        st.subheader(report["seller"])
        st.caption(f"{report['category']} · Report generated in this session · {result['total_reviews']} review(s) inspected")
        if score_details["confidence"] == "Low":
            st.warning("Insufficient evidence: too little information was provided for a meaningful seller assessment.")
        report_data = build_review_report_data(result)
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Reviews", report_data["review_count"])
        r2.metric("Pairs compared", report_data["possible_pair_count"])
        r3.metric("Pairs flagged", report_data["flagged_pair_count"])
        r4.metric("Duplicate groups", report_data["exact_duplicate_group_count"])
        st.caption(f"Evidence level: {score_details['confidence']} · Similarity threshold: {report_data['threshold']:.0%}")
        st.caption("Important: the 0–100 score is an experimental screening heuristic based only on submitted information. It is not a validated probability of fraud or trustworthiness and is not produced by the research model.")
        score_col, summary_col = st.columns([.85, 1.4], gap="large")
        with score_col:
            with st.container(border=True):
                st.markdown("#### Trust Score")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=score_details["score"],
                    number={"suffix":"/100","font":{"size":50,"color":"#211516"}},
                    gauge={"axis":{"range":[0,100],"tickcolor":"#777078"},
                           "bar":{"color":"#BE5B7B"},
                           "bgcolor":"rgba(0,0,0,0)",
                           "steps":[{"range":[0,40],"color":"#F9E6EA"},{"range":[40,70],"color":"#FBF1E2"},{"range":[70,100],"color":"#E5F2EB"}]}
                ))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(family="DM Sans",color="#211516",size=15),height=310,margin=dict(l=20,r=20,t=25,b=5))
                st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
                st.markdown(f"**{concern_band(score_details['score'])[0]} · provisional heuristic**")
                st.caption("Interactive screening score only. It is not a validated deep-learning prediction or fraud probability.")
        with summary_col:
            with st.container(border=True):
                st.markdown("#### Review pattern summary")
                st.caption(f"Configured text-similarity threshold: {report_data['threshold']:.0%}")
                if report_data["flagged_pair_count"] > 0:
                    st.warning(f"{report_data['flagged_pair_count']} of {report_data['possible_pair_count']} compared pair(s) met the threshold. Similarity warrants inspection but does not prove fraud.")
                elif report_data["possible_pair_count"] > 0:
                    st.success("No submitted review pairs crossed the current similarity threshold.")
                else:
                    st.info("At least two reviews with comparable text are needed to assess review patterns.")
                st.markdown("**Assessment status**")
                st.write(score_details["status"])
                st.markdown("**Data quality**")
                st.write(f"{report_data['review_count']} non-blank review(s) supplied. Seller details are user-entered and not independently verified.")
        band_label, band_color, band_bg = concern_band(score_details["score"])
        possible = report_data["possible_pair_count"]
        share = (report_data["flagged_pair_count"] / possible * 100) if possible else None
        st.markdown(f'<span style="background:{band_bg};color:{band_color};padding:.3rem .9rem;border-radius:999px;font-weight:700">{band_label} (provisional)</span>', unsafe_allow_html=True)
        if share is not None:
            st.caption(f"{share:.0f}% of compared review pairs met the threshold. This is a screening signal, not a fake-review percentage.")
        st.markdown("### Signals and comparisons")
        signal_col, pattern_col = st.columns(2, gap="large")
        unavailable_signals = [
            label for field, label in (
                ("account_age_days", "Account age"),
                ("rating", "Rating"),
                ("review_count", "Review count"),
            )
            if report.get("inputs", {}).get(field) is None
        ]
        unavailable_signals.append("Price comparison")
        contributions = build_indicator_contributions(
            score_details["reasons"], unavailable_signals
        )
        assessed_contributions = [item for item in contributions if item["assessed"]]
        not_assessed_signals = [item["signal"] for item in contributions if not item["assessed"]]
        signal_df = pd.DataFrame(assessed_contributions)
        if not signal_df.empty:
            signal_df["Effect"] = signal_df["points"].apply(
            lambda value: "Raises indicator" if value > 0 else (
                "Lowers indicator" if value < 0 else "No score change"
            )
        )
        with signal_col:
            with st.container(border=True):
                st.markdown("#### Heuristic point contributions")
                if not signal_df.empty:
                    fig = px.bar(
                        signal_df, x="points", y="signal", orientation="h", color="Effect",
                        hover_data={"explanation":True, "points":":.1f"},
                        labels={"points":"Heuristic point adjustment","signal":"Assessed signal"},
                        color_discrete_map={
                            "Raises indicator":"#55A58A",
                            "Lowers indicator":"#BE5B7B",
                            "No score change":"#B7ADB0",
                        },
                    )
                    fig.update_layout(legend=dict(orientation="h", y=-.3))
                    fig.update_xaxes(title="Heuristic points")
                    st.plotly_chart(
                        chart_style(fig, max(250, 90 + 42 * len(signal_df))),
                        width="stretch", config={"displayModeBar":False},
                    )
                else:
                    st.info("No signal contribution was assessed for this submission.")
                if not_assessed_signals:
                    st.markdown("**Not assessed:** " + " · ".join(not_assessed_signals))
                st.caption("Bars show the existing heuristic's point adjustments only; they are separate from raw values entered by the user.")
        with pattern_col:
            with st.container(border=True):
                st.markdown("#### Review-pair pattern")
                if report_data["possible_pair_count"]:
                    pattern_df = pd.DataFrame({
                        "Pair outcome":["Met threshold","Did not meet threshold"],
                        "Comparisons":[
                            report_data["flagged_pair_count"],
                            report_data["non_matching_pair_count"],
                        ],
                    })
                    fig = px.pie(
                        pattern_df, names="Pair outcome", values="Comparisons", hole=.62,
                        color="Pair outcome",
                        color_discrete_map={
                            "Met threshold":"#BE5B7B",
                            "Did not meet threshold":"#F0E3E5",
                        },
                    )
                    fig.update_traces(
                        textinfo="percent",
                        hovertemplate="%{label}: %{value} pair(s)<extra></extra>",
                    )
                    st.plotly_chart(chart_style(fig, 300), width="stretch", config={"displayModeBar":False})
                    st.caption(f"{report_data['flagged_pair_count']} matching and {report_data['non_matching_pair_count']} non-matching comparison(s), from {report_data['review_count']} submitted reviews.")
                else:
                    st.info("Not assessed: no comparable review pairs were available, so no donut is shown.")
        st.markdown("**Not analysed yet (planned):** price comparison · image originality · review-timing bursts · live marketplace data")
        st.markdown("### Review evidence inspector")
        if report_data["flagged_pair_count"]:
            st.caption(f"{report_data['flagged_pair_count']} flagged pair(s) total · showing {len(report_data['visible_pairs'])} at most. Each pair met or exceeded the {report_data['threshold']:.0%} configured similarity threshold.")
            pair_chart_data = pd.DataFrame([
                {"Pair":pair["label"], "Similarity (%)":pair["similarity"] * 100}
                for pair in report_data["visible_pairs"]
            ])
            fig = px.bar(
                pair_chart_data, x="Similarity (%)", y="Pair", orientation="h",
                text="Similarity (%)", labels={"Pair":"Compared reviews"},
                color_discrete_sequence=["#BE5B7B"],
            )
            fig.update_traces(
                texttemplate="%{text:.1f}%", textposition="outside",
                hovertemplate="%{y}: %{x:.1f}% similarity<extra></extra>",
            )
            fig.update_xaxes(range=[0, 105], title="Text similarity (%)")
            st.plotly_chart(chart_style(fig, max(220, 70 + 42 * len(pair_chart_data))),
                            width="stretch", config={"displayModeBar":False})
            if report_data["hidden_pair_count"]:
                st.caption(f"{report_data['hidden_pair_count']} additional flagged pair(s) are not expanded to keep the report readable.")
            for pair in report_data["visible_pairs"]:
                duplicate_label = " · Exact duplicate after normalization" if pair["exact_duplicate"] else ""
                with st.expander(f"{pair['label']} · {pair['similarity']:.1%} similarity{duplicate_label}"):
                    a,b = st.columns(2)
                    with a:
                        st.markdown(f"**Review {pair['review_a_index'] + 1}**")
                        st.write(pair["review_a"])
                    with b:
                        st.markdown(f"**Review {pair['review_b_index'] + 1}**")
                        st.write(pair["review_b"])
                    st.progress(min(1.0,max(0.0,float(pair["similarity"]))))
                    reason = (
                        "These reviews normalize to the same text, so they are an exact-duplicate pair."
                        if pair["exact_duplicate"] else
                        "This pair met the configured text-similarity threshold."
                    )
                    st.caption(f"{reason} Similarity warrants inspection but does not prove fraud or establish reviewer identity.")
        elif report_data["possible_pair_count"] == 0:
            st.info("No review pairs can be shown. Submit at least two reviews with comparable text to enable comparison.")
        else:
            st.info("No submitted review pair met the configured similarity threshold.")
        if result.get("repeated_text_groups"):
            st.markdown("#### Exact-duplicate groups")
            for group in result["repeated_text_groups"]:
                st.write(f"Repeated **{group['count']}** times after normalization: {group['normalized_review']}")
        with st.expander("Seller information and signal provenance"):
            st.caption("The following seller/product details were entered by the user and have not been independently verified.")
            inputs = report.get("inputs", {})
            input_cols = st.columns(3)
            input_cols[0].metric(
                "Account age (days)",
                inputs.get("account_age_days") if inputs.get("account_age_days") is not None else "Not assessed",
            )
            input_cols[1].metric(
                "Rating (out of 5)",
                f"{inputs['rating']:.1f}" if inputs.get("rating") is not None else "Not assessed",
            )
            input_cols[2].metric(
                "Seller review count",
                inputs.get("review_count") if inputs.get("review_count") is not None else "Not assessed",
            )
            price_col, url_col = st.columns(2)
            price_col.metric(
                "Product price",
                f"{inputs['price']:.2f}" if inputs.get("price") is not None else "Not assessed",
            )
            url_col.metric(
                "Product URL",
                "Provided" if inputs.get("product_url_provided") else "Not provided",
            )
            st.markdown("**Availability**")
            st.write(
                "Review similarity is calculated from submitted review text. "
                "Reliable price comparison, live marketplace data, image originality analysis, "
                "and calibrated e-commerce fraud prediction are unavailable."
            )
            for label, detail in report["evidence"].items():
                st.markdown(f"- **{label}:** {detail}")
        st.caption(
            "Review similarity is computed from submitted text. Account age, rating, and review count are user-provided, not independently verified. "
            "Price consistency is not assessed because no reliable comparison source is connected; a supplied product URL is not looked up."
        )
        st.markdown("### Why the indicator changed")
        for kind, explanation, delta in score_details["reasons"]:
            delta_text = f" ({delta:+.1f} points)" if delta else ""
            st.markdown(f"- **{kind}:** {explanation}{delta_text}")
        st.markdown("### Before you buy")
        for tip in report["precautions"]:
            st.markdown(f"- {tip}")
        st.caption("No live marketplace verification, independent price comparison, image analysis, or validated e-commerce fraud prediction is currently connected.")

# -------------------- ANALYTICS --------------------
elif page == "Analytics":
    page_header("PERFORMANCE & ACTIVITY", "Analytics", "Explore actual review-check activity separately from the research model's reported evaluation.")
    records = st.session_state.history
    reviews_total = sum(int(r.get("reviews",0)) for r in records)
    pairs_total = sum(int(r.get("similar_pairs",0)) for r in records)
    checks_with_pairs = sum(int(r.get("similar_pairs",0)) > 0 for r in records)
    a,b,c,d = st.columns(4)
    a.metric("Analyses",len(records))
    b.metric("Reviews",reviews_total)
    c.metric("Pair matches",pairs_total)
    d.metric("Checks matched",checks_with_pairs)
    st.markdown("### Live app activity")
    history_summary = summarize_history(records)
    st.info(
        "Seller-risk categories are unavailable: saved records contain analysis statuses, not validated fraud classes. "
        "Charts below describe recorded activity only."
    )
    if records:
        df = pd.DataFrame(records)
        status_col, category_col = st.columns(2, gap="large")
        with status_col:
            with st.container(border=True):
                st.markdown("#### Saved analysis statuses")
                status_df = pd.DataFrame(
                    [{"Status":status, "Analyses":count}
                     for status, count in history_summary["status_counts"].items()]
                )
                if not status_df.empty:
                    fig = px.bar(
                        status_df, x="Analyses", y="Status", orientation="h",
                        text="Analyses", color_discrete_sequence=["#BE5B7B"],
                        labels={"Analyses":"Saved checks"},
                    )
                    fig.update_layout(showlegend=False, bargap=.35)
                    fig.update_traces(
                        textposition="outside", cliponaxis=False,
                        hovertemplate="%{y}: %{x} saved check(s)<extra></extra>",
                    )
                    fig.update_xaxes(title="Saved checks", rangemode="tozero", dtick=1)
                    st.plotly_chart(
                        chart_style(fig, max(240, 100 + 42 * len(status_df))),
                        width="stretch", config={"displayModeBar":False},
                    )
                else:
                    st.info("No saved status values are available.")
                st.caption("These are workflow statuses from saved checks, not seller-risk or fraud categories.")
        with category_col:
            with st.container(border=True):
                st.markdown("#### Saved checks by product category")
                category_df = pd.DataFrame(
                    [{"Category":category, "Analyses":count}
                     for category, count in history_summary["category_counts"].items()]
                )
                if not category_df.empty:
                    fig = px.bar(
                        category_df, x="Analyses", y="Category", orientation="h",
                        text="Analyses", color_discrete_sequence=["#BE5B7B"],
                        labels={"Analyses":"Saved checks"},
                    )
                    fig.update_traces(
                        textposition="outside", cliponaxis=False,
                        hovertemplate="%{y}: %{x} saved check(s)<extra></extra>",
                    )
                    fig.update_layout(showlegend=False, bargap=.35)
                    fig.update_xaxes(title="Saved checks", rangemode="tozero", dtick=1)
                    st.plotly_chart(
                        chart_style(fig, max(240, 100 + 42 * len(category_df))),
                        width="stretch", config={"displayModeBar":False},
                    )
                else:
                    st.info("No saved category values are available.")
        time_col, pairs_col = st.columns(2, gap="large")
        with time_col:
            with st.container(border=True):
                st.markdown("#### Analysis volume over time")
                daily_df = pd.DataFrame(history_summary["daily_counts"])
                if not daily_df.empty:
                    fig = px.line(
                        daily_df, x="date", y="analyses", markers=True,
                        labels={"date":"Saved date","analyses":"Analysis checks"},
                        color_discrete_sequence=["#BE5B7B"],
                    )
                    fig.update_yaxes(rangemode="tozero", dtick=1)
                    fig.update_xaxes(type="category", tickangle=-15)
                    st.plotly_chart(chart_style(fig, 300), width="stretch", config={"displayModeBar":False})
                    st.caption(f"Based on {history_summary['dated_record_count']} records with usable saved dates.")
                else:
                    st.info("A time trend is unavailable because saved records have no usable dates.")
        with pairs_col:
            with st.container(border=True):
                st.markdown("#### Similar pairs per saved check")
                if {"seller", "similar_pairs"}.issubset(df.columns):
                    pair_df = df[["seller", "similar_pairs"]].copy()
                    pair_df["similar_pairs"] = pd.to_numeric(
                        pair_df["similar_pairs"], errors="coerce"
                    ).fillna(0)
                    pair_df["Check"] = [
                        f"{index + 1}. {str(seller)[:16]}"
                        for index, seller in enumerate(pair_df["seller"])
                    ]
                    if pair_df["similar_pairs"].gt(0).any():
                        fig = px.bar(
                            pair_df, x="Check", y="similar_pairs",
                            color_discrete_sequence=["#BE5B7B"],
                            labels={"similar_pairs":"Pairs meeting threshold"},
                        )
                        fig.update_traces(marker_line_width=0)
                        fig.update_yaxes(
                            title="Pairs meeting threshold", rangemode="tozero", dtick=1
                        )
                        fig.update_xaxes(type="category", tickangle=-15, title="Saved check")
                        st.plotly_chart(
                            chart_style(fig, 300), width="stretch",
                            config={"displayModeBar":False},
                        )
                    else:
                        st.info(
                            "No similar review pairs were detected in the saved checks. "
                            "The chart will appear when a check has one or more matching pairs."
                        )
                else:
                    st.info("Saved records do not contain the fields needed for this chart.")
        with st.container(border=True):
            st.markdown("#### Recent activity records")
            display_columns = [
                column for column in
                ["date", "seller", "category", "reviews", "similar_pairs", "status"]
                if column in df.columns
            ]
            st.dataframe(df[display_columns].tail(10), width="stretch", hide_index=True)
    else:
        with st.container(border=True):
            st.info("No live activity yet. Run a check on the Detection page and this section will populate with real session data.")
            st.write("This area intentionally avoids demo numbers so users can tell when no analyses have been run.")
    st.divider()
    st.markdown("### Research model evaluation")
    M = load_metrics()
    if not M:
        st.info("models/model_metrics.json not found. Copy it from the Kaggle export.")
    else:
        st.caption(f"{M['model']} · {M['n_test']:,} held-out YelpChi test samples · dataset-level metrics, not live seller-risk estimates")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Accuracy", f"{M['accuracy']:.2%}")
        m2.metric("Precision", f"{M['precision']:.2%}")
        m3.metric("Recall", f"{M['recall']:.2%}")
        m4.metric("F1-score", f"{M['f1']:.2%}")
        if M.get("roc_auc") is not None:
            n1, n2, _, _ = st.columns(4)
            n1.metric("ROC-AUC", f"{M['roc_auc']:.3f}")
            n2.metric("PR-AUC", f"{M['pr_auc']:.3f}")
        cm_col, chart_col = st.columns([1, 1.2], gap="large")
        with cm_col:
            with st.container(border=True):
                st.markdown("#### Confusion matrix")
                cm = M["confusion_matrix"]
                fig = go.Figure(go.Heatmap(z=cm, x=["Predicted class 0", "Predicted class 1"],
                                           y=["Actual class 0", "Actual class 1"], text=cm,
                                           texttemplate="%{text}", showscale=False,
                                           colorscale=[[0, "#f4f0fb"], [1, "#8068cb"]]))
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(chart_style(fig, 300), use_container_width=True, config={"displayModeBar": False})
                st.caption("Confirm class-label meanings against the original dataset before presenting them as fraud/non-fraud.")
        with chart_col:
            with st.container(border=True):
                st.markdown("#### Evaluation metrics")
                metrics = pd.DataFrame({"Metric": ["Accuracy", "Precision", "Recall", "F1-score"],
                                        "Score (%)": [round(M[k] * 100, 2) for k in ("accuracy", "precision", "recall", "f1")]})
                fig = px.bar(metrics, x="Metric", y="Score (%)", range_y=[0, 100], text="Score (%)",
                             color_discrete_sequence=["#8974d4"])
                fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside", cliponaxis=False, marker_line_width=0)
                st.plotly_chart(chart_style(fig, 300), use_container_width=True, config={"displayModeBar": False})
        with st.container(border=True):
            st.markdown("#### YelpChi class distribution")
            fig = px.pie(names=["Class 0", "Class 1"], values=[39277, 6677], hole=.62,
                         color_discrete_sequence=["#8974d4", "#e99ab5"])
            st.plotly_chart(chart_style(fig), use_container_width=True, config={"displayModeBar": False})
            st.caption("The dataset is imbalanced, which is why accuracy alone can mislead.")
    if EXPERIMENTS_PATH.exists():
        exp = pd.DataFrame(json.loads(EXPERIMENTS_PATH.read_text(encoding="utf-8")))
        with st.container(border=True):
            st.markdown("#### Experiment comparison (validation F1-score)")
            fig = px.bar(exp, x="Approach", y="F1-score (%)", text="F1-score (%)",
                         color_discrete_sequence=["#8974d4"])
            fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_yaxes(range=[0, 70])
            fig.update_xaxes(tickangle=-25)
            st.plotly_chart(chart_style(fig, 380), use_container_width=True, config={"displayModeBar": False})
            st.caption("Compared on the common validation set (5,515 samples), not the test set. The final test result above is for the selected configuration only.")
    st.warning("Metrics are computed from the exported model on the held-out test split. YelpChi is not a verified e-commerce seller-fraud dataset.")

# -------------------- HISTORY --------------------
elif page == "History":
    page_header("YOUR WORKSPACE", "Analysis history", "Search, filter and export records created during this active session.")
    records = st.session_state.history
    a,b,c = st.columns(3)
    a.metric("Checks",len(records))
    b.metric("Matched",sum(int(r.get("similar_pairs",0))>0 for r in records))
    c.metric("Reviews",sum(int(r.get("reviews",0)) for r in records))
    if records:
        df = pd.DataFrame(records)
        with st.container(border=True):
            st.markdown("#### Find an analysis")
            with st.container(key="history-filters"):
                f1,f2,f3 = st.columns([1.5,1,1])
                with f1:
                    search = st.text_input("Search seller",placeholder="Type a seller name...")
                with f2:
                    status_options = ["All"] + sorted(df["status"].dropna().unique().tolist())
                    status_filter = st.selectbox(
                        "Status", status_options, key="history-status-filter"
                    )
                with f3:
                    category_options = ["All"] + sorted(df["category"].dropna().unique().tolist())
                    category_filter = st.selectbox(
                        "Category", category_options, key="history-category-filter"
                    )
            filtered = df.copy()
            if search:
                filtered = filtered[filtered["seller"].str.contains(search,case=False,na=False)]
            if status_filter != "All":
                filtered = filtered[filtered["status"] == status_filter]
            if category_filter != "All":
                filtered = filtered[filtered["category"] == category_filter]
            st.caption(f"{len(filtered)} matching record(s)")
            if not filtered.empty:
                status_chart_col, category_chart_col = st.columns(2, gap="large")
                if "status" in filtered.columns:
                    with status_chart_col:
                        st.markdown("**Statuses in filtered history**")
                        status_counts = (
                            filtered["status"].dropna().value_counts()
                            .rename_axis("Status").reset_index(name="Analyses")
                        )
                        if not status_counts.empty:
                            fig = px.bar(
                                status_counts, x="Analyses", y="Status", orientation="h",
                                text="Analyses", color_discrete_sequence=["#BE5B7B"],
                            )
                            fig.update_layout(showlegend=False)
                            st.plotly_chart(
                                chart_style(fig, max(220, 90 + 40 * len(status_counts))),
                                width="stretch", config={"displayModeBar":False},
                            )
                if "category" in filtered.columns:
                    with category_chart_col:
                        st.markdown("**Categories in filtered history**")
                        category_counts = (
                            filtered["category"].dropna().value_counts()
                            .rename_axis("Category").reset_index(name="Analyses")
                        )
                        if not category_counts.empty:
                            fig = px.bar(
                                category_counts, x="Analyses", y="Category",
                                orientation="h", text="Analyses",
                                color_discrete_sequence=["#BE5B7B"],
                                labels={"Analyses":"Saved checks"},
                            )
                            fig.update_traces(
                                textposition="outside", cliponaxis=False,
                                hovertemplate="%{y}: %{x} saved check(s)<extra></extra>",
                            )
                            fig.update_layout(showlegend=False, bargap=.35)
                            fig.update_xaxes(
                                title="Saved checks", rangemode="tozero", dtick=1
                            )
                            st.plotly_chart(
                                chart_style(
                                    fig, max(220, 90 + 40 * len(category_counts))
                                ),
                                width="stretch",
                                config={"displayModeBar":False},
                            )
            display_cols = ["date","seller","category","reviews","similar_pairs","status","indicator"]
            display_history = filtered[display_cols].rename(
                columns={"indicator": "Provisional indicator"}
            )
            history_table = (
                display_history
                .style
                .format(
                    {"Provisional indicator": "{:.0f}/100"},
                    escape="html",
                    na_rep="",
                )
                .set_properties(
                    **{
                        "background-color": "#FFFCFB",
                        "color": "#211516",
                        "border-color": "#F0E3E5",
                    }
                )
                .set_table_styles(
                    [
                        {
                            "selector": "table",
                            "props": [
                                ("background-color", "#FFFCFB"),
                                ("color", "#211516"),
                                ("border", "1px solid #F0E3E5"),
                                ("border-collapse", "collapse"),
                                ("width", "100%"),
                                ("min-width", "820px"),
                            ],
                        },
                        {
                            "selector": "th.col_heading",
                            "props": [
                                ("background-color", "#F8F3F2"),
                                ("color", "#211516"),
                                ("border-color", "#F0E3E5"),
                                ("font-weight", "700"),
                                ("white-space", "nowrap"),
                            ],
                        },
                        {
                            "selector": "td",
                            "props": [
                                ("background-color", "#FFFCFB"),
                                ("color", "#211516"),
                                ("border-color", "#F0E3E5"),
                                ("white-space", "nowrap"),
                            ],
                        },
                    ]
                )
                .hide(axis="index")
            )
            with st.container(key="history-html-table"):
                st.markdown(history_table.to_html(), unsafe_allow_html=True)
            st.download_button("Export filtered history to CSV",data=filtered.to_csv(index=False).encode("utf-8"),
                               file_name="trustline_history.csv",mime="text/csv")
        with st.expander("What does this history contain?"):
            st.write("Records store the details entered, number of submitted reviews, text-similarity findings and the experimental indicator for each check. Records are saved to data/history.csv on this computer, so they survive a page refresh.")
    else:
        with st.container(border=True):
            st.info("No checks yet. Go to Detection and analyse some review text to create your first record.")
            st.markdown("**Once you run an analysis, this page will provide:**")
            st.write("• Search by seller name")
            st.write("• Filter by status and category")
            st.write("• Review findings and export matching records")

# -------------------- MODEL --------------------
elif page == "Model":
    page_header("MODEL TRANSPARENCY", "How Trustline works", "A clear view of the current research model, the live review-text tool and what remains to be integrated.")
    pipeline = st.columns(4)
    steps = [
        ("01","Input data","Seller details and pasted review text"),
        ("02","Text comparison","Normalise text and compare review pairs"),
        ("03","Research MLP","Separate model trained on 32 YelpChi features"),
        ("04","Evidence report","Show findings, caveats and precautions"),
    ]
    for col,(num,title,desc) in zip(pipeline,steps):
        with col:
            st.markdown(f'<div class="pipeline-step"><div class="pipeline-number">{num}</div><div class="pipeline-title">{title}</div><div class="pipeline-copy">{desc}</div></div>',unsafe_allow_html=True)
    st.write("")
    left,right = st.columns([1.1,1],gap="large")
    with left:
        with st.container(border=True):
            st.markdown("#### Trained research model")
            st.write("YelpChi-based multilayer perceptron (MLP)")
            st.code("Input: 32 numerical features\nLinear(32, 128) → ReLU → Dropout(0.1)\nLinear(128, 64) → ReLU → Dropout(0.1)\nLinear(64, 32) → ReLU → Dropout(0.1)\nLinear(32, 2)",language="text")
            if st.button("Load trained model and scaler",type="primary",use_container_width=True):
                try:
                    model,scaler = load_model_and_scaler()
                    st.session_state.model_load_status = {"ok":True,"features":int(scaler.n_features_in_),"classes":int(model[-1].out_features)}
                except Exception as exc:
                    st.session_state.model_load_status = {"ok":False,"error":str(exc)}
            if st.session_state.model_load_status:
                status = st.session_state.model_load_status
                if status["ok"]:
                    st.success("Model and scaler loaded successfully.")
                    st.write(f"Input features: {status['features']} · Output classes: {status['classes']}")
                else:
                    st.error(f"Could not load model: {status['error']}")
    with right:
        with st.container(border=True):
            st.markdown("#### Evaluation of the exported model")
            M = load_metrics()
            if M:
                m1, m2 = st.columns(2)
                m1.metric("Accuracy", f"{M['accuracy']:.2%}")
                m2.metric("F1-score", f"{M['f1']:.2%}")
                m3, m4 = st.columns(2)
                m3.metric("Precision", f"{M['precision']:.2%}")
                m4.metric("Recall", f"{M['recall']:.2%}")
                st.caption("Computed on the held-out YelpChi test split using the exported model files.")
            else:
                st.info("models/model_metrics.json not found. Copy it from the Kaggle export.")
    st.write("")
    render_model_demo()
    st.markdown("### Live features vs. research-only components")
    st.caption("The live review-text comparison and the separate YelpChi research model are shown separately so the interface does not imply that the trained MLP currently scores submitted sellers.")
    st.markdown("### What is active today?")
    c1,c2 = st.columns(2,gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("#### Review similarity")
            st.success("Connected to the Detection form")
            st.write("Compares submitted review text and displays similar pairs and repeated text groups.")
    with c2:
        with st.container(border=True):
            st.markdown("#### MLP seller assessment")
            st.warning("Not connected to seller form")
            st.write("The MLP expects 32 dataset-specific numerical features. The current form does not produce those features, so its output is not used as a seller verdict.")
    st.markdown("### Known limitations")
    limitations = [
        "The provisional 0–100 indicator is an experimental heuristic, not a trained or calibrated fraud probability.",
        "Seller name, rating, account age, review count and price are user-entered and not independently verified.",
        "YelpChi is not a verified e-commerce seller-fraud dataset.",
        "No live marketplace lookup, price comparison, image originality model or review-timestamp burst detector is connected.",
        "No similarity matches does not prove reviews are genuine or a seller is safe.",
    ]
    for item in limitations:
        st.markdown(f"- {item}")