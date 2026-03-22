"""
Shared CSS — shadcn/ui dark + Tailwind green palette.

Palette reference (Tailwind):
  green-400  #4ade80   ← primary accent (contrast 8.2:1 on bg)
  green-500  #22c55e
  green-600  #16a34a
  green-700  #15803d
  green-800  #166534
  green-900  #14532d
  green-950  #052e16

  Base bg      #0d1b12   (page)
  Surface      #142019   (cards / sidebar)
  Surface+     #1c2d20   (hover / raised)
  Border       #264d30
  Border-light #1a3322
"""
import streamlit as st

_CSS = """
<style>
/* ── Reset / base ────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: #0d1b12; }
[data-testid="stHeader"]           { background: transparent !important; }
[data-testid="stDecoration"]       { display: none !important; }
.block-container                   { padding-top: 2rem; max-width: 1080px; }

/* ── Sidebar shell ───────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0a150e !important;
    border-right: 1px solid #1a3322 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.75rem;
}

/* ── Hide Streamlit's auto-generated page nav (shows raw filenames) ──── */
/* We use our own render_nav() instead                                    */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] {
    display: none !important;
}

/* ── Custom nav: st.page_link inside sidebar ─────────────────────────── */
/* Nuclear-broad selector — catches whatever Streamlit renders            */
[data-testid="stSidebar"] a {
    color: #d1fae5 !important;
    text-decoration: none !important;
}
[data-testid="stSidebar"] a:hover {
    color: #4ade80 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] .stPageLink a {
    color: #d1fae5 !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.75rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    transition: background 0.15s, color 0.15s !important;
    width: 100% !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] .stPageLink a:hover {
    background: #1c2d20 !important;
    color: #4ade80 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
    background: #1c2d20 !important;
    color: #4ade80 !important;
    font-weight: 700 !important;
}

/* ── Typography ──────────────────────────────────────────────────────── */
h1 { color: #4ade80 !important; font-size: 1.85rem !important; letter-spacing: -0.5px; }
h2 { color: #86efac !important; }
h3 {
    color: #86efac !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 700;
}
p, li { color: #d1fae5; }
label {
    color: #bbf7d0 !important;    /* green-200 — clearly readable */
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}
small, .caption, [data-testid="stCaptionContainer"] {
    color: #6ee7b7 !important;    /* green-300 */
}

/* ── Inputs ──────────────────────────────────────────────────────────── */
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
[data-baseweb="select"] > div:first-child {
    background: #0d1b12 !important;
    border: 1px solid #264d30 !important;
    border-radius: 8px !important;
    color: #f0f9f1 !important;
}
[data-baseweb="input"] > div:focus-within,
[data-baseweb="textarea"] > div:focus-within,
[data-baseweb="select"] > div:first-child:focus-within {
    border-color: #4ade80 !important;
    box-shadow: 0 0 0 2px rgba(74,222,128,0.18) !important;
}
input, textarea { color: #f0f9f1 !important; }
[data-baseweb="select"] span,
[data-baseweb="select"] div,
[data-baseweb="select"] [role="option"] { color: #f0f9f1 !important; }

/* Dropdown panel */
[data-baseweb="popover"] [data-baseweb="menu"],
[role="listbox"] {
    background: #142019 !important;
    border: 1px solid #264d30 !important;
    border-radius: 8px !important;
}
[role="option"]:hover { background: #1c2d20 !important; }
[role="option"][aria-selected="true"] {
    background: #166534 !important;
    color: #4ade80 !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: #16a34a !important;    /* green-600 */
    color: #f0f9f1 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.2rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
    width: 100%;
}
.stButton > button:hover {
    background: #15803d !important;    /* green-700 */
    box-shadow: 0 4px 14px rgba(22,163,74,0.38) !important;
    transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }
.stButton > button:disabled { opacity: 0.35 !important; transform: none !important; }

/* Primary (type="primary") */
button[kind="primaryFormSubmit"],
button[data-testid="stBaseButton-primary"] {
    background: #16a34a !important;
}
button[kind="primaryFormSubmit"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background: #15803d !important;
}

/* Secondary */
button[data-testid="stBaseButton-secondary"] {
    background: transparent !important;
    border: 1px solid #264d30 !important;
    color: #86efac !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    background: #1c2d20 !important;
    border-color: #4ade80 !important;
    color: #4ade80 !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #1a3322 !important;
    gap: 0.25rem;
}
[data-testid="stTabs"] button[role="tab"] {
    color: #6ee7b7 !important;
    font-weight: 500;
    font-size: 0.875rem;
    padding: 0.5rem 1rem;
    border-radius: 6px 6px 0 0;
    border: none !important;
    background: transparent !important;
}
[data-testid="stTabs"] button[role="tab"]:hover { color: #4ade80 !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #4ade80 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #4ade80 !important;
}

/* ── Progress bar ────────────────────────────────────────────────────── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #16a34a, #4ade80) !important;
    border-radius: 4px;
}

/* ── Data editor / table ─────────────────────────────────────────────── */
[data-testid="stDataFrame"],
[data-testid="data-grid-canvas"] {
    border: 1px solid #1a3322 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Metrics ─────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #142019;
    border: 1px solid #1a3322;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}
[data-testid="stMetricLabel"] { color: #6ee7b7 !important; font-size: 0.78rem !important; }
[data-testid="stMetricValue"] { color: #f0f9f1 !important; font-size: 1.6rem !important; }
[data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }

/* ── Alerts ──────────────────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── Expander ────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #1a3322 !important;
    border-radius: 10px !important;
    background: #142019 !important;
}
[data-testid="stExpanderToggleIcon"] { color: #4ade80 !important; }

/* ── Divider ─────────────────────────────────────────────────────────── */
hr { border-color: #1a3322 !important; margin: 0.75rem 0 !important; }

/* ── File uploader ───────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed #264d30 !important;
    border-radius: 10px !important;
    background: #0d1b12 !important;
    padding: 1rem !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #4ade80 !important; }

/* ── Camera input ────────────────────────────────────────────────────── */
[data-testid="stCameraInput"] {
    border: 2px dashed #264d30 !important;
    border-radius: 10px !important;
    overflow: hidden;
}

/* ── Log panel ───────────────────────────────────────────────────────── */
.log-panel {
    background: #060e08;
    border: 1px solid #1a3322;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.78rem;
    line-height: 1.65;
    height: 430px;
    overflow-y: auto;
    color: #6ee7b7;
    white-space: pre-wrap;
}
.log-panel .dim  { color: #264d30; }
.log-panel .ok   { color: #4ade80; }
.log-panel .warn { color: #fbbf24; }
.log-panel .err  { color: #f87171; }

/* ── Status dots ─────────────────────────────────────────────────────── */
.status-bar { display:flex; align-items:center; gap:0.5rem; margin-bottom:0.6rem; }
.dot        { width:8px; height:8px; border-radius:50%; display:inline-block; }
.dot-idle    { background:#264d30; }
.dot-running { background:#4ade80; box-shadow:0 0 6px #4ade80; animation:pulse 1s infinite; }
.dot-done    { background:#22c55e; }
.dot-error   { background:#f87171; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.35} }
.status-label  { font-size:0.8rem; font-weight:600; }
.idle-label    { color:#264d30; }
.running-label { color:#4ade80; }
.done-label    { color:#22c55e; }
.error-label   { color:#f87171; }

/* ── Field errors ────────────────────────────────────────────────────── */
.field-error {
    display:flex; align-items:flex-start; gap:0.45rem;
    margin:0.15rem 0 0.4rem; padding:0.35rem 0.75rem;
    background:rgba(248,113,113,0.10);
    border:1px solid rgba(248,113,113,0.3);
    border-radius:7px;
    color:#fca5a5; font-size:0.77rem; font-weight:500;
}
.field-error-icon { font-size:0.85rem; flex-shrink:0; }
.validation-banner {
    display:flex; align-items:center; gap:0.6rem;
    margin-bottom:1rem; padding:0.65rem 1rem;
    background:rgba(248,113,113,0.10);
    border:1px solid rgba(248,113,113,0.35);
    border-radius:10px;
    color:#fca5a5; font-size:0.85rem; font-weight:600;
}

/* ── Info pill ───────────────────────────────────────────────────────── */
.info-pill {
    display:inline-block; padding:0.25rem 0.75rem;
    background:#052e16; border:1px solid #166534;
    border-radius:20px; font-size:0.78rem; color:#86efac;
}

/* ── Slider ──────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"] {
    background: #4ade80 !important;
    border-color: #4ade80 !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] > div {
    background: #16a34a !important;
}
</style>
"""


def inject_global_css():
    st.markdown(_CSS, unsafe_allow_html=True)
