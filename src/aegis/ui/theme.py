"""Local dashboard styling. No remote fonts, stylesheets or image assets."""
import streamlit as st


def apply_theme():
    st.markdown('''<style>
    .stApp { background: #f5f7fa; color: #172b40; }
    [data-testid="stHeader"] { background: rgba(245,247,250,.94); }
    .block-container { max-width: 1440px; padding: 2.1rem 2.7rem 3rem; }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e3e9ef; }
    [data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }
    h1,h2,h3 { color: #142d43; letter-spacing: -.035em; }
    h1 { font-size: 2.1rem !important; font-weight: 700 !important; padding-bottom: .25rem !important; }
    h2 { font-size: 1.28rem !important; }
    h3 { font-size: 1.05rem !important; letter-spacing: -.015em; }
    [data-testid="stCaptionContainer"] { color: #61758a; }
    [data-testid="stMetric"] { background: white; border: 1px solid #e1e8ef; border-radius: 12px;
      padding: 1.1rem 1.25rem; border-top: 3px solid #159b87; min-height: 112px; }
    [data-testid="stMetricLabel"] { color: #61758a; font-size: .85rem; }
    [data-testid="stMetricValue"] { color: #142d43; font-weight: 650; font-size: 1.9rem; }
    [class*="st-key-panel_"] { background: #ffffff; border-radius: 12px; }
    [data-testid="stExpander"] { background: white; border-radius: 10px; }
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    .stButton > button, .stDownloadButton > button { border-radius: 8px; font-weight: 600; min-height: 2.6rem; }
    [data-testid="stFileUploader"] { background: #fff; border-radius: 12px; }
    .aegis-brand { display:flex; gap:12px; align-items:center; margin-bottom: 8px; }
    .aegis-mark { background:#142d43; color:#62d6bb; width:43px; height:43px; border-radius:12px;
      display:grid; place-items:center; font-size:25px; font-weight:800; }
    .aegis-wordmark { font-size:25px; font-weight:800; letter-spacing:.13em; color:#142d43; line-height:1.15; }
    .aegis-submark { font-size:10px; letter-spacing:.12em; color:#7890a4; margin-top:5px; text-transform:uppercase; }
    .aegis-eyebrow { color:#61758a; font-size:11px; font-weight:700; letter-spacing:.15em; text-transform:uppercase; margin:8px 0; }
    .aegis-status { display:inline-block; padding:5px 10px; border-radius:30px; background:#e4f5f0;
      color:#147764; font-size:11px; font-weight:700; letter-spacing:.05em; }
    @media(max-width: 760px) { .block-container { padding: 1.3rem 1rem 2rem; } h1 { font-size:1.7rem !important; }
      [data-testid="stMetric"] { padding:.8rem; min-height:96px; } }
    </style>''', unsafe_allow_html=True)


def brand():
    st.markdown('''<div class="aegis-brand"><div class="aegis-mark">A</div><div>
    <div class="aegis-wordmark">AEGIS</div><div class="aegis-submark">Evidence & investigation</div>
    </div></div>''', unsafe_allow_html=True)
