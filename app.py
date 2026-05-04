import streamlit as st
import requests
import openpyxl
import re
import io
import gspread
import pandas as pd
import altair as alt
import concurrent.futures
from datetime import datetime, date, timedelta
from email.utils import parsedate
from google.oauth2.service_account import Credentials
from transformers import pipeline
from collections import Counter

# ============================
# 페이지 설정
# ============================
st.set_page_config(
    page_title="DAISO SNS ISSUE FINDER",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# CSS
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --primary:    #0066CC;
    --primary-lt: #E8F1FB;
    --primary-md: #CCE0F5;
    --bg:         #F8F9FB;
    --bg-white:   #FFFFFF;
    --border:     #E2E8F0;
    --border2:    #CBD5E1;
    --text:       #1A202C;
    --text2:      #4A5568;
    --text3:      #718096;
    --pos:        #16A34A;
    --pos-bg:     #F0FDF4;
    --neg:        #DC2626;
    --neg-bg:     #FEF2F2;
    --neu:        #CA8A04;
    --neu-bg:     #FEFCE8;
    --shadow:     0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md:  0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.04);
    --admin:      #7C3AED;
    --admin-lt:   #F5F3FF;
    --admin-md:   #DDD6FE;
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: var(--bg-white) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stNumberInput input {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important;
}
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] .stTextArea textarea:focus,
[data-testid="stSidebar"] .stNumberInput input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.12) !important;
    outline: none !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 0.875rem !important;
    padding: 0.3rem 0.5rem !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] {
    margin-top: 0 !important; margin-bottom: 0 !important;
    padding-top: 0 !important; padding-bottom: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] > label { display: none !important; }
.date-label { font-size: 0.7rem; color: #718096; margin-bottom: 1px; margin-top: 0; display: block; line-height: 1.1; }
[data-testid="stSidebar"] [data-testid="column"] { gap: 0 !important; padding-top: 0 !important; padding-bottom: 0 !important; min-width: 0 !important; }
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }

.app-header {
    background: var(--bg-white); border-bottom: 1px solid var(--border);
    padding: 1.25rem 2rem; display: flex; align-items: center; gap: 0.75rem;
    margin-bottom: 1.5rem; border-radius: 12px; box-shadow: var(--shadow);
    position: relative;
}
.header-title { font-size: 1.25rem; font-weight: 700; color: var(--text); letter-spacing: -0.01em; }
.header-sub { font-size: 0.78rem; color: var(--text3); margin-top: 0.1rem; }

.card { background: var(--bg-white); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.5rem; box-shadow: var(--shadow); margin-bottom: 1rem; }

.metric-card { flex: 1; background: var(--bg-white); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.5rem; box-shadow: var(--shadow); border-top: 3px solid transparent; }
.metric-card.total { border-top-color: var(--primary); }
.metric-card.pos   { border-top-color: var(--pos); }
.metric-card.neg   { border-top-color: var(--neg); }
.metric-card.neu   { border-top-color: var(--neu); }

.metric-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text3); margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
.metric-icon { width: 22px; height: 22px; background: var(--primary); border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; color: #FFFFFF !important; font-size: 0.68rem; font-weight: 700; flex-shrink: 0; line-height: 1; }
.metric-icon.pos { background: var(--pos); }
.metric-icon.neg { background: var(--neg); }
.metric-icon.neu { background: var(--neu); }
.metric-value { font-family: 'Inter', sans-serif; font-size: 2.2rem; font-weight: 600; color: var(--text); line-height: 1; }
.metric-pct { font-size: 0.78rem; color: var(--text3); margin-top: 0.3rem; }

.section-title-icon { width: 24px; height: 24px; background: var(--primary); border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; color: #FFFFFF !important; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; vertical-align: middle; }

.badge-pos { background: var(--pos-bg); color: var(--pos); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neg { background: var(--neg-bg); color: var(--neg); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neu { background: var(--neu-bg); color: var(--neu); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }

.top-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border); }
.top-item:last-child { border-bottom: none; }
.top-rank { width: 26px; height: 26px; background: var(--primary-lt); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; color: var(--primary); flex-shrink: 0; }
.top-rank.r1 { background: var(--primary); color: #FFFFFF !important; }
.top-name { flex: 1; font-size: 0.85rem; color: var(--text); }
.top-count { font-size: 0.78rem; font-weight: 600; color: var(--primary); background: var(--primary-lt); padding: 2px 8px; border-radius: 20px; }

.result-card { background: var(--bg-white); border: 1px solid var(--border); border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.5rem; box-shadow: var(--shadow); transition: box-shadow 0.2s; }
.result-card:hover { box-shadow: var(--shadow-md); }
.result-title { font-size: 0.9rem; font-weight: 500; color: var(--text); margin-bottom: 0.4rem; }
.result-meta { font-size: 0.75rem; color: var(--text3); display: flex; gap: 0.75rem; flex-wrap: wrap; }
.result-meta span { display: flex; align-items: center; gap: 0.2rem; }
.result-reason { font-size: 0.78rem; color: var(--neg); background: var(--neg-bg); border-left: 3px solid var(--neg); border-radius: 0 6px 6px 0; padding: 0.3rem 0.65rem; margin-top: 0.45rem; line-height: 1.5; }
.result-reason.pos { color: var(--pos); background: var(--pos-bg); border-left-color: var(--pos); }
.result-reason.neu { color: var(--neu); background: var(--neu-bg); border-left-color: var(--neu); }
.prod-tag { display: inline-flex; align-items: center; gap: 0.25rem; background: var(--primary-lt); color: var(--primary); border: 1px solid var(--primary-md); border-radius: 6px; padding: 2px 7px; font-size: 0.72rem; font-weight: 600; margin-right: 0.3rem; }

.login-wrap { max-width: 380px; margin: 5rem auto; background: var(--bg-white); border: 1px solid var(--border); border-radius: 16px; padding: 2.5rem 2rem; text-align: center; box-shadow: var(--shadow-md); }
.login-icon { width: 52px; height: 52px; background: var(--primary); border-radius: 14px; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; color: #FFFFFF !important; }
.login-title { font-size: 1.3rem; font-weight: 700; color: var(--text); margin-bottom: 0.25rem; }
.login-sub { font-size: 0.82rem; color: var(--text3); margin-bottom: 1.5rem; }

.sb-section { display: flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.7rem; background: var(--primary-lt); border-left: 3px solid var(--primary); border-radius: 0 6px 6px 0; margin: 1rem 0 0.5rem; }
.sb-section-icon { width: 20px; height: 20px; background: var(--primary); border-radius: 5px; display: inline-flex; align-items: center; justify-content: center; color: #FFFFFF !important; font-size: 0.62rem; font-weight: 700; flex-shrink: 0; }
.sb-section-text { font-size: 0.72rem; font-weight: 700; color: var(--primary) !important; text-transform: uppercase; letter-spacing: 0.07em; }
.sb-hint { font-size: 0.68rem; color: var(--text3); margin-top: 0.15rem; display: block; line-height: 1.5; }

.ch-row { display: flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0; min-height: 32px; }
.ch-icon { width: 20px; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 0.55rem; color: #FFFFFF !important; font-weight: 900; flex-shrink: 0; }
.ch-naver   { background: #03C75A; }
.ch-youtube { background: #FF0000; }
.ch-label   { font-size: 0.82rem; font-weight: 500; color: var(--text) !important; line-height: 1; }

[data-testid="stNumberInput"] > div { border-radius: 8px !important; }
[data-testid="stNumberInput"] button { color: var(--primary) !important; }

/* 기본 버튼 */
.stButton > button { background: var(--primary) !important; color: #FFFFFF !important; border: none !important; border-radius: 8px !important; font-family: 'Noto Sans KR', sans-serif !important; font-size: 0.875rem !important; font-weight: 600 !important; padding: 0.6rem 1.25rem !important; transition: all 0.2s !important; letter-spacing: 0.01em !important; }
.stButton > button:hover { background: #0052A3 !important; box-shadow: 0 4px 12px rgba(0,102,204,0.3) !important; }

/* 사이드바 버튼: 노란색 */
[data-testid="stSidebar"] .stButton > button { background: #FFD600 !important; color: #1A202C !important; font-size: 1rem !important; font-weight: 800 !important; border: none !important; box-shadow: 0 2px 8px rgba(255,214,0,0.35) !important; }
[data-testid="stSidebar"] .stButton > button:hover { background: #F5C800 !important; box-shadow: 0 4px 14px rgba(255,214,0,0.5) !important; color: #1A202C !important; }

.stDownloadButton > button { background: var(--bg-white) !important; color: var(--primary) !important; border: 1.5px solid var(--primary) !important; border-radius: 8px !important; font-family: 'Noto Sans KR', sans-serif !important; font-size: 0.875rem !important; font-weight: 500 !important; width: 100% !important; }
.stDownloadButton > button:hover { background: var(--primary-lt) !important; }

.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 2px solid var(--border) !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] { font-family: 'Noto Sans KR', sans-serif !important; font-size: 0.85rem !important; font-weight: 500 !important; color: var(--text3) !important; background: transparent !important; border: none !important; border-bottom: 2px solid transparent !important; padding: 0.6rem 1.2rem !important; border-radius: 0 !important; margin-bottom: -2px !important; }
.stTabs [aria-selected="true"] { color: var(--primary) !important; border-bottom-color: var(--primary) !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem !important; }

.stProgress > div > div > div > div { background: var(--primary) !important; border-radius: 4px !important; }
.stProgress > div > div > div { background: var(--border) !important; border-radius: 4px !important; height: 6px !important; }
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; }
.stAlert { border-radius: 8px !important; }
hr { border: none; border-top: 1px solid var(--border) !important; margin: 1rem 0 !important; }
#MainMenu, footer {
    visibility: hidden;
}

[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
}

.badge-coming { display: inline-flex; align-items: center; gap: 0.3rem; background: #F1F5F9; color: #64748B; border: 1px dashed #CBD5E1; padding: 0.35rem 0.75rem; border-radius: 6px; font-size: 0.78rem; font-weight: 500; }

[data-testid="stSidebar"] .stCheckbox { display: flex !important; align-items: center !important; margin: 0 !important; padding: 0 !important; min-height: unset !important; }
[data-testid="stSidebar"] .stCheckbox label { padding: 0 !important; min-height: unset !important; gap: 0 !important; }

.param-guide-box { background: #F0F7FF; border: 1.5px solid #B3D1F5; border-radius: 10px; padding: 0.9rem 1rem; margin: 0.5rem 0 1rem; font-size: 0.78rem; color: #1A202C; line-height: 1.7; }
.param-guide-box b { color: #0066CC; }
.param-guide-box code { background: #E8F1FB; color: #0052A3; border-radius: 4px; padding: 1px 5px; font-size: 0.74rem; font-family: monospace; }

/* 관리자 모드 */
.admin-badge-on { display: inline-flex; align-items: center; gap: 0.35rem; background: var(--admin); color: #FFFFFF; padding: 0.3rem 0.75rem; border-radius: 20px; font-size: 0.72rem; font-weight: 700; box-shadow: 0 2px 8px rgba(124,58,237,0.35); letter-spacing: 0.04em; }
.admin-panel { background: var(--bg-white); border: 2px solid var(--admin); border-radius: 14px; padding: 1.5rem 1.75rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(124,58,237,0.12); }
.admin-panel-title { display: flex; align-items: center; gap: 0.6rem; font-size: 1rem; font-weight: 700; color: var(--admin); margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--admin-md); }
.admin-panel-icon { width: 28px; height: 28px; background: var(--admin); border-radius: 7px; display: flex; align-items: center; justify-content: center; color: #FFFFFF !important; font-size: 0.8rem; flex-shrink: 0; }
.admin-kw-tag { display: inline-flex; align-items: center; gap: 0.4rem; background: var(--admin-lt); color: var(--admin); border: 1px solid var(--admin-md); border-radius: 20px; padding: 0.25rem 0.65rem; font-size: 0.76rem; font-weight: 600; margin: 0.2rem; }
.admin-section { background: var(--admin-lt); border: 1px solid var(--admin-md); border-left: 3px solid var(--admin); border-radius: 0 8px 8px 0; padding: 0.6rem 0.9rem; margin: 0.75rem 0 0.5rem; font-size: 0.75rem; font-weight: 700; color: var(--admin); text-transform: uppercase; letter-spacing: 0.07em; }
.admin-stat-box { background: linear-gradient(135deg, var(--admin-lt), #EDE9FE); border: 1px solid var(--admin-md); border-radius: 10px; padding: 0.9rem 1.2rem; text-align: center; }
.admin-stat-num { font-size: 1.8rem; font-weight: 700; color: var(--admin); font-family: 'Inter', sans-serif; line-height: 1; }
.admin-stat-label { font-size: 0.72rem; color: var(--text3); margin-top: 0.25rem; }
.admin-login-modal { max-width: 340px; margin: 3rem auto; background: var(--bg-white); border: 2px solid var(--admin); border-radius: 16px; padding: 2rem 1.75rem; text-align: center; box-shadow: 0 8px 32px rgba(124,58,237,0.18); }
.admin-login-icon { width: 52px; height: 52px; background: var(--admin); border-radius: 14px; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; color: #FFFFFF !important; }
.relearn-badge { display: inline-flex; align-items: center; gap: 0.3rem; background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; border-radius: 6px; padding: 0.3rem 0.65rem; font-size: 0.72rem; font-weight: 600; }
.admin-panel .stTextInput input, .admin-panel .stTextArea textarea { border: 1.5px solid var(--admin-md) !important; border-radius: 8px !important; }
.admin-panel .stTextInput input:focus, .admin-panel .stTextArea textarea:focus { border-color: var(--admin) !important; box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important; }
.admin-panel .stButton > button, .admin-btn > button { background: var(--admin) !important; color: #FFFFFF !important; box-shadow: 0 2px 8px rgba(124,58,237,0.25) !important; }
.admin-panel .stButton > button:hover { background: #6D28D9 !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# ADMIN_PASSWORD 체크
# ============================================================
if "ADMIN_PASSWORD" not in st.secrets:
    st.error("🚨 secrets에 ADMIN_PASSWORD가 없습니다.")
    st.stop()
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]


# ============================================================
# 비밀번호 인증
# ============================================================
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="login-wrap">
        <div class="login-icon">🔵</div>
        <div class="login-title">DAISO SNS ISSUE FINDER</div>
        <div class="login-sub">다이소 SNS 고객불만관리 AI시스템</div>
    </div>
    """, unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        pw = st.text_input("", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        if st.button("로그인", use_container_width=True):
            if pw == st.secrets.get("PASSWORD", ""):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    return False

if not check_password():
    st.stop()


# ============================================================
# 세션 초기화
# ============================================================
_defaults = {
    "admin_mode":            False,
    "admin_show_login":      False,
    "admin_exclude_kws":     [],
    "admin_retrain_log":     [],
    "admin_excluded_urls":   {},
    "analysis_results":      None,
    "analysis_done":         False,
    "dash_filter":           "전체",
    "analysis_stopped":      False,
    "exclude_title_kw_list": [],
    "yt_api_error":          None,
    "excluded_items":        {},
    "gold_labels":           [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# API 키
# ============================================================
NAVER_CLIENT_ID     = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
YOUTUBE_API_KEY     = st.secrets.get("YOUTUBE_API_KEY", "")


# ============================================================
# Google Sheets
# ============================================================
def get_gsheet_client_rw():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def _get_or_create_worksheet(sh, title: str, headers: list):
    try:
        return sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=len(headers))
        ws.append_row(headers)
        return ws

def load_keywords_from_sheet():
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "keywords", ["type","keyword","updated_at"])
        records = ws.get_all_records()
        if not records: return
        df = pd.DataFrame(records)
        for kw_type, session_key in [
            ("neg","neg_kw_list"),("pos","pos_kw_list"),
            ("promo","promo_kw_list"),("exclude","exclude_title_kw_list"),
        ]:
            loaded = df[df["type"] == kw_type]["keyword"].tolist()
            if loaded:
                st.session_state[session_key] = loaded
    except Exception as e:
        st.warning(f"⚠ 키워드 시트 로드 실패: {e}")

def save_keywords_to_sheet():
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "keywords", ["type","keyword","updated_at"])
        ws.clear(); ws.append_row(["type","keyword","updated_at"])
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = []
        for kw_type, session_key in [
            ("neg","neg_kw_list"),("pos","pos_kw_list"),
            ("promo","promo_kw_list"),("exclude","exclude_title_kw_list"),
        ]:
            for kw in st.session_state.get(session_key, []):
                rows.append([kw_type, kw, now])
        if rows: ws.append_rows(rows)
    except Exception as e:
        st.warning(f"⚠ 키워드 저장 실패: {e}")

def load_excluded_urls_from_sheet():
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "excluded_urls", ["url","reason","excluded_at"])
        records = ws.get_all_records()
        if records:
            df = pd.DataFrame(records)
            st.session_state["admin_excluded_urls"] = dict(zip(df["url"], df["reason"]))
    except Exception as e:
        st.warning(f"⚠ 제외 URL 로드 실패: {e}")

def save_excluded_url_to_sheet(url: str, reason: str):
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "excluded_urls", ["url","reason","excluded_at"])
        ws.append_row([url, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    except Exception as e:
        st.warning(f"⚠ 제외 URL 저장 실패: {e}")

def load_goldset_from_sheet():
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "goldset", [
            "link","title","AI판정","확신도","정답레이블","출처","날짜","레이블일시"
        ])
        records = ws.get_all_records()
        if records:
            st.session_state["gold_labels"] = records
    except Exception as e:
        st.warning(f"⚠ 골드셋 로드 실패: {e}")

def save_goldset_to_sheet(entry: dict):
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "goldset", [
            "link","title","AI판정","확신도","정답레이블","출처","날짜","레이블일시"
        ])
        ws.append_row([
            entry.get("link",""), entry.get("title",""),
            entry.get("AI판정",""), entry.get("확신도",""),
            entry.get("정답레이블",""), entry.get("출처",""),
            entry.get("날짜",""), entry.get("레이블일시",""),
        ])
    except Exception as e:
        st.warning(f"⚠ 골드셋 저장 실패: {e}")

if not st.session_state.get("_sheets_loaded"):
    load_keywords_from_sheet()
    load_excluded_urls_from_sheet()
    load_goldset_from_sheet()
    st.session_state["_sheets_loaded"] = True


# ============================================================
# 품명 DB  ★ [자] 소분류 제외 + 품번 4~9자리 + 품명 토큰 매칭
# ============================================================
EXCLUDE_SUBCATEGORIES = {"[자]"}

@st.cache_data(ttl=3600)
def load_product_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        df = pd.DataFrame(sh.sheet1.get_all_records())
        df.columns = [str(c).strip() for c in df.columns]
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        # 품명 토큰 미리 계산
        if "품명" in df.columns:
            df["_tokens"] = df["품명"].apply(
                lambda n: set(re.findall(r'[가-힣]{2,}|[A-Za-z]{3,}', str(n)))
            )
        return df
    except Exception as e:
        st.warning(f"⚠ 품명 DB 로드 실패: {e}")
        return pd.DataFrame(columns=["품번","품명","소분류","_tokens"])

PRODUCT_DB = load_product_db()

VALID_PRODUCT_CODES: set = set()
if not PRODUCT_DB.empty and "품번" in PRODUCT_DB.columns:
    VALID_PRODUCT_CODES = {
        c for c in PRODUCT_DB["품번"].dropna().astype(str).str.strip()
        if re.fullmatch(r'\d{4,9}', c)
    }

def load_subcategories():
    if not PRODUCT_DB.empty and "소분류" in PRODUCT_DB.columns:
        return [
            s for s in PRODUCT_DB["소분류"].dropna().unique()
            if not any(excl in str(s) for excl in EXCLUDE_SUBCATEGORIES)
        ]
    return []

SUBCATEGORIES = load_subcategories()


# ============================================================
# AI 모델 (앙상블: Multilingual + RoBERTa)
# ============================================================
@st.cache_resource(validate=lambda m: m is not None)
def load_multilingual():
    try:
        return pipeline("text-classification",
                        model="tabularisai/multilingual-sentiment-analysis",
                        truncation=True, max_length=512, top_k=None, device=-1)
    except Exception:
        return None

@st.cache_resource(validate=lambda m: m is not None)
def load_roberta():
    try:
        return pipeline("text-classification",
                        model="Chamsol/klue-roberta-sentiment-classification",
                        truncation=True, max_length=512, top_k=None, device=-1)
    except Exception:
        return None


# ============================================================
# 룰베이스 키워드 기본값
# ============================================================
BASE_NEGATIVE_KW = [
    # 품질 불량
    "불량","불량품","불량이에요","불량이야","불량 같아",
    "하자","하자품","하자 있어","결함","결함 있어",
    "고장","고장났","고장나서","고장이에요",
    "망가","망가졌","망가지네","금방 망가","금방망가",
    "부서","부서졌","금방 부서","금방부서",
    "깨졌","깨져서","깨지네","깨지는",
    "뜯겨","뜯겨서","뜯어지","벗겨지","벗겨졌",
    "뒤틀","뒤틀려","휘어","휘었","틀어졌",
    "터졌","터져서","터지네",
    "오래 못가","오래못가","오래 못써",
    "변질","변질됐","녹았","녹이 슬었","녹이 슨",
    # 불만 감정
    "불만","불만이에요","불만이야",
    "실망","실망이에요","너무 실망",
    "짜증","짜증나","짜증나요","짜증났",
    "최악","최악이에요","최악이야","진짜 최악",
    "형편없","형편없어","형편없네",
    "쓰레기","쓰레기 같은","쓰레기야",
    "허접","허접하네","허접해",
    "후회","후회해요","후회됩니다",
    "속았","낚였","사기","사기 같아","뻥이야",
    "가짜","가짜 같아",
    # 부정 평가
    "별로야","별로예요","별로네","진짜 별로","완전 별로",
    "생각보다 별로","기대 이하","기대보다 별로",
    "그냥저냥","글쎄요","애매해요",
    "비추","비추천","비추예요","비추합니다",
    "추천 안","추천안해","추천 못","추천하지 않",
    "사지마","사지 마","사지 말아요",
    "돈낭비","돈 낭비","돈 버렸","돈 아까워",
    "구매 실패","구매실패","쇼핑 실패",
    # 별점
    "별점 1","별점1","별1개","1점짜리","평점 1",
    # 환불/교환
    "환불","환불 요청","환불 했","환불 신청",
    "반품","반품 했","반품 신청",
    "교환","교환 요청","교환 신청",
    "환급","클레임",
    # 위생/오염
    "냄새나","냄새가 나","냄새 나요","악취",
    "오염","오염됐","더럽","더러워","더럽네",
    "불결","지저분","지저분해","위생 문제",
    "이물질","벌레",
    # 색상/품질
    "색번짐","색이 번져","이염","이염됐",
    "색상 달라","색이 달라","색상 차이","색감 차이","색상상이",
    "사진이랑 달라","실물이 달라","색이다름",
    "과점착","접착 안","안 붙어","안붙어",
    # 기능 불량
    "작동 안","작동이 안","안 됩니다","안돼요","잘 안 돼",
    "못 쓰겠","못써요","못쓰겠","쓸 수가 없",
    "쓸모없어","쓸모 없어",
    "뚜껑이 안","뚜껑이 깨","잠금이 안",
    # 포장/수량
    "과포장","수량 적어","수량적음","양이 적어","내용물 적어",
    "원산지 불명확","성능 과장","성능과장",
    # 재구매 거부
    "재구매 안","재구매 의사 없","다시는 안 살","다시 안 살",
]
BASE_POSITIVE_KW = [
    "좋아요","좋았","만족","추천","재구매","최고","훌륭","완벽","편리","예뻐",
    "가성비","합리적","대박","꿀템","강추","마음에 들","만족스럽","굿","짱",
    "갓성비","득템","완전좋","완전 좋","행복","사랑","최애","예쁘다","예쁜",
    "지림","감탄","감동","맘에 쏙","맘에 들어",
]
BASE_PROMO_KW = [
    "다이소 매장","다이소 오픈","다이소 신상","다이소 신제품","다이소 근처",
    "다이소 위치","다이소 영업시간","다이소 매장 위치","다이소 점포",
    "다이소 방문","다이소 주차","다이소에서 구입","다이소 쇼핑",
    "홍보","광고","제품을 받았습니다","제공받아","협찬","무료로 받",
    "내돈내산 아닌","리뷰어","체험단","서포터즈","내돈내산아님",
    "다이소 하울","다이소 추천템","다이소 인기템","다이소 꿀템 추천",
    "다이소 추천 아이템","다이소 베스트","다이소 신상품 추천",
]

if "neg_kw_list"   not in st.session_state: st.session_state["neg_kw_list"]   = list(BASE_NEGATIVE_KW)
if "pos_kw_list"   not in st.session_state: st.session_state["pos_kw_list"]   = list(BASE_POSITIVE_KW)
if "promo_kw_list" not in st.session_state: st.session_state["promo_kw_list"] = list(BASE_PROMO_KW)

def get_neg_kw():   return st.session_state["neg_kw_list"]
def get_pos_kw():   return st.session_state["pos_kw_list"]
def get_promo_kw(): return st.session_state["promo_kw_list"]
def get_excl_kw():  return st.session_state["exclude_title_kw_list"]


# ============================================================
# 관리자 키워드 관리
# ============================================================
def admin_apply_keyword(kw_type: str, keyword: str, action: str = "add"):
    kw = keyword.strip()
    if not kw: return False, "키워드가 비어 있습니다."
    key_map   = {"neg":"neg_kw_list","pos":"pos_kw_list","promo":"promo_kw_list","exclude":"exclude_title_kw_list"}
    label_map = {"neg":"부정 키워드","pos":"긍정 키워드","promo":"홍보 제외 키워드","exclude":"제목 직접 제외 키워드"}
    key = key_map.get(kw_type)
    if not key: return False, "잘못된 키워드 유형입니다."
    lst = st.session_state[key]
    if action == "add":
        if kw in lst: return False, f"이미 등록된 키워드: {kw}"
        lst.append(kw)
        log_msg = f"[추가] {label_map[kw_type]} → '{kw}'"
    else:
        if kw not in lst: return False, f"목록에 없는 키워드: {kw}"
        lst.remove(kw)
        log_msg = f"[삭제] {label_map[kw_type]} → '{kw}'"
    st.session_state["admin_retrain_log"].append({
        "시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "내용": log_msg
    })
    save_keywords_to_sheet()
    return True, log_msg


# ============================================================
# 텍스트 전처리
# ============================================================
def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', str(text))
    text = re.sub(r'&[#\w]+;', ' ', text)
    return text.strip()


# ============================================================
# 판단 근거 문장 추출  ★ 코드4
# ============================================================
def extract_reason_sentence(full_text: str, sentiment: str) -> str:
    kw_list = get_neg_kw() if sentiment == "부정" else (get_pos_kw() if sentiment == "긍정" else [])
    if not kw_list: return ""
    sentences = re.split(r'[.!?。\n]+', full_text)
    best_sent, best_cnt = "", 0
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 5: continue
        cnt = sum(1 for kw in kw_list if kw in sent)
        if cnt > best_cnt:
            best_cnt = cnt; best_sent = sent
    if not best_sent:
        for kw in kw_list:
            idx = full_text.find(kw)
            if idx != -1:
                s = max(0, idx-20); e = min(len(full_text), idx+60)
                best_sent = full_text[s:e].strip(); break
    return best_sent[:120] if best_sent else ""


# ============================================================
# 필터 함수들
# ============================================================
def is_promotional(item: dict) -> bool:
    title = clean_text(item.get("title",""))
    desc  = clean_text(item.get("description",""))
    full  = title + " " + desc
    return (sum(1 for kw in get_promo_kw() if kw in full) >= 1
            and sum(1 for kw in get_neg_kw() if kw in full) == 0)

def is_admin_excluded(item: dict) -> bool:
    if item.get("link","") in st.session_state.get("admin_excluded_urls",{}):
        return True
    title = clean_text(item.get("title",""))
    return any(kw in title for kw in get_excl_kw())

USIM_EXCLUDE_KW = [
    "유심","USIM","유심칩","유심카드","심카드","SIM카드","통신사",
    "SKT","KT","LGU+","알뜰폰","eSIM","이심","정력","정액"
]
def is_usim_related(it):
    text = (clean_text(it.get("title","")) + " " + clean_text(it.get("description",""))).upper()
    return any(kw.upper() in text for kw in USIM_EXCLUDE_KW)


# ============================================================
# 라벨 매핑
# ============================================================
ROBERTA_LABEL_MAP = {
    "positive":"긍정","pos":"긍정","LABEL_2":"긍정","긍정":"긍정",
    "negative":"부정","neg":"부정","LABEL_0":"부정","부정":"부정",
    "neutral":"중립","neu":"중립","LABEL_1":"중립","중립":"중립",
}
MULTI_LABEL_MAP = {
    "Very Negative":"부정","Negative":"부정","Neutral":"중립",
    "Positive":"긍정","Very Positive":"긍정",
    "LABEL_0":"부정","LABEL_1":"부정","LABEL_2":"중립","LABEL_3":"긍정","LABEL_4":"긍정",
}
MULTI_NEG_BOOST = {"Very Negative","LABEL_0"}

def rule_based(text: str):
    neg = sum(1 for kw in get_neg_kw() if kw in text)
    pos = sum(1 for kw in get_pos_kw() if kw in text)
    if neg > pos: return "부정", min(0.65 + neg * 0.08, 0.98)
    if pos > neg: return "긍정", min(0.60 + pos * 0.08, 0.98)
    return "중립", 0.50


# ============================================================
# 다이소 관련성
# ============================================================
DAISO_VARIANTS = ["다이소","DAISO","daiso"]

def is_daiso_related(item: dict) -> bool:
    full = (clean_text(item.get("title","")) + " " + clean_text(item.get("description",""))).upper()
    return any(v.upper() in full for v in DAISO_VARIANTS)

def build_naver_query(raw_keyword: str) -> str:
    kw = raw_keyword.strip()
    if not any(v in kw for v in DAISO_VARIANTS):
        kw = "다이소 " + kw
    return kw


# ============================================================
# 네이버 / 카페 / 유튜브 수집
# ============================================================
def collect_naver_paged(query: str, search_type: str, total: int) -> list:
    all_items, per_page, start_idx = [], 100, 1
    label = "블로그" if search_type == "blog" else "지식인"
    while len(all_items) < total:
        if start_idx > 1000: break
        fetch_cnt = min(per_page, total - len(all_items), 1000 - start_idx + 1)
        if fetch_cnt <= 0: break
        try:
            resp  = requests.get(f"https://openapi.naver.com/v1/search/{search_type}.json",
                headers={"X-Naver-Client-Id":NAVER_CLIENT_ID,"X-Naver-Client-Secret":NAVER_CLIENT_SECRET},
                params={"query":query,"display":fetch_cnt,"start":start_idx,"sort":"date"}, timeout=10)
            items = resp.json().get("items",[])
        except Exception: break
        if not items: break
        for item in items:
            item["출처"] = label; item["검색어"] = query
        all_items.extend(items); start_idx += fetch_cnt
        if len(items) < fetch_cnt: break
    return all_items[:total]

def collect_cafe_paged(query: str, total: int) -> list:
    all_items, per_page, start_idx = [], 100, 1
    while len(all_items) < total:
        if start_idx > 1000: break
        fetch_cnt = min(per_page, total - len(all_items), 1000 - start_idx + 1)
        if fetch_cnt <= 0: break
        try:
            resp  = requests.get("https://openapi.naver.com/v1/search/cafearticle.json",
                headers={"X-Naver-Client-Id":NAVER_CLIENT_ID,"X-Naver-Client-Secret":NAVER_CLIENT_SECRET},
                params={"query":query,"display":fetch_cnt,"start":start_idx,"sort":"date"}, timeout=10)
            items = resp.json().get("items",[])
        except Exception: break
        if not items: break
        for item in items:
            item["출처"] = "카페"; item["검색어"] = query; item["channel"] = item.get("cafename","")
        all_items.extend(items); start_idx += fetch_cnt
        if len(items) < fetch_cnt: break
    return all_items[:total]

def search_youtube(query: str, max_results: int = 30) -> list:
    if not YOUTUBE_API_KEY: return []
    try:
        resp = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "key":YOUTUBE_API_KEY,"q":query,"part":"snippet","type":"video",
            "maxResults":min(max_results,50),"order":"date","relevanceLanguage":"ko","regionCode":"KR"
        }, timeout=10)
        data = resp.json()
    except Exception as e:
        st.session_state["yt_api_error"] = f"네트워크 오류: {e}"; return []
    if "error" in data:
        err = data["error"]; code = err.get("code","")
        reason = err.get("errors",[{}])[0].get("reason","")
        if code == 403 and reason == "quotaExceeded":
            st.session_state["yt_api_error"] = "🚫 YouTube API 일일 쿼터 초과"
        else:
            st.session_state["yt_api_error"] = f"YouTube API 오류 ({code}): {err.get('message','')}"
        return []
    items     = data.get("items",[])
    video_ids = [i["id"]["videoId"] for i in items if i.get("id",{}).get("videoId")]
    stats_map = {}
    if video_ids:
        try:
            for sv in requests.get("https://www.googleapis.com/youtube/v3/videos",
                params={"key":YOUTUBE_API_KEY,"id":",".join(video_ids),"part":"statistics"},
                timeout=10).json().get("items",[]):
                stats_map[sv["id"]] = sv.get("statistics",{})
        except Exception: pass
    results = []
    for item in items:
        vid_id  = item.get("id",{}).get("videoId","")
        snippet = item.get("snippet",{})
        stats   = stats_map.get(vid_id,{})
        pub_raw = snippet.get("publishedAt","")
        try:   pub_dt = datetime.strptime(pub_raw[:10],"%Y-%m-%d"); pub_str = pub_dt.strftime("%Y-%m-%d")
        except: pub_dt = None; pub_str = pub_raw[:10]
        results.append({
            "출처":"유튜브","검색어":query,"video_id":vid_id,
            "title":snippet.get("title",""),"description":snippet.get("description","")[:300],
            "channel":snippet.get("channelTitle",""),
            "thumbnail":snippet.get("thumbnails",{}).get("medium",{}).get("url",""),
            "link":f"https://www.youtube.com/watch?v={vid_id}",
            "날짜":pub_str,"pub_dt":pub_dt,
            "views":int(stats.get("viewCount",0) or 0),
            "likes":int(stats.get("likeCount",0) or 0),
            "comments":int(stats.get("commentCount",0) or 0),
        })
    return results


# ============================================================
# 날짜 파싱  ★ 코드4 RFC2822 안전 파싱 적용
# ============================================================
def parse_date(item: dict):
    ds = item.get("postdate") or item.get("pubDate","")
    if not ds: return None
    ds = str(ds).strip()
    if re.fullmatch(r'\d{8}', ds):
        try: return datetime.strptime(ds, "%Y%m%d")
        except: pass
    # RFC 2822 (카페·지식인 pubDate) — email.utils로 timezone 포함 안전 처리
    try:
        t = parsedate(ds)
        if t: return datetime(*t[:6])
    except: pass
    return None

def filter_by_date(items: list, start_dt: date, end_dt: date) -> list:
    s = datetime(start_dt.year, start_dt.month, start_dt.day)
    e = datetime(end_dt.year,   end_dt.month,   end_dt.day, 23, 59, 59)
    result = []
    for item in items:
        dt = item.get("pub_dt") if item.get("출처") == "유튜브" else parse_date(item)
        if dt is None:
            result.append(item)   # 날짜 파싱 실패 → 포함 (유실 방지)
        elif s <= dt <= e:
            result.append(item)
    return result


# ============================================================
# 품번/품명/소분류 추출  ★ 품번 4~9자리 + 품명 토큰 매칭
# ============================================================
DATE_PATS = [
    r'\b20\d{6}\b', r'\b\d{4}[-./]\d{2}[-./]\d{2}\b',
    r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b',
    r'\b\d{4}년\s*\d{1,2}월', r'\b\d{1,2}월\s*\d{1,2}일',
]
def is_date_like(t: str) -> bool:
    t = t.strip()
    for p in DATE_PATS:
        if re.fullmatch(p, t): return True
    return bool(re.fullmatch(r'\d{6,8}', t))

def extract_product_code(text: str) -> str:
    """1순위: 품명 토큰 매칭 / 2순위: 숫자 품번 4~9자리 직접 매칭"""
    if PRODUCT_DB.empty: return ""
    found_codes = []
    # 1순위: 품명 키워드 매칭
    if "_tokens" in PRODUCT_DB.columns:
        for _, row in PRODUCT_DB.iterrows():
            tokens = row.get("_tokens", set())
            key_tokens = [t for t in tokens if len(t) >= 3]
            if key_tokens and any(t in text for t in key_tokens):
                code = str(row.get("품번","")).strip()
                if code and code not in found_codes:
                    found_codes.append(code)
    # 2순위: 숫자 품번 직접 매칭 (4~9자리)
    if not found_codes and VALID_PRODUCT_CODES:
        raw_nums = re.findall(r'\b(\d{4,9})\b', text)
        for c in raw_nums:
            if is_date_like(c): continue
            if c in VALID_PRODUCT_CODES and c not in found_codes:
                found_codes.append(c)
    return ", ".join(found_codes[:3]) if found_codes else ""

def extract_price(text: str) -> str:
    prices = re.findall(r'\d{1,3}(?:,\d{3})*원', text)
    return ", ".join(dict.fromkeys(prices)) if prices else ""

SYNONYM_MAP = {
    "꽂이":"홀더","홀더":"꽂이","수납":"정리","정리":"수납",
    "바구니":"수납함","수납함":"바구니","케이스":"커버","커버":"케이스",
    "그릇":"용기","용기":"그릇","팬":"후라이팬","후라이팬":"팬",
    "집게":"클립","클립":"집게","수건":"타월","타월":"수건",
}

def extract_subcategory(text: str) -> str:
    if not SUBCATEGORIES: return ""
    found = [s for s in SUBCATEGORIES if s in text]
    if found: return ", ".join(dict.fromkeys(found))
    text_syn = text
    for w, s in SYNONYM_MAP.items(): text_syn = text_syn.replace(w, s)
    found2 = [s for s in SUBCATEGORIES if s in text_syn]
    if found2: return ", ".join(dict.fromkeys(found2))
    tokens = re.findall(r'[가-힣]{2,}', text)
    found3 = [s for s in SUBCATEGORIES if any(t in tokens for t in re.findall(r'[가-힣]{2,}', s) if len(t) >= 2)]
    if found3:
        found3.sort(key=lambda s: sum(1 for t in re.findall(r'[가-힣]{2,}', s) if t in tokens), reverse=True)
        return found3[0]
    return ""

def match_product_name(code: str) -> str:
    if PRODUCT_DB.empty or not code: return ""
    names = []
    for c in [c.strip() for c in code.split(",")][:3]:
        row = PRODUCT_DB[PRODUCT_DB["품번"].astype(str).str.strip() == c]
        if not row.empty:
            name = str(row.iloc[0].get("품명",""))
            if name and name not in names: names.append(name)
    return ", ".join(names)

def match_subcategory_from_code(code: str) -> str:
    if PRODUCT_DB.empty or not code: return ""
    for c in [c.strip() for c in code.split(",")][:3]:
        row = PRODUCT_DB[PRODUCT_DB["품번"].astype(str).str.strip() == c]
        if not row.empty and "소분류" in row.columns:
            val = str(row.iloc[0].get("소분류",""))
            if val and not any(excl in val for excl in EXCLUDE_SUBCATEGORIES):
                return val
    return ""


# ============================================================
# 골드셋 기반 자가학습 분석
# ============================================================
def analyze_goldset(gold: list, current_threshold: int = 55):
    if not gold: return None
    result = {"total":len(gold),"accuracy":0,"recall":{},"precision":{},"threshold_rec":current_threshold,"threshold_msg":"","suggested_kw":[],"confusion":{}}
    labels = ["부정","긍정","중립"]
    match = sum(1 for g in gold if g.get("AI판정") == g.get("정답레이블"))
    result["accuracy"] = round(match / len(gold) * 100, 1)
    for lbl in labels:
        tp  = sum(1 for g in gold if g.get("정답레이블")==lbl and g.get("AI판정")==lbl)
        act = sum(1 for g in gold if g.get("정답레이블")==lbl)
        pre = sum(1 for g in gold if g.get("AI판정")==lbl)
        result["recall"][lbl]    = round(tp/act*100,1) if act else 0
        result["precision"][lbl] = round(tp/pre*100,1) if pre else 0
    confusion_list = [f"{g['AI판정']}→{g['정답레이블']}" for g in gold if g.get("AI판정") != g.get("정답레이블")]
    result["confusion"] = dict(Counter(confusion_list).most_common(6))
    neg_recall = result["recall"].get("부정",0)
    neg_prec   = result["precision"].get("부정",0)
    if neg_recall < 55:
        result["threshold_rec"] = max(current_threshold-5,40)
        result["threshold_msg"] = f"부정 재현율 {neg_recall}% 낮음 → threshold {result['threshold_rec']}%로 낮추기 권장"
    elif neg_prec < 55:
        result["threshold_rec"] = min(current_threshold+5,75)
        result["threshold_msg"] = f"부정 정밀도 {neg_prec}% 낮음 → threshold {result['threshold_rec']}%로 높이기 권장"
    else:
        result["threshold_rec"] = current_threshold
        result["threshold_msg"] = f"현재 threshold {current_threshold}% 적정"
    missed_neg = [g for g in gold if g.get("정답레이블")=="부정" and g.get("AI판정")!="부정"]
    kw_candidates = []
    stopwords = {"다이소","구매","상품","제품","사용","이에요","이야","입니다","에서","했어","했는","이네"}
    existing = set(st.session_state.get("neg_kw_list",[]))
    for g in missed_neg:
        for t in re.findall(r'[가-힣]{2,6}', g.get("title","")):
            if t not in existing and t not in stopwords and t not in kw_candidates:
                kw_candidates.append(t)
    result["suggested_kw"] = [kw for kw,_ in Counter(kw_candidates).most_common(10)]
    return result


# ============================================================
# 엑셀 생성  ★ 판단 근거 문장 컬럼 포함
# ============================================================
def create_excel(data: list, start_dt: date, end_dt: date) -> io.BytesIO:
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "DAISO SNS ISSUE FINDER"
    headers = ["출처","검색어","소분류","품번","품명","가격언급","제목","링크","날짜","감성","확신도(%)","판단 근거 문장","채널/카페명","조회수","좋아요","댓글수"]
    ws.append(headers)
    hf   = openpyxl.styles.Font(bold=True, color="0066CC", name="Malgun Gothic")
    hfil = openpyxl.styles.PatternFill(start_color="E8F1FB", end_color="E8F1FB", fill_type="solid")
    hbrd = openpyxl.styles.Border(bottom=openpyxl.styles.Side(style="thin", color="0066CC"))
    for c in range(1, len(headers)+1):
        cell = ws.cell(1,c); cell.font = hf; cell.fill = hfil; cell.border = hbrd
        cell.alignment = openpyxl.styles.Alignment(horizontal="center")
    col_bg  = {"긍정":"E8F5EE","부정":"FDEEEE","중립":"FFFBE8"}
    col_txt = {"긍정":"16A34A","부정":"DC2626","중립":"CA8A04"}
    for ri, row in enumerate(data, 2):
        ws.append([row.get(k,"") for k in ["출처","검색어","소분류","품번","품명","가격언급","title","link","날짜","감성","확신도","판단근거","channel","views","likes","comments"]])
        s = row.get("감성","")
        if s in col_bg:
            ws.cell(ri,10).fill = openpyxl.styles.PatternFill(start_color=col_bg[s], end_color=col_bg[s], fill_type="solid")
            ws.cell(ri,10).font = openpyxl.styles.Font(color=col_txt[s], bold=True, name="Malgun Gothic")
        ev_cell = ws.cell(ri,12)
        if ev_cell.value:
            ev_cell.font = openpyxl.styles.Font(italic=True, color="555555", name="Malgun Gothic", size=9)
    for letter, width in zip("ABCDEFGHIJKLMNOP", [8,20,15,15,20,12,45,50,12,8,10,60,20,10,10,10]):
        ws.column_dimensions[letter].width = width
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf


# ============================================================
# 헬퍼
# ============================================================
SENT_BADGE      = {"긍정":"badge-pos","부정":"badge-neg","중립":"badge-neu"}
SENT_REASON_CLS = {"긍정":"pos","부정":"","중립":"neu"}

def icon(label: str) -> str:
    return f'<span class="section-title-icon">{label}</span>'

def fmt_score(score) -> str:
    try:    return f"{int(round(float(score)))}%"
    except: return f"{score}%"

def render_prod_tags(r: dict) -> str:
    tags = ""
    if r.get("소분류"): tags += f'<span class="prod-tag">📂 {r["소분류"]}</span>'
    if r.get("품번"):   tags += f'<span class="prod-tag">🔢 {r["품번"]}</span>'
    if r.get("품명"):   tags += f'<span class="prod-tag">🏷 {r["품명"]}</span>'
    if r.get("가격언급"): tags += f'<span class="prod-tag">💰 {r["가격언급"]}</span>'
    return tags

def render_result_card(r: dict):
    """★ 코드4 스타일 카드: 품목 태그 + 판단 근거 문장 포함"""
    _b      = SENT_BADGE.get(r["감성"],"")
    _rc     = SENT_REASON_CLS.get(r["감성"],"")
    _badge  = f'<span class="{_b}">{r["감성"]} {fmt_score(r["확신도"])}</span>'
    _title  = r.get("title") or "(제목 없음)"
    _tags   = render_prod_tags(r)
    _reason = r.get("판단근거","")
    _price  = f'<span>💰 {r["가격언급"]}</span>' if r.get("가격언급") else ""
    _views  = ""
    if r.get("출처") == "유튜브":
        v = f"{r['views']:,}" if isinstance(r.get("views"),int) else "-"
        l = f"{r['likes']:,}" if isinstance(r.get("likes"),int) else "-"
        c = f"{r['comments']:,}" if isinstance(r.get("comments"),int) else "-"
        _views = f'<span>▶ {v}</span><span>♥ {l}</span><span>💬 {c}</span>'
    prod_html   = f'<div style="margin-top:0.4rem;">{_tags}</div>' if _tags else ""
    reason_html = f'<div class="result-reason {_rc}">💬 {_reason}</div>' if _reason else ""
    st.markdown(
        f'<div class="result-card">'
        f'<div class="result-title"><a href="{r.get("link","")}" target="_blank" style="color:#1A202C;text-decoration:none;">{_title}</a></div>'
        f'<div class="result-meta">'
        f'<span>📍 {r.get("출처","")}</span><span>🔍 {r.get("검색어","")}</span><span>📅 {r.get("날짜","")}</span>'
        f'{_price}{_views}{_badge}'
        f'</div>'
        f'{prod_html}{reason_html}'
        f'</div>',
        unsafe_allow_html=True)


# ============================================================
# 정렬  ★ 코드4
# ============================================================
def sort_results(data: list, sort_key: str) -> list:
    if sort_key == "최신날짜순":  return sorted(data, key=lambda x: x.get("날짜",""), reverse=True)
    if sort_key == "부정 높은순": return sorted(data, key=lambda x: (x["감성"]=="부정", x.get("확신도",0)), reverse=True)
    if sort_key == "긍정 높은순": return sorted(data, key=lambda x: (x["감성"]=="긍정", x.get("확신도",0)), reverse=True)
    if sort_key == "조회수 높은순": return sorted(data, key=lambda x: x.get("views") or 0, reverse=True)
    return data


# ============================================================
# 레이블링 버튼 (관리자 전용)
# ============================================================
def render_label_buttons(r: dict, idx: int):
    if not st.session_state.get("admin_mode"): return
    item_link = r.get("link", str(idx))
    already = next((g for g in st.session_state.get("gold_labels",[]) if g.get("link") == item_link), None)
    if already:
        color = {"부정":"#DC2626","긍정":"#16A34A","중립":"#CA8A04"}.get(already.get("정답레이블",""),"#718096")
        st.markdown(f'<div style="background:#F8F9FB;border:1px solid #E2E8F0;border-radius:6px;padding:0.35rem 0.75rem;font-size:0.73rem;color:#718096;margin-bottom:0.4rem;">✅ 정답 레이블: <strong style="color:{color};">{already.get("정답레이블","")}</strong></div>', unsafe_allow_html=True)
    else:
        lb0, lb1, lb2, lb3 = st.columns([2.5,1,1,1])
        with lb0:
            st.markdown('<div style="font-size:0.72rem;color:#7C3AED;font-weight:600;padding-top:0.45rem;">🏷 정답 레이블 표기:</div>', unsafe_allow_html=True)
        def _save(label):
            entry = {"link":r.get("link",""),"title":r.get("title","")[:80],"AI판정":r["감성"],"확신도":r["확신도"],"정답레이블":label,"출처":r.get("출처",""),"날짜":r.get("날짜",""),"레이블일시":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            st.session_state["gold_labels"].append(entry)
            save_goldset_to_sheet(entry)
        with lb1:
            if st.button("🔴 부정", key=f"lb_neg_{idx}", use_container_width=True): _save("부정"); st.rerun()
        with lb2:
            if st.button("🟢 긍정", key=f"lb_pos_{idx}", use_container_width=True): _save("긍정"); st.rerun()
        with lb3:
            if st.button("⚪ 중립", key=f"lb_neu_{idx}", use_container_width=True): _save("중립"); st.rerun()


# ============================================================
# 관리자 버튼
# ============================================================
admin_col1, admin_col2 = st.columns([10,1])
with admin_col2:
    if st.session_state["admin_mode"]:
        if st.button("🔓 관리자", key="admin_toggle_off"):
            st.session_state["admin_mode"] = False
            st.session_state["admin_show_login"] = False
            st.rerun()
        st.markdown('<span class="admin-badge-on">🔓 ADMIN</span>', unsafe_allow_html=True)
    else:
        if st.button("🔐 관리자", key="admin_toggle_on"):
            st.session_state["admin_show_login"] = not st.session_state["admin_show_login"]
            st.rerun()

if st.session_state["admin_show_login"] and not st.session_state["admin_mode"]:
    with st.container():
        st.markdown("""<div class="admin-login-modal"><div class="admin-login-icon">🛡️</div><div class="login-title" style="color:#7C3AED;">관리자 로그인</div><div class="login-sub">관리자 전용 기능에 접근합니다</div></div>""", unsafe_allow_html=True)
        _, mid_col, _ = st.columns([1,2,1])
        with mid_col:
            admin_pw = st.text_input("관리자 비밀번호", type="password", placeholder="비밀번호 입력", label_visibility="collapsed", key="admin_pw_input")
            lc, cc = st.columns(2)
            with lc:
                if st.button("로그인", key="admin_login_confirm", use_container_width=True):
                    if admin_pw == ADMIN_PASSWORD:
                        st.session_state["admin_mode"] = True
                        st.session_state["admin_show_login"] = False
                        st.success("✅ 관리자 모드 활성화"); st.rerun()
                    else:
                        st.error("비밀번호가 틀렸습니다.")
            with cc:
                if st.button("취소", key="admin_login_cancel", use_container_width=True):
                    st.session_state["admin_show_login"] = False; st.rerun()
    st.markdown("---")


# ============================================================
# 관리자 패널
# ============================================================
if st.session_state["admin_mode"]:
    st.markdown("""<div class="admin-panel"><div class="admin-panel-title"><div class="admin-panel-icon">🛡</div>관리자 모드 — AI 재학습 키워드 관리<span class="admin-badge-on" style="margin-left:auto;">🔓 ADMIN ON</span></div></div>""", unsafe_allow_html=True)

    adm_tab1, adm_tab2, adm_tab3, adm_tab4, adm_tab5 = st.tabs(
        ["➕ 키워드 추가","🗑 키워드 삭제","📋 현재 키워드 목록","📜 재학습 로그","🏷 골드셋 관리"])

    with adm_tab1:
        st.markdown('<div class="admin-section">새 키워드 추가 → AI 분석에 즉시 반영 + Google Sheets 자동 저장</div>', unsafe_allow_html=True)
        ac1, ac2 = st.columns([2,1])
        with ac1: new_kw_input = st.text_input("추가할 키워드", placeholder="예: 냄새나요  /  가성비 최고", key="admin_new_kw")
        with ac2:
            kw_type_sel = st.selectbox("키워드 유형", options=["neg","pos","promo","exclude"],
                format_func=lambda x: {"neg":"🔴 부정","pos":"🟢 긍정","promo":"🟡 홍보 제외","exclude":"⛔ 제목 직접 제외"}[x], key="admin_kw_type")
        if st.button("✅ 키워드 추가 & AI 재학습 반영", key="admin_add_kw_btn", use_container_width=True):
            ok, msg = admin_apply_keyword(kw_type_sel, new_kw_input, "add")
            if ok: st.success(f"✅ {msg}"); st.markdown('<span class="relearn-badge">🔄 AI 룰베이스 재학습 완료 + Sheets 저장 완료</span>', unsafe_allow_html=True)
            else:  st.warning(f"⚠ {msg}")

    with adm_tab2:
        st.markdown('<div class="admin-section">기존 키워드 삭제</div>', unsafe_allow_html=True)
        del_type = st.selectbox("삭제할 키워드 유형", options=["neg","pos","promo","exclude"],
            format_func=lambda x: {"neg":"🔴 부정","pos":"🟢 긍정","promo":"🟡 홍보 제외","exclude":"⛔ 제목 직접 제외"}[x], key="admin_del_kw_type")
        key_map_del = {"neg":"neg_kw_list","pos":"pos_kw_list","promo":"promo_kw_list","exclude":"exclude_title_kw_list"}
        kw_list_for_del = st.session_state[key_map_del[del_type]]
        if kw_list_for_del:
            del_target = st.selectbox("삭제할 키워드 선택", options=kw_list_for_del, key="admin_del_kw_target")
            if st.button("🗑 선택 키워드 삭제", key="admin_del_kw_btn", use_container_width=True):
                ok, msg = admin_apply_keyword(del_type, del_target, "remove")
                if ok: st.success(f"✅ {msg}"); st.rerun()
                else:  st.warning(f"⚠ {msg}")
        else: st.info("해당 유형에 등록된 키워드가 없습니다.")

    with adm_tab3:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🔴 부정 키워드**")
            st.markdown("".join([f'<span class="admin-kw-tag">{k}</span>' for k in get_neg_kw()]), unsafe_allow_html=True)
            st.markdown("**🟢 긍정 키워드**")
            st.markdown("".join([f'<span class="admin-kw-tag" style="background:#F0FDF4;color:#16A34A;border-color:#A7F3D0;">{k}</span>' for k in get_pos_kw()]), unsafe_allow_html=True)
        with col_b:
            st.markdown("**🟡 홍보 제외 키워드**")
            st.markdown("".join([f'<span class="admin-kw-tag" style="background:#FEFCE8;color:#CA8A04;border-color:#FDE68A;">{k}</span>' for k in get_promo_kw()]), unsafe_allow_html=True)
            st.markdown("**⛔ 제목 직접 제외**")
            excl_tags = "".join([f'<span class="admin-kw-tag" style="background:#FEF2F2;color:#DC2626;border-color:#FCA5A5;">{k}</span>' for k in get_excl_kw()])
            st.markdown(excl_tags or "<span style='color:#718096;font-size:0.82rem;'>없음</span>", unsafe_allow_html=True)
        sc1,sc2,sc3,sc4 = st.columns(4)
        for col, label, count in [(sc1,"부정",len(get_neg_kw())),(sc2,"긍정",len(get_pos_kw())),(sc3,"홍보 제외",len(get_promo_kw())),(sc4,"직접 제외",len(get_excl_kw()))]:
            with col: st.markdown(f'<div class="admin-stat-box"><div class="admin-stat-num">{count}</div><div class="admin-stat-label">{label}</div></div>', unsafe_allow_html=True)
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        if st.button("🔄 전체 키워드 기본값으로 초기화", key="admin_reset_kw"):
            st.session_state["neg_kw_list"] = list(BASE_NEGATIVE_KW)
            st.session_state["pos_kw_list"] = list(BASE_POSITIVE_KW)
            st.session_state["promo_kw_list"] = list(BASE_PROMO_KW)
            st.session_state["exclude_title_kw_list"] = []
            save_keywords_to_sheet()
            st.success("✅ 기본값으로 초기화 완료"); st.rerun()

    with adm_tab4:
        log = st.session_state.get("admin_retrain_log",[])
        if log:
            log_df = pd.DataFrame(list(reversed(log)))
            st.dataframe(log_df, use_container_width=True, hide_index=True, height=300)
            st.download_button("📥 로그 CSV", log_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "admin_log.csv", "text/csv")
        else: st.info("아직 재학습 이력이 없습니다.")

    with adm_tab5:
        gold = st.session_state.get("gold_labels",[])
        st.markdown('<div class="admin-section">골드셋 현황 — AI 판정 정확도 실시간 측정</div>', unsafe_allow_html=True)
        if len(gold) < 10:
            st.info(f"현재 {len(gold)}건 레이블링됨. 10건 이상부터 정확도 분석이 활성화됩니다.")
        else:
            _cur_thr = st.session_state.get("_cur_threshold", 55)
            analysis = analyze_goldset(gold, current_threshold=_cur_thr)
            acc_color = "#16A34A" if analysis["accuracy"] >= 70 else "#CA8A04" if analysis["accuracy"] >= 50 else "#DC2626"
            st.markdown(f"""<div style="background:#F0F7FF;border:1.5px solid #B3D1F5;border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem;">
                <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">
                    <div><div style="font-size:0.72rem;color:#718096;font-weight:600;">AI 정확도</div>
                    <div style="font-size:2rem;font-weight:700;color:{acc_color};font-family:Inter;">{analysis["accuracy"]}%</div>
                    <div style="font-size:0.72rem;color:#718096;">{analysis["total"]}건 기준</div></div>
                    <div style="flex:1;min-width:200px;"><div style="font-size:0.72rem;color:#718096;font-weight:600;margin-bottom:0.3rem;">🎯 Threshold 추천</div>
                    <div style="font-size:0.85rem;color:#0066CC;font-weight:600;">{analysis["threshold_msg"]}</div></div>
                </div></div>""", unsafe_allow_html=True)
            perf_data = [{"감성":lbl,"재현율 Recall (%)":analysis["recall"].get(lbl,0),"정밀도 Precision (%)":analysis["precision"].get(lbl,0),"판단":"✅ 양호" if analysis["recall"].get(lbl,0)>=65 and analysis["precision"].get(lbl,0)>=65 else "⚠ 개선 필요"} for lbl in ["부정","긍정","중립"]]
            st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True, height=140)
            if analysis["confusion"]:
                st.markdown("**AI 오판 패턴**")
                conf_html = ""
                for pattern, cnt in analysis["confusion"].items():
                    parts = pattern.split("→")
                    if len(parts) == 2:
                        conf_html += f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0.75rem;background:#FEF2F2;border:1px solid #FCA5A5;border-radius:6px;margin-bottom:0.3rem;"><span style="color:#DC2626;font-weight:600;">{parts[0]}</span><span style="color:#718096;">→ 실제</span><span style="color:#16A34A;font-weight:600;">{parts[1]}</span><span style="margin-left:auto;background:#FEE2E2;color:#DC2626;padding:1px 8px;border-radius:10px;font-size:0.75rem;">{cnt}건</span></div>'
                st.markdown(conf_html, unsafe_allow_html=True)
            suggested = analysis.get("suggested_kw",[])
            if suggested:
                st.markdown('<div class="admin-section" style="margin-top:1rem;">키워드 자동 추출 — AI가 놓친 부정 글에서 추출</div>', unsafe_allow_html=True)
                st.markdown('<span style="font-size:0.78rem;color:#718096;">AI가 중립으로 잘못 판정한 부정 글에서 자주 나온 표현입니다. 승인할 키워드를 선택 후 추가하세요.</span>', unsafe_allow_html=True)
                selected_kws = []
                kw_cols = st.columns(5)
                for i, kw in enumerate(suggested):
                    with kw_cols[i%5]:
                        if st.checkbox(kw, key=f"suggest_kw_{i}"): selected_kws.append(kw)
                if selected_kws and st.button("✅ 선택 키워드 부정 목록에 추가", key="add_suggested_kw", use_container_width=True):
                    added = []
                    for kw in selected_kws:
                        ok, msg = admin_apply_keyword("neg", kw, "add")
                        if ok: added.append(kw)
                    if added: st.success(f"✅ {len(added)}개 키워드 추가: {', '.join(added)}"); st.rerun()
            st.markdown("---")

        st.markdown('<div class="admin-section">레이블링 데이터 관리</div>', unsafe_allow_html=True)
        if gold:
            gold_df = pd.DataFrame(gold)
            dist = Counter(g.get("정답레이블","") for g in gold)
            gc1, gc2, gc3 = st.columns(3)
            for col, lbl, color in [(gc1,"부정","#DC2626"),(gc2,"긍정","#16A34A"),(gc3,"중립","#CA8A04")]:
                with col: st.markdown(f'<div class="admin-stat-box"><div class="admin-stat-num" style="color:{color};">{dist.get(lbl,0)}</div><div class="admin-stat-label">{lbl}</div></div>', unsafe_allow_html=True)
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            display_cols = [c for c in ["title","AI판정","확신도","정답레이블","출처","날짜","레이블일시"] if c in gold_df.columns]
            st.dataframe(gold_df[display_cols].tail(50), use_container_width=True, hide_index=True, height=250)
            g_dl1, g_dl2 = st.columns(2)
            with g_dl1:
                st.download_button("📥 골드셋 CSV 다운로드", gold_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), f"goldset_{date.today()}.csv", "text/csv", use_container_width=True)
            with g_dl2:
                if st.button("🗑 골드셋 전체 초기화", key="gold_reset", use_container_width=True):
                    st.session_state["gold_labels"] = []; st.success("초기화 완료"); st.rerun()
        else: st.info("아직 레이블링 데이터가 없습니다. 분석 후 각 글 카드에서 정답을 표기해주세요.")

    st.markdown("---")


# ============================================================
# 앱 헤더
# ============================================================
st.markdown("""
<div class="app-header">
    <div style="display:flex;align-items:center;gap:0.5rem;flex-shrink:0;">
        <div style="width:48px;height:48px;background:#0066CC;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 2px 6px rgba(0,102,204,0.35);">
            <svg width="30" height="20" viewBox="0 0 60 38" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M0 2 H8 Q16 2 16 10 Q16 18 8 18 H0 Z M4 5 V15 H8 Q12 15 12 10 Q12 5 8 5 Z" fill="#FFFFFF"/>
                <path d="M18 18 L24 2 L30 18 M20.5 12 H27.5" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
                <rect x="33" y="2" width="3.5" height="16" rx="1" fill="#FFFFFF"/>
                <path d="M40 15 Q40 18 44 18 Q48 18 48 14.5 Q48 11 44 10 Q40 9 40 5.5 Q40 2 44 2 Q48 2 48 5" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
                <ellipse cx="54" cy="10" rx="5" ry="8" stroke="#FFFFFF" stroke-width="3" fill="none"/>
            </svg>
        </div>
    </div>
    <div style="width:1px;height:36px;background:#E2E8F0;margin:0 0.25rem;flex-shrink:0;"></div>
    <div>
        <div class="header-title">SNS Issue Finder : 고객 불만 AI 자동 분석</div>
        <div class="header-sub">네이버 블로그 · 지식인 · 카페 · 유튜브 &nbsp;|&nbsp; Multilingual Sentiment × KLUE-RoBERTa Ensemble</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.markdown("""<div style="display:flex;align-items:center;gap:0.6rem;padding-bottom:1rem;border-bottom:1px solid #E2E8F0;margin-bottom:0.25rem;">
        <div style="width:32px;height:32px;background:#0066CC;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,102,204,0.3);">
            <span style="color:#FFFFFF;font-size:0.65rem;font-weight:900;letter-spacing:0.05em;font-family:'Inter',sans-serif;">D</span>
        </div>
        <div>
            <div style="font-weight:700;font-size:0.95rem;color:#1A202C;">DAISO ISSUE FINDER</div>
            <div style="font-size:0.68rem;color:#718096;">Created by 데이터분석팀</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── 채널 ──
    st.markdown("""<div class="sb-section" style="margin:0.5rem 0 0.4rem;"><div class="sb-section-icon"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/></svg></div><span class="sb-section-text">CHANNEL</span></div>""", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        cb1, ic1 = st.columns([1,4])
        with cb1: search_blog = st.checkbox("블로그", value=True, key="cb_blog", label_visibility="collapsed")
        with ic1: st.markdown('<div class="ch-row"><div class="ch-icon ch-naver">N</div><span class="ch-label">블로그</span></div>', unsafe_allow_html=True)
        cb2, ic2 = st.columns([1,4])
        with cb2: search_cafe = st.checkbox("카페", value=True, key="cb_cafe", label_visibility="collapsed")
        with ic2: st.markdown('<div class="ch-row"><div class="ch-icon ch-naver">N</div><span class="ch-label">카페</span></div>', unsafe_allow_html=True)
    with col_right:
        cb3, ic3 = st.columns([1,4])
        with cb3: search_kin = st.checkbox("지식인", value=True, key="cb_kin", label_visibility="collapsed")
        with ic3: st.markdown('<div class="ch-row"><div class="ch-icon ch-naver">N</div><span class="ch-label">지식인</span></div>', unsafe_allow_html=True)
        cb4, ic4 = st.columns([1,4])
        with cb4: search_yt = st.checkbox("유튜브", value=True, key="cb_yt", label_visibility="collapsed")
        with ic4: st.markdown('<div class="ch-row"><div class="ch-icon ch-youtube"><svg width="9" height="9" viewBox="0 0 24 24" fill="#FFFFFF"><polygon points="5,3 19,12 5,21"/></svg></div><span class="ch-label">유튜브</span></div>', unsafe_allow_html=True)

    # ── 검색어 ──
    st.markdown("""<div class="sb-section" style="margin:0.5rem 0 0.3rem;"><div class="sb-section-icon"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div><span class="sb-section-text">Searching Word</span></div>""", unsafe_allow_html=True)
    keywords_input = st.text_area("", value="다이소 상품불량\n다이소 불량\n다이소 별로", height=80, label_visibility="collapsed", placeholder="줄바꿈으로 구분 · 최대 3개")
    st.markdown('<span class="sb-hint">줄바꿈으로 구분, 최대 3개<br>※ \'다이소\' 없으면 자동 추가됩니다</span>', unsafe_allow_html=True)

    # ── 분석 기간 ──
    st.markdown("""<div class="sb-section" style="margin:0.5rem 0 0.3rem;"><div class="sb-section-icon"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div><span class="sb-section-text">분석 기간</span></div>""", unsafe_allow_html=True)
    _default_start = date.today() - timedelta(days=365)
    _default_end   = date.today()
    dc1, dc2 = st.columns(2, gap="small")
    with dc1:
        st.markdown('<span class="date-label">시작일</span>', unsafe_allow_html=True)
        start_date = st.date_input("시작일", value=_default_start, label_visibility="collapsed", key="date_start")
    with dc2:
        st.markdown('<span class="date-label">종료일</span>', unsafe_allow_html=True)
        end_date = st.date_input("종료일", value=_default_end, label_visibility="collapsed", key="date_end")
    st.markdown(f'<span class="sb-hint">기본값: 최근 1년 ({_default_start} ~ {_default_end})</span>', unsafe_allow_html=True)

    # ── 수집 개수 ──
    st.markdown("""<div class="sb-section" style="margin:0.5rem 0 0.3rem;"><div class="sb-section-icon"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg></div><span class="sb-section-text">분석개수</span></div>""", unsafe_allow_html=True)
    display_count = st.number_input("감성 판단 기준", min_value=100, max_value=5000, value=100, step=100, label_visibility="collapsed")
    st.markdown('<span class="sb-hint">데이터 수집건수 · 100 ~ 5,000 (±100)</span>', unsafe_allow_html=True)

    # ── 감성 파라미터 ──
    st.markdown("""<div class="sb-section" style="margin:0.5rem 0 0.3rem;"><div class="sb-section-icon"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><span class="sb-section-text">감성 파라미터</span></div>""", unsafe_allow_html=True)
    threshold = st.number_input("", min_value=40, max_value=95, value=55, step=5, label_visibility="collapsed")
    st.markdown('<span class="sb-hint">40~50% 민감 · 55~65% 권장 · 70%+ 엄격</span>', unsafe_allow_html=True)
    st.session_state["_cur_threshold"] = threshold

    st.markdown("""<div class="sb-section" style="margin:0.5rem 0 0.3rem;"><div class="sb-section-icon">⚙</div><span class="sb-section-text">파라미터 가이드</span></div>
    <div class="param-guide-box">
        <b>📌 AI 모델 가중치 구성</b><br>
        • Multilingual Sentiment: <code>× 1.5</code> (Very Negative: <code>× 1.8</code>)<br>
        • KLUE-RoBERTa: <code>× 1.0</code><br>
        • 룰베이스 키워드: <code>× 0.8</code>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1: run_btn  = st.button("▶ AI분석", use_container_width=True, key="run_btn")
    with btn_col2: stop_btn = st.button("⏹ 중지",  use_container_width=True, key="stop_btn")


# ============================================================
# 중지 처리
# ============================================================
if stop_btn:
    st.session_state["analysis_stopped"] = True
    st.warning("⏹ 분석이 중지되었습니다. 이전 결과는 아래에서 확인할 수 있습니다.")


# ============================================================
# 분석 실행
# ============================================================
if run_btn:
    st.session_state["analysis_stopped"] = False
    st.session_state["analysis_done"]    = False
    st.session_state["analysis_results"] = None
    st.session_state["dash_filter"]      = "전체"
    st.session_state["yt_api_error"]     = None

    keywords_raw = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()][:3]
    if not keywords_raw: st.error("검색어를 최소 1개 입력해주세요."); st.stop()
    if not any([search_blog, search_kin, search_cafe, search_yt]): st.error("채널을 하나 이상 선택해주세요."); st.stop()
    if start_date > end_date: st.error("시작일이 종료일보다 늦습니다."); st.stop()

    keywords = [build_naver_query(k) for k in keywords_raw]

    with st.spinner("AI 앙상블 모델 초기화 중..."):
        model_multi = load_multilingual()
        model_r     = load_roberta()

    model_failures = []
    if model_multi is None: model_failures.append("Multilingual Sentiment")
    if model_r     is None: model_failures.append("KLUE-RoBERTa")
    if len(model_failures) == 2: st.error("🚨 AI 모델 2개 모두 로드 실패 — 룰베이스만으로 판정합니다.")
    elif len(model_failures) == 1: st.warning(f"⚠ {model_failures[0]} 모델 로드 실패 — 나머지 + 룰베이스로 분석합니다.")
    else: st.markdown('<div style="background:#F0FDF4;border:1px solid #A7F3D0;border-radius:8px;padding:0.6rem 1rem;font-size:0.82rem;color:#16A34A;font-weight:600;margin-bottom:0.5rem;">✅ AI 앙상블 모델 정상 로드 완료</div>', unsafe_allow_html=True)

    collect_tasks = []
    for kw in keywords:
        if search_blog: collect_tasks.append(("blog", kw, "블로그"))
        if search_kin:  collect_tasks.append(("kin",  kw, "지식인"))
        if search_cafe: collect_tasks.append(("cafe", kw, "카페"))
        if search_yt and YOUTUBE_API_KEY: collect_tasks.append(("yt", kw, "유튜브"))

    prog = st.progress(0); prog_text = st.empty()
    all_items, collect_log = [], []

    def _fetch(task, count=display_count):
        tp, kw, label = task
        if tp == "blog": return label, kw, collect_naver_paged(kw, "blog", count)
        if tp == "kin":  return label, kw, collect_naver_paged(kw, "kin",  count)
        if tp == "cafe": return label, kw, collect_cafe_paged(kw, count)
        if tp == "yt":   return label, kw, search_youtube(kw, max_results=min(count,50))
        return label, kw, []

    total_tasks, done_tasks = len(collect_tasks), 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, t): t for t in collect_tasks}
        for fut in concurrent.futures.as_completed(futures):
            try: label, kw, items = fut.result()
            except Exception as e: label, kw, items = "오류","",[]
            all_items.extend(items); collect_log.append(f"{label}/{len(items)}건")
            done_tasks += 1
            prog.progress(done_tasks/max(total_tasks,1))
            prog_text.markdown(f'<span style="font-size:0.78rem;color:#718096;">수집 중 {done_tasks}/{total_tasks} 완료</span>', unsafe_allow_html=True)
    prog.empty(); prog_text.empty()

    if st.session_state.get("yt_api_error"):
        st.warning(f"📺 유튜브 수집 오류: {st.session_state['yt_api_error']}")
        st.session_state["yt_api_error"] = None

    seen, unique_items = set(), []
    for item in all_items:
        lnk = item.get("link","")
        if lnk not in seen: seen.add(lnk); unique_items.append(item)

    before_rel   = len(unique_items)
    unique_items = [it for it in unique_items if it.get("출처") in ("카페","지식인") or is_daiso_related(it)]
    rel_excluded = before_rel - len(unique_items)

    before_promo   = len(unique_items)
    unique_items   = [it for it in unique_items if not is_promotional(it)]
    promo_excluded = before_promo - len(unique_items)

    before_admin   = len(unique_items)
    unique_items   = [it for it in unique_items if not is_admin_excluded(it)]
    admin_excluded = before_admin - len(unique_items)

    before_usim  = len(unique_items)
    unique_items = [it for it in unique_items if not is_usim_related(it)]
    usim_excluded = before_usim - len(unique_items)

    filtered = filter_by_date(unique_items, start_date, end_date)
    if not filtered: st.warning("해당 기간에 결과가 없습니다."); st.stop()

    notes = []
    if rel_excluded   > 0: notes.append(f"다이소 무관 <strong>{rel_excluded}</strong>건 제외")
    if promo_excluded > 0: notes.append(f"홍보성 <strong>{promo_excluded}</strong>건 제외")
    if admin_excluded > 0: notes.append(f"관리자 제외 <strong>{admin_excluded}</strong>건 제외")
    if usim_excluded  > 0: notes.append(f"유심 관련 <strong>{usim_excluded}</strong>건 제외")
    note_str = (" &nbsp;·&nbsp; " + " &nbsp;·&nbsp; ".join(notes)) if notes else ""
    st.markdown(f"""<div class="card" style="border-left:3px solid #0066CC;">
        <span style="font-size:0.85rem;color:#0066CC;font-weight:600;">✅ 수집 완료 — 총 <strong>{len(filtered)}</strong>건{note_str}</span><br>
        <span style="font-size:0.72rem;color:#718096;">{' &nbsp;|&nbsp; '.join(collect_log)}</span>
    </div>""", unsafe_allow_html=True)

    results = []
    progress_bar = st.progress(0); status_text = st.empty()
    BATCH = 8; total_f = len(filtered)

    for batch_start in range(0, total_f, BATCH):
        if st.session_state.get("analysis_stopped"): break
        batch = filtered[batch_start: batch_start + BATCH]
        texts, metas = [], []
        for item in batch:
            src   = item.get("출처","")
            title = clean_text(item.get("title",""))
            desc  = clean_text(item.get("description",""))
            full  = title + " " + desc
            texts.append(full); metas.append((src, item, title))

        e_batch = model_multi(texts, batch_size=BATCH, truncation=True, max_length=512) if model_multi else [None]*len(texts)
        r_batch = model_r(texts, batch_size=BATCH, truncation=True, max_length=512)     if model_r     else [None]*len(texts)

        for idx, (full, (src, item, title)) in enumerate(zip(texts, metas)):
            votes = {"긍정":0.0,"부정":0.0,"중립":0.0}
            multi_neg_score = 0.0
            if e_batch[idx]:
                try:
                    for it in e_batch[idx]:
                        lbl = MULTI_LABEL_MAP.get(it["label"])
                        if lbl:
                            weight = 1.8 if it["label"] in MULTI_NEG_BOOST else 1.5
                            votes[lbl] += it["score"] * weight
                            if lbl == "부정": multi_neg_score += it["score"]
                except: pass
            if r_batch[idx]:
                try:
                    for it in r_batch[idx]:
                        lbl = ROBERTA_LABEL_MAP.get(it["label"])
                        if lbl: votes[lbl] += it["score"] * 1.0
                except: pass

            rule_lbl, rule_sc = rule_based(full)
            votes[rule_lbl] += rule_sc * 0.8
            total_v = sum(votes.values())
            if total_v == 0:
                sentiment, score = "중립", 50
            else:
                best  = max(votes, key=votes.get)
                score = round(votes[best] / total_v * 100)
                neg_kw_cnt = sum(1 for kw in get_neg_kw() if kw in full)
                if best == "부정" and not (multi_neg_score >= 0.35 or neg_kw_cnt >= 1):
                    best = "중립"; score = max(round(score*0.7), 45)
                sentiment = best

            if score < threshold and sentiment != "중립":
                sentiment = "중립"

            date_str  = item.get("날짜","") if src == "유튜브" else (lambda dt: dt.strftime("%Y-%m-%d") if dt else "")(parse_date(item))
            prod_code = extract_product_code(full) if src != "유튜브" else ""
            prod_name = match_product_name(prod_code)
            subcate   = match_subcategory_from_code(prod_code) or extract_subcategory(full)
            reason    = extract_reason_sentence(full, sentiment)

            results.append({
                "출처":src,"검색어":item.get("검색어",""),
                "소분류":subcate,"품번":prod_code,"품명":prod_name,
                "가격언급":extract_price(full) if src != "유튜브" else "",
                "title":title,"link":item.get("link",""),
                "날짜":date_str,"감성":sentiment,"확신도":score,
                "판단근거":reason,
                "channel":item.get("channel","") or item.get("cafename",""),
                "views":item.get("views",""),"likes":item.get("likes",""),
                "comments":item.get("comments",""),"video_id":item.get("video_id",""),
            })

        done_so_far = min(batch_start + BATCH, total_f)
        progress_bar.progress(done_so_far / total_f)
        status_text.markdown(f'<span style="font-size:0.78rem;color:#718096;">AI 분석 중 {done_so_far} / {total_f}</span>', unsafe_allow_html=True)

    progress_bar.empty(); status_text.empty()
    st.session_state["analysis_results"] = results
    st.session_state["analysis_done"]    = True
    st.session_state["_start_date"]      = start_date
    st.session_state["_end_date"]        = end_date
    st.rerun()


# ============================================================
# 채널 상세 탭 공통 함수
# ============================================================
def render_detail_tab(src_results: list, src_name: str, start_dt: date, end_dt: date, extra_sort: bool = False):
    if not src_results: st.info(f"{src_name} 수집 결과가 없습니다."); return
    t  = len(src_results)
    p  = sum(1 for r in src_results if r["감성"]=="긍정")
    n  = sum(1 for r in src_results if r["감성"]=="부정")
    ne = sum(1 for r in src_results if r["감성"]=="중립")
    c1,c2,c3,c4 = st.columns(4)
    for col, cls, lbl, val in [(c1,"total","전체",t),(c2,"pos","긍정",p),(c3,"neg","부정",n),(c4,"neu","중립",ne)]:
        with col: st.markdown(f'<div class="metric-card {cls}"><div class="metric-label"><span class="metric-icon {cls}">{lbl}</span>{lbl}</div><div class="metric-value">{val}</div><div class="metric-pct">{round(val/t*100) if t else 0}%</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    kw_stats = {}
    for r in src_results:
        kw = r.get("검색어","")
        kw_stats.setdefault(kw, {"긍정":0,"부정":0,"중립":0})
        kw_stats[kw][r["감성"]] += 1
    kw_rows = [{"검색어":kw,"긍정":s["긍정"],"부정":s["부정"],"중립":s["중립"],"합계":sum(s.values()),"부정률(%)":round(s["부정"]/sum(s.values())*100,1) if sum(s.values()) else 0} for kw,s in kw_stats.items()]
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("검색")} <span style="font-size:0.95rem;font-weight:600;">검색어별 분포</span></div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(kw_rows), use_container_width=True, hide_index=True, height=160)

    # ★ 정렬 기능 (코드4)
    sort_options = ["최신날짜순","부정 높은순","긍정 높은순"]
    if extra_sort: sort_options.append("조회수 높은순")
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.4rem;">{icon("↕")} <span style="font-size:0.95rem;font-weight:600;">정렬 기준</span></div>', unsafe_allow_html=True)
    sort_key = st.radio("정렬", sort_options, horizontal=True, key=f"sort_{src_name}", label_visibility="collapsed")
    sorted_data = sort_results(src_results, sort_key)

    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0.75rem 0 0.75rem;">{icon("목록")} <span style="font-size:0.95rem;font-weight:600;">상세 결과 ({len(sorted_data)}건)</span></div>', unsafe_allow_html=True)
    for idx, r in enumerate(sorted_data):
        render_result_card(r)
        render_label_buttons(r, f"{src_name}_{idx}")

    st.download_button(f"📥 {src_name} CSV 다운로드",
        pd.DataFrame(src_results).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        f"ISSUE_{src_name}_{start_dt}_{end_dt}.csv", "text/csv", use_container_width=True)


# ============================================================
# 결과 렌더링
# ============================================================
if st.session_state.get("analysis_done") and st.session_state.get("analysis_results"):
    results    = st.session_state["analysis_results"]
    start_date = st.session_state.get("_start_date", date.today())
    end_date   = st.session_state.get("_end_date",   date.today())

    total = len(results)
    pos   = sum(1 for r in results if r["감성"]=="긍정")
    neg   = sum(1 for r in results if r["감성"]=="부정")
    neu   = sum(1 for r in results if r["감성"]=="중립")

    all_subs = []
    for r in results:
        if r.get("소분류"): all_subs.extend([s.strip() for s in r["소분류"].split(",") if s.strip()])
    sub_cnt = Counter(all_subs)

    all_codes = []
    for r in results:
        if r.get("품번"):
            for c in r["품번"].split(","):
                c = c.strip()
                if c: all_codes.append(f"{c} {r.get('품명','')}".strip())
    code_cnt = Counter(all_codes)

    date_neg = {}
    for r in results:
        if r["감성"] == "부정" and r.get("날짜"):
            m = r["날짜"][:7]
            date_neg[m] = date_neg.get(m,0) + 1

    date_sent = {}
    for r in results:
        if r.get("날짜"):
            d = r["날짜"][:10]
            date_sent.setdefault(d, {"긍정":0,"부정":0,"중립":0})
            date_sent[d][r["감성"]] += 1

    tab_dash, tab_blog, tab_kin, tab_cafe, tab_yt = st.tabs(
        ["📊 대시보드","📝 블로그","💬 지식인","☕ 카페","▶ 유튜브"])

    with tab_dash:
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("↑")} <span style="font-size:0.95rem;font-weight:600;">분석 요약</span></div>', unsafe_allow_html=True)

        dash_filter    = st.session_state["dash_filter"]
        filter_options = [f"전체 ({total})",f"긍정 ({pos})",f"부정 ({neg})",f"중립 ({neu})"]
        filter_map     = {f"전체 ({total})":"전체",f"긍정 ({pos})":"긍정",f"부정 ({neg})":"부정",f"중립 ({neu})":"중립"}
        current_idx = 0
        for i, opt in enumerate(filter_options):
            if filter_map[opt] == dash_filter: current_idx = i; break
        selected_opt = st.radio("필터", filter_options, index=current_idx, horizontal=True, label_visibility="collapsed", key="dash_radio")
        st.session_state["dash_filter"] = filter_map[selected_opt]
        dash_filter = st.session_state["dash_filter"]

        c1,c2,c3,c4 = st.columns(4)
        for col, cls, lbl, val in [(c1,"total","전체",total),(c2,"pos","긍정",pos),(c3,"neg","부정",neg),(c4,"neu","중립",neu)]:
            with col:
                pct = round(val/total*100) if total else 0
                st.markdown(f'<div class="metric-card {cls}"><div class="metric-label"><span class="metric-icon {cls}">{lbl}</span>{lbl}</div><div class="metric-value">{val}</div><div class="metric-pct">{pct}%</div></div>', unsafe_allow_html=True)

        filtered_results = results if dash_filter == "전체" else [r for r in results if r["감성"] == dash_filter]
        st.markdown(f'<div style="font-size:0.78rem;color:#718096;margin:0.5rem 0;">현재 필터: <strong style="color:#0066CC;">{dash_filter}</strong> — {len(filtered_results)}건</div>', unsafe_allow_html=True)

        # 일자별 감성 추이
        if date_sent:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("📈")} <span style="font-size:0.95rem;font-weight:600;">일자별 감성 추이</span></div>', unsafe_allow_html=True)
            chart_rows = []
            for d, counts in date_sent.items():
                chart_rows.append({"날짜":d,"감성":"긍정","건수":counts["긍정"]})
                chart_rows.append({"날짜":d,"감성":"부정","건수":counts["부정"]})
            chart_df = pd.DataFrame(chart_rows).sort_values("날짜")
            color_scale = alt.Scale(domain=["긍정","부정"], range=["#16A34A","#DC2626"])
            chart = (alt.Chart(chart_df).mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X("날짜:O", axis=alt.Axis(title="",labelAngle=-45,labelFontSize=10)),
                    y=alt.Y("건수:Q", axis=alt.Axis(title="건수",titleFontSize=11)),
                    color=alt.Color("감성:N", scale=color_scale, legend=alt.Legend(title="감성")),
                    tooltip=[alt.Tooltip("날짜:O"),alt.Tooltip("감성:N"),alt.Tooltip("건수:Q")]
                ).properties(height=250)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=True,gridColor="#F0F0F0",domain=False))
            st.altair_chart(chart, use_container_width=True)

        filt_subs = []
        for r in filtered_results:
            if r.get("소분류"): filt_subs.extend([s.strip() for s in r["소분류"].split(",") if s.strip()])
        filt_sub_cnt = Counter(filt_subs)
        filt_codes = []
        for r in filtered_results:
            if r.get("품번"):
                for c in r["품번"].split(","):
                    c = c.strip()
                    if c: filt_codes.append(f"{c} {r.get('품명','')}".strip())
        filt_code_cnt = Counter(filt_codes)

        col_top1, col_top2 = st.columns(2)
        with col_top1:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("분류")} <span style="font-size:0.95rem;font-weight:600;">소분류 TOP 10</span></div>', unsafe_allow_html=True)
            html = "".join([f'<div class="top-item"><div class="top-rank {"r1" if rank==1 else ""}">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>' for rank,(name,count) in enumerate(filt_sub_cnt.most_common(10),1)])
            st.markdown(f'<div class="card">{html or "<span style=\'color:#718096;font-size:0.82rem;\'>소분류 데이터 없음</span>"}</div>', unsafe_allow_html=True)
        with col_top2:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("품번")} <span style="font-size:0.95rem;font-weight:600;">주요 품번+품명 TOP 10</span></div>', unsafe_allow_html=True)
            html2 = "".join([f'<div class="top-item"><div class="top-rank {"r1" if rank==1 else ""}">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>' for rank,(name,count) in enumerate(filt_code_cnt.most_common(10),1)])
            st.markdown(f'<div class="card">{html2 or "<span style=\'color:#718096;font-size:0.82rem;\'>품번 데이터 없음</span>"}</div>', unsafe_allow_html=True)

        # 글 목록
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("📋")} <span style="font-size:0.95rem;font-weight:600;">{dash_filter} 글 목록</span></div>', unsafe_allow_html=True)

        # ★ 정렬 (코드4)
        dash_sort = st.radio("정렬", ["최신날짜순","부정 높은순","긍정 높은순"], horizontal=True, key="dash_sort", label_visibility="collapsed")
        sorted_filtered = sort_results(filtered_results, dash_sort)

        if sorted_filtered:
            for idx, r in enumerate(sorted_filtered[:30]):
                item_key = r.get("link", str(idx))
                if item_key in st.session_state.get("excluded_items",{}): continue
                render_result_card(r)
                render_label_buttons(r, f"dash_{idx}")

                if st.session_state["admin_mode"]:
                    with st.expander(f"🛡 관리자: 이 글 제외하기 (#{idx+1})", expanded=False):
                        excl_col1, excl_col2 = st.columns([3,1])
                        with excl_col1:
                            reason_input = st.text_input("제외 사유", key=f"exclude_reason_{idx}", placeholder="예: 무관한 글 · 스팸 · 홍보성")
                        with excl_col2:
                            st.markdown("<div style='margin-top:1.6rem'></div>", unsafe_allow_html=True)
                            if st.button("제외 확정", key=f"exclude_btn_{idx}", use_container_width=True):
                                if reason_input.strip():
                                    st.session_state["admin_excluded_urls"][item_key] = reason_input.strip()
                                    save_excluded_url_to_sheet(item_key, reason_input.strip())
                                    st.session_state["admin_retrain_log"].append({"시각":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"내용":f"[URL제외] '{r.get('title','')[:40]}' — 사유: {reason_input.strip()}"})
                                    st.session_state["analysis_results"] = [x for x in st.session_state["analysis_results"] if x.get("link","") != item_key]
                                    st.success("✅ 제외 완료"); st.rerun()
                                else: st.warning("제외 사유를 입력해주세요.")
        else:
            st.info(f"'{dash_filter}'으로 분류된 글이 없습니다.")

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("↓")} <span style="font-size:0.95rem;font-weight:600;">결과 다운로드</span></div>', unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        with dl1:
            buf = create_excel(results, start_date, end_date)
            st.download_button("📥 EXCEL 다운로드", buf, f"ISSUE_{start_date}_{end_date}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with dl2:
            csv_data = pd.DataFrame(results).to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSV 다운로드", csv_data.encode("utf-8-sig"), f"ISSUE_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

    with tab_blog:
        render_detail_tab([r for r in results if r["출처"]=="블로그"], "블로그", start_date, end_date)
    with tab_kin:
        render_detail_tab([r for r in results if r["출처"]=="지식인"], "지식인", start_date, end_date)
    with tab_cafe:
        render_detail_tab([r for r in results if r["출처"]=="카페"], "카페", start_date, end_date)

    with tab_yt:
        yt_results = [r for r in results if r["출처"]=="유튜브"]
        if not yt_results:
            if not YOUTUBE_API_KEY: st.warning("YOUTUBE_API_KEY가 secrets에 없습니다.")
            else: st.info("유튜브 수집 결과가 없습니다.")
        else:
            render_detail_tab(yt_results, "유튜브", start_date, end_date, extra_sort=True)
            st.markdown("""<div style="margin-top:1.5rem;padding:1.25rem 1.5rem;background:#F8FAFC;border:1.5px dashed #CBD5E1;border-radius:10px;text-align:center;">
                <div style="font-size:0.9rem;font-weight:600;color:#64748B;margin-bottom:0.3rem;">💬 유튜브 댓글 감성분석</div>
                <div class="badge-coming" style="display:inline-flex;">추가 예정 기능입니다</div>
                <div style="font-size:0.75rem;color:#94A3B8;margin-top:0.5rem;">다음 버전에서 제공될 예정입니다</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("""<div style="text-align:center;padding:2rem 0 1rem;border-top:1px solid #E2E8F0;margin-top:2rem;">
        <span style="font-size:0.75rem;color:#A0AEC0;">DAISO SNS Issue Finder · Multilingual Sentiment × KLUE-RoBERTa Ensemble · Created by 데이터분석팀</span>
    </div>""", unsafe_allow_html=True)
