import streamlit as st
import requests
import openpyxl
import re
import io
import gspread
import pandas as pd
import altair as alt
import concurrent.futures
from datetime import datetime, date
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
[data-testid="stSidebar"] [data-testid="stDateInput"] input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.12) !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] {
    margin-top: 0 !important; margin-bottom: 0 !important;
    padding-top: 0 !important; padding-bottom: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] > label { display: none !important; }

.date-label {
    font-size: 0.7rem; color: #718096; margin-bottom: 1px;
    margin-top: 0; display: block; line-height: 1.1;
}

[data-testid="stSidebar"] [data-testid="column"] {
    gap: 0 !important; padding-top: 0 !important; padding-bottom: 0 !important;
    min-width: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    gap: 0.3rem !important;
}

.app-header {
    background: var(--bg-white); border-bottom: 1px solid var(--border);
    padding: 1.25rem 2rem; display: flex; align-items: center; gap: 0.75rem;
    margin-bottom: 1.5rem; border-radius: 12px; box-shadow: var(--shadow);
    position: relative;
}
.header-icon {
    width: 40px; height: 40px; background: var(--primary); border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; color: #FFFFFF !important; flex-shrink: 0;
}
.header-title { font-size: 1.25rem; font-weight: 700; color: var(--text); letter-spacing: -0.01em; }
.header-sub { font-size: 0.78rem; color: var(--text3); margin-top: 0.1rem; }

.card {
    background: var(--bg-white); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.25rem 1.5rem; box-shadow: var(--shadow); margin-bottom: 1rem;
}

.metric-card {
    flex: 1; background: var(--bg-white); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.25rem 1.5rem; box-shadow: var(--shadow);
    border-top: 3px solid transparent;
}
.metric-card.total { border-top-color: var(--primary); }
.metric-card.pos   { border-top-color: var(--pos); }
.metric-card.neg   { border-top-color: var(--neg); }
.metric-card.neu   { border-top-color: var(--neu); }

.metric-label {
    font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--text3); margin-bottom: 0.5rem;
    display: flex; align-items: center; gap: 0.5rem;
}
.metric-icon {
    width: 22px; height: 22px; background: var(--primary); border-radius: 6px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #FFFFFF !important; font-size: 0.68rem; font-weight: 700;
    flex-shrink: 0; line-height: 1;
}
.metric-icon.pos { background: var(--pos); color: #FFFFFF !important; }
.metric-icon.neg { background: var(--neg); color: #FFFFFF !important; }
.metric-icon.neu { background: var(--neu); color: #FFFFFF !important; }
.metric-value { font-family: 'Inter', sans-serif; font-size: 2.2rem; font-weight: 600; color: var(--text); line-height: 1; }
.metric-pct { font-size: 0.78rem; color: var(--text3); margin-top: 0.3rem; }

.section-title-icon {
    width: 24px; height: 24px; background: var(--primary); border-radius: 6px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #FFFFFF !important; font-size: 0.75rem; font-weight: 700;
    flex-shrink: 0; vertical-align: middle;
}

.badge-pos { background: var(--pos-bg); color: var(--pos); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neg { background: var(--neg-bg); color: var(--neg); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neu { background: var(--neu-bg); color: var(--neu); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }

.top-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border); }
.top-item:last-child { border-bottom: none; }
.top-rank {
    width: 26px; height: 26px; background: var(--primary-lt); border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.72rem; font-weight: 700; color: var(--primary); flex-shrink: 0;
}
.top-rank.r1 { background: var(--primary); color: #FFFFFF !important; }
.top-name { flex: 1; font-size: 0.85rem; color: var(--text); }
.top-count { font-size: 0.78rem; font-weight: 600; color: var(--primary); background: var(--primary-lt); padding: 2px 8px; border-radius: 20px; }

.result-card {
    background: var(--bg-white); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.25rem; margin-bottom: 0.5rem; box-shadow: var(--shadow); transition: box-shadow 0.2s;
}
.result-card:hover { box-shadow: var(--shadow-md); }
.result-title { font-size: 0.9rem; font-weight: 500; color: var(--text); margin-bottom: 0.4rem; }
.result-meta { font-size: 0.75rem; color: var(--text3); display: flex; gap: 0.75rem; flex-wrap: wrap; }
.result-meta span { display: flex; align-items: center; gap: 0.2rem; }

/* ─── 대시보드 필터 버튼 ─── */
.filter-btn-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.filter-btn {
    padding: 0.45rem 1.1rem; border-radius: 20px; border: 1.5px solid var(--border2);
    background: var(--bg-white); color: var(--text2); font-size: 0.82rem; font-weight: 600;
    cursor: pointer; transition: all 0.18s; font-family: 'Noto Sans KR', sans-serif;
}
.filter-btn:hover { border-color: var(--primary); color: var(--primary); background: var(--primary-lt); }
.filter-btn.active-total { background: var(--primary); color: #fff; border-color: var(--primary); }
.filter-btn.active-pos   { background: var(--pos);     color: #fff; border-color: var(--pos); }
.filter-btn.active-neg   { background: var(--neg);     color: #fff; border-color: var(--neg); }
.filter-btn.active-neu   { background: var(--neu);     color: #fff; border-color: var(--neu); }

.login-wrap {
    max-width: 380px; margin: 5rem auto; background: var(--bg-white);
    border: 1px solid var(--border); border-radius: 16px; padding: 2.5rem 2rem;
    text-align: center; box-shadow: var(--shadow-md);
}
.login-icon {
    width: 52px; height: 52px; background: var(--primary); border-radius: 14px;
    margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; color: #FFFFFF !important;
}
.login-title { font-size: 1.3rem; font-weight: 700; color: var(--text); margin-bottom: 0.25rem; }
.login-sub { font-size: 0.82rem; color: var(--text3); margin-bottom: 1.5rem; }

.sb-section {
    display: flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.7rem;
    background: var(--primary-lt); border-left: 3px solid var(--primary);
    border-radius: 0 6px 6px 0; margin: 1rem 0 0.5rem;
}
.sb-section-icon {
    width: 20px; height: 20px; background: var(--primary); border-radius: 5px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #FFFFFF !important; font-size: 0.62rem; font-weight: 700; flex-shrink: 0;
}
.sb-section-text { font-size: 0.72rem; font-weight: 700; color: var(--primary) !important; text-transform: uppercase; letter-spacing: 0.07em; }
.sb-hint { font-size: 0.68rem; color: var(--text3); margin-top: 0.15rem; display: block; line-height: 1.5; }

.ch-row { display: flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0; min-height: 32px; }
.ch-icon { width: 20px; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 0.55rem; color: #FFFFFF !important; font-weight: 900; flex-shrink: 0; }
.ch-naver   { background: #03C75A; }
.ch-youtube { background: #FF0000; }
.ch-label   { font-size: 0.82rem; font-weight: 500; color: var(--text) !important; line-height: 1; }

[data-testid="stNumberInput"] > div { border-radius: 8px !important; }
[data-testid="stNumberInput"] button { color: var(--primary) !important; }

/* ── 기본 버튼 (메인 영역) ── */
.stButton > button {
    background: var(--primary) !important; color: #FFFFFF !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important; font-weight: 600 !important;
    padding: 0.6rem 1.25rem !important; transition: all 0.2s !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover { background: #0052A3 !important; box-shadow: 0 4px 12px rgba(0,102,204,0.3) !important; }

/* ── 사이드바 run_btn = 노란색 (key="run_btn" 타겟) ── */
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] .stButton:has(button[data-testid*="run"]) > button,
button[data-testid="run_btn"] {
    background: #FFD600 !important; color: #1A202C !important;
}

/* 사이드바 모든 버튼 기본 → 노란색, 중지만 파란색으로 override */
[data-testid="stSidebar"] .stButton > button {
    background: #FFD600 !important;
    color: #1A202C !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(255,214,0,0.35) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #F5C800 !important;
    box-shadow: 0 4px 14px rgba(255,214,0,0.5) !important;
    color: #1A202C !important;
}

/* 중지 버튼 (key="stop_btn") — 파란색 */
[data-testid="stSidebar"] [data-testid="stop_btn"] > button,
[data-testid="stSidebar"] .stButton:last-of-type > button {
    background: #0066CC !important; color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(0,102,204,0.35) !important;
}
[data-testid="stSidebar"] .stButton:last-of-type > button:hover {
    background: #0052A3 !important;
    box-shadow: 0 4px 14px rgba(0,102,204,0.5) !important;
    color: #FFFFFF !important;
}

.stDownloadButton > button {
    background: var(--bg-white) !important; color: var(--primary) !important;
    border: 1.5px solid var(--primary) !important; border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important; font-weight: 500 !important; width: 100% !important;
}
.stDownloadButton > button:hover { background: var(--primary-lt) !important; }

.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 2px solid var(--border) !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Noto Sans KR', sans-serif !important; font-size: 0.85rem !important;
    font-weight: 500 !important; color: var(--text3) !important; background: transparent !important;
    border: none !important; border-bottom: 2px solid transparent !important;
    padding: 0.6rem 1.2rem !important; border-radius: 0 !important; margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] { color: var(--primary) !important; border-bottom-color: var(--primary) !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem !important; }

.stProgress > div > div > div > div { background: var(--primary) !important; border-radius: 4px !important; }
.stProgress > div > div > div { background: var(--border) !important; border-radius: 4px !important; height: 6px !important; }
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; }
.stAlert { border-radius: 8px !important; }
hr { border: none; border-top: 1px solid var(--border) !important; margin: 1rem 0 !important; }
#MainMenu, footer, header { visibility: hidden; }

.badge-coming {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #F1F5F9; color: #64748B; border: 1px dashed #CBD5E1;
    padding: 0.35rem 0.75rem; border-radius: 6px; font-size: 0.78rem; font-weight: 500;
}

[data-testid="stSidebar"] .stCheckbox {
    display: flex !important; align-items: center !important; margin: 0 !important; padding: 0 !important; min-height: unset !important;
}
[data-testid="stSidebar"] .stCheckbox label { padding: 0 !important; min-height: unset !important; gap: 0 !important; }

.param-guide-box {
    background: #F0F7FF; border: 1.5px solid #B3D1F5; border-radius: 10px;
    padding: 0.9rem 1rem; margin: 0.5rem 0 1rem; font-size: 0.78rem;
    color: #1A202C; line-height: 1.7;
}
.param-guide-box b { color: #0066CC; }
.param-guide-box code { background: #E8F1FB; color: #0052A3; border-radius: 4px; padding: 1px 5px; font-size: 0.74rem; font-family: monospace; }

/* ==============================
   관리자 모드 스타일
   ============================== */
.admin-badge-on {
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: var(--admin); color: #FFFFFF;
    padding: 0.3rem 0.75rem; border-radius: 20px;
    font-size: 0.72rem; font-weight: 700;
    box-shadow: 0 2px 8px rgba(124,58,237,0.35);
    letter-spacing: 0.04em;
}

.admin-panel {
    background: var(--bg-white);
    border: 2px solid var(--admin);
    border-radius: 14px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(124,58,237,0.12);
}
.admin-panel-title {
    display: flex; align-items: center; gap: 0.6rem;
    font-size: 1rem; font-weight: 700; color: var(--admin);
    margin-bottom: 1rem; padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--admin-md);
}
.admin-panel-icon {
    width: 28px; height: 28px; background: var(--admin); border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    color: #FFFFFF !important; font-size: 0.8rem; flex-shrink: 0;
}

.admin-kw-tag {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--admin-lt); color: var(--admin);
    border: 1px solid var(--admin-md); border-radius: 20px;
    padding: 0.25rem 0.65rem; font-size: 0.76rem; font-weight: 600;
    margin: 0.2rem;
}

.admin-section {
    background: var(--admin-lt); border: 1px solid var(--admin-md);
    border-left: 3px solid var(--admin); border-radius: 0 8px 8px 0;
    padding: 0.6rem 0.9rem; margin: 0.75rem 0 0.5rem;
    font-size: 0.75rem; font-weight: 700; color: var(--admin);
    text-transform: uppercase; letter-spacing: 0.07em;
}

.admin-stat-box {
    background: linear-gradient(135deg, var(--admin-lt), #EDE9FE);
    border: 1px solid var(--admin-md); border-radius: 10px;
    padding: 0.9rem 1.2rem; text-align: center;
}
.admin-stat-num {
    font-size: 1.8rem; font-weight: 700; color: var(--admin);
    font-family: 'Inter', sans-serif; line-height: 1;
}
.admin-stat-label { font-size: 0.72rem; color: var(--text3); margin-top: 0.25rem; }

.admin-login-modal {
    max-width: 340px; margin: 3rem auto;
    background: var(--bg-white);
    border: 2px solid var(--admin);
    border-radius: 16px; padding: 2rem 1.75rem;
    text-align: center; box-shadow: 0 8px 32px rgba(124,58,237,0.18);
}
.admin-login-icon {
    width: 52px; height: 52px; background: var(--admin); border-radius: 14px;
    margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; color: #FFFFFF !important;
}

.relearn-badge {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #ECFDF5; color: #059669;
    border: 1px solid #A7F3D0; border-radius: 6px;
    padding: 0.3rem 0.65rem; font-size: 0.72rem; font-weight: 600;
}

.admin-panel .stTextInput input,
.admin-panel .stTextArea textarea {
    border: 1.5px solid var(--admin-md) !important;
    border-radius: 8px !important;
}
.admin-panel .stTextInput input:focus,
.admin-panel .stTextArea textarea:focus {
    border-color: var(--admin) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}

/* 관리자 버튼 보라색 override */
.admin-panel .stButton > button,
.admin-btn > button {
    background: var(--admin) !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.25) !important;
}
.admin-panel .stButton > button:hover {
    background: #6D28D9 !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# ① 일반 사용자 비밀번호 인증
# ============================================================
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="login-wrap">
        <div class="login-icon">🔵</div>
        <div class="login-title">DAISO SNS ISSUE FINDER</div>
        <div class="login-sub">다이소 SNS 상품불량 수집 AI시스템</div>
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
# ② 세션 초기화 (전체)
# ============================================================
_defaults = {
    "admin_mode":           False,
    "admin_show_login":     False,
    "admin_exclude_kws":    [],
    "admin_retrain_log":    [],
    "admin_excluded_urls":  {},
    "analysis_results":     None,   # ★ 분석 결과 저장
    "analysis_done":        False,  # ★ 분석 완료 여부
    "dash_filter":          "전체", # ★ 대시보드 필터
    "analysis_stopped":     False,
    "exclude_title_kw_list": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# ADMIN_PASSWORD — secrets 미설정 시 앱 강제 중단
# ============================================================
if "ADMIN_PASSWORD" not in st.secrets:
    st.error("🚨 보안 오류: secrets에 ADMIN_PASSWORD가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# ============================================================
# API키
# ============================================================
NAVER_CLIENT_ID     = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
YOUTUBE_API_KEY     = st.secrets.get("YOUTUBE_API_KEY", "")

# ============================================================
# 구글시트 불러오기 (품번,품명,소분류)
# ============================================================
@st.cache_data(ttl=3600)
def load_product_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        gc  = gspread.authorize(creds)
        sh  = gc.open_by_url(st.secrets["GSHEET_URL"])
        df  = pd.DataFrame(sh.sheet1.get_all_records())
        df.columns = [c.strip() for c in df.columns]
        if "품번" in df.columns:
            df["품번"] = df["품번"].astype(str).str.strip()
        return df
    except Exception as e:
        st.warning(f"⚠ 품명 DB 로드 실패: {e}")
        return pd.DataFrame(columns=["품번", "품명", "소분류"])

PRODUCT_DB = load_product_db()
VALID_PRODUCT_CODES = set()
if not PRODUCT_DB.empty and "품번" in PRODUCT_DB.columns:
    VALID_PRODUCT_CODES = set(PRODUCT_DB["품번"].dropna().astype(str).str.strip().tolist())

def load_subcategories():
    if not PRODUCT_DB.empty and "소분류" in PRODUCT_DB.columns:
        return list(PRODUCT_DB["소분류"].dropna().unique())
    return []

SUBCATEGORIES = load_subcategories()


# ============================================================
# AI모델링 (앙상블)
# ============================================================
@st.cache_resource
def load_multilingual():
    try:
        return pipeline("text-classification", model="tabularisai/multilingual-sentiment-analysis",
                         truncation=True, max_length=512, top_k=None, device=-1)
    except Exception:
        return None

@st.cache_resource
def load_roberta():
    try:
        return pipeline("text-classification", model="Chamsol/klue-roberta-sentiment-classification",
                         truncation=True, max_length=512, top_k=None, device=-1)
    except Exception:
        return None


# ============================================================
# 텍스트 전처리
# ============================================================
def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[#\w]+;', ' ', text)
    return text.strip()


# ============================================================
# 룰베이스 키워드
# ============================================================
BASE_NEGATIVE_KW = [
    "불만","짜증","별로","최악","실망","환불","불량","교환","이상해","형편없",
    "쓰레기","구려","나빠","고장","터졌","망가","깨졌","불편","아쉬워","위험",
    "조심","주의","문제","하자","뜯겨","냄새","오염","불결","지저분","더럽",
    "싸구려","허접","대충","클레임","AS","환급","반품","재구매 안","비추",
    "별점 1","별점1","1점","속았","낚였","사기","뻥","가짜","품질 나쁜",
    "품질이 나쁜","뚜껑이 안","뚜껑이 깨","잘 안 돼","안 되는","못 쓰겠",
    "못써","쓸모없어","수량적음","색이다름","색상상이","성능과장","원산지 불명확",
    "색감차이","과포장","과점착","색번짐","이염","후회","별로야","별로네",
    "글쎄","그냥저냥","생각보다 별로","기대 이하","실패","구매실패","돈낭비",
    "돈 낭비","비싸","불합리","사지마","사지 마","추천안","추천 안","별1",
    "1개","뒤틀","휘어","금방망가","금방 망가","오래못가","오래 못가",
    "금방부서","금방 부서",
]

BASE_POSITIVE_KW = [
    "좋아요","좋았","만족","추천","재구매","최고","훌륭","완벽","편리","예뻐",
    "가성비","합리적","대박","꿀템","강추","마음에 들","만족스럽","굿","짱",
    "갓성비","득템","완전좋","완전 좋","행복","사랑","최애","예쁘다","예쁜",
]

BASE_PROMO_KW = [
    "다이소 매장", "다이소 오픈", "다이소 신상", "다이소 신제품", "다이소 근처",
    "다이소 위치", "다이소 영업시간", "다이소 매장 위치", "다이소 점포",
    "다이소 방문", "다이소 주차", "다이소에서 구입", "다이소 쇼핑",
    "홍보", "광고", "제품을 받았습니다", "제공받아", "협찬", "무료로 받",
    "내돈내산 아닌", "리뷰어", "체험단", "서포터즈", "내돈내산아님",
    "다이소 하울", "다이소 추천템", "다이소 인기템", "다이소 꿀템 추천",
    "다이소 추천 아이템", "다이소 베스트", "다이소 신상품 추천",
]

if "neg_kw_list"   not in st.session_state: st.session_state["neg_kw_list"]   = list(BASE_NEGATIVE_KW)
if "pos_kw_list"   not in st.session_state: st.session_state["pos_kw_list"]   = list(BASE_POSITIVE_KW)
if "promo_kw_list" not in st.session_state: st.session_state["promo_kw_list"] = list(BASE_PROMO_KW)

def get_neg_kw():   return st.session_state["neg_kw_list"]
def get_pos_kw():   return st.session_state["pos_kw_list"]
def get_promo_kw(): return st.session_state["promo_kw_list"]
def get_excl_kw():  return st.session_state["exclude_title_kw_list"]


# ============================================================
# 관리자 재학습 반영
# ============================================================
def admin_apply_keyword(kw_type: str, keyword: str, action: str = "add"):
    kw = keyword.strip()
    if not kw:
        return False, "키워드가 비어 있습니다."
    key_map = {
        "neg":     "neg_kw_list",
        "pos":     "pos_kw_list",
        "promo":   "promo_kw_list",
        "exclude": "exclude_title_kw_list",
    }
    label_map = {
        "neg": "부정 키워드", "pos": "긍정 키워드",
        "promo": "홍보 제외 키워드", "exclude": "제목 직접 제외 키워드",
    }
    key = key_map.get(kw_type)
    if not key:
        return False, "잘못된 키워드 유형입니다."
    lst = st.session_state[key]
    if action == "add":
        if kw in lst:
            return False, f"이미 등록된 키워드입니다: {kw}"
        lst.append(kw)
        log_msg = f"[추가] {label_map[kw_type]} → '{kw}'"
    else:
        if kw not in lst:
            return False, f"목록에 없는 키워드입니다: {kw}"
        lst.remove(kw)
        log_msg = f"[삭제] {label_map[kw_type]} → '{kw}'"
    st.session_state["admin_retrain_log"].append({
        "시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "내용": log_msg
    })
    return True, log_msg


# ============================================================
# 홍보성 글 판단 / 관리자 제외 / 유심 제외
# ============================================================
def is_promotional(item: dict) -> bool:
    title = clean_text(item.get("title", ""))
    desc  = clean_text(item.get("description", ""))
    full  = title + " " + desc
    promo_hit = sum(1 for kw in get_promo_kw() if kw in full)
    neg_hit   = sum(1 for kw in get_neg_kw()   if kw in full)
    return promo_hit >= 1 and neg_hit == 0

def is_admin_excluded(item: dict) -> bool:
    if item.get("link", "") in st.session_state.get("admin_excluded_urls", {}):
        return True
    title = clean_text(item.get("title", ""))
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
    "Very Negative": "부정", "Negative": "부정", "Neutral": "중립",
    "Positive": "긍정", "Very Positive": "긍정",
    "LABEL_0": "부정", "LABEL_1": "부정", "LABEL_2": "중립",
    "LABEL_3": "긍정", "LABEL_4": "긍정",
}
MULTI_NEG_BOOST = {"Very Negative", "LABEL_0"}

def rule_based(text: str):
    neg = sum(1 for kw in get_neg_kw() if kw in text)
    pos = sum(1 for kw in get_pos_kw() if kw in text)
    if neg > pos:  return "부정", min(0.65 + neg * 0.08, 0.98)
    if pos > neg:  return "긍정", min(0.60 + pos * 0.08, 0.98)
    return "중립", 0.50


# ============================================================
# 다이소 관련성 필터
# ============================================================
DAISO_VARIANTS = ["다이소", "DAISO", "daiso"]

def is_daiso_related(item: dict) -> bool:
    title = clean_text(item.get("title", ""))
    desc  = clean_text(item.get("description", ""))
    full  = (title + " " + desc).upper()
    return any(v.upper() in full for v in DAISO_VARIANTS)

def build_naver_query(raw_keyword: str) -> str:
    kw = raw_keyword.strip()
    has_daiso = any(v in kw for v in DAISO_VARIANTS)
    if not has_daiso:
        kw = "다이소 " + kw
    return kw


# ============================================================
# 네이버 / 카페 / 유튜브 수집
# ============================================================
def collect_naver_paged(query: str, search_type: str, total: int) -> list:
    all_items = []
    per_page  = 100
    start_idx = 1
    label = "블로그" if search_type == "blog" else "지식인"
    while len(all_items) < total:
        if start_idx > 1000: break
        remaining = total - len(all_items)
        fetch_cnt = min(per_page, remaining, 1000 - start_idx + 1)
        if fetch_cnt <= 0: break
        url     = f"https://openapi.naver.com/v1/search/{search_type}.json"
        headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
        params  = {"query": query, "display": fetch_cnt, "start": start_idx, "sort": "date"}
        try:
            resp  = requests.get(url, headers=headers, params=params, timeout=10)
            items = resp.json().get("items", [])
        except Exception: break
        if not items: break
        for item in items:
            item["출처"]   = label
            item["검색어"] = query
        all_items.extend(items)
        start_idx += fetch_cnt
        if len(items) < fetch_cnt: break
    return all_items[:total]

def collect_cafe_paged(query: str, total: int) -> list:
    all_items = []
    per_page  = 100
    start_idx = 1
    while len(all_items) < total:
        if start_idx > 1000: break
        remaining = total - len(all_items)
        fetch_cnt = min(per_page, remaining, 1000 - start_idx + 1)
        if fetch_cnt <= 0: break
        url     = "https://openapi.naver.com/v1/search/cafearticle.json"
        headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
        params  = {"query": query, "display": fetch_cnt, "start": start_idx, "sort": "date"}
        try:
            resp  = requests.get(url, headers=headers, params=params, timeout=10)
            items = resp.json().get("items", [])
        except Exception: break
        if not items: break
        for item in items:
            item["출처"]   = "카페"
            item["검색어"] = query
            item["channel"] = item.get("cafename", "")
        all_items.extend(items)
        start_idx += fetch_cnt
        if len(items) < fetch_cnt: break
    return all_items[:total]

def search_youtube(query: str, max_results: int = 30) -> list:
    if not YOUTUBE_API_KEY: return []
    try:
        resp = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "key": YOUTUBE_API_KEY, "q": query, "part": "snippet",
            "type": "video", "maxResults": min(max_results, 50),
            "order": "date", "relevanceLanguage": "ko", "regionCode": "KR"
        }, timeout=10)
        data = resp.json()
    except Exception: return []
    if "error" in data: return []
    items     = data.get("items", [])
    video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
    stats_map = {}
    if video_ids:
        try:
            for sv in requests.get("https://www.googleapis.com/youtube/v3/videos", params={
                "key": YOUTUBE_API_KEY, "id": ",".join(video_ids), "part": "statistics"
            }, timeout=10).json().get("items", []):
                stats_map[sv["id"]] = sv.get("statistics", {})
        except Exception: pass
    results = []
    for item in items:
        vid_id  = item.get("id", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        stats   = stats_map.get(vid_id, {})
        pub_raw = snippet.get("publishedAt", "")
        try:   pub_dt = datetime.strptime(pub_raw[:10], "%Y-%m-%d"); pub_str = pub_dt.strftime("%Y-%m-%d")
        except: pub_dt = None; pub_str = pub_raw[:10]
        results.append({
            "출처":"유튜브","검색어":query,"video_id":vid_id,
            "title":snippet.get("title",""),
            "description":snippet.get("description","")[:300],
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
# 날짜 파싱 & 필터
# ============================================================
def parse_date(item: dict):
    ds = item.get("postdate") or item.get("pubDate", "")
    if not ds: return None
    try:
        if len(ds) == 8: return datetime.strptime(ds, "%Y%m%d")
        return datetime.strptime(ds[:16], "%a, %d %b %Y")
    except: return None

def filter_by_date(items: list, start_dt: date, end_dt: date) -> list:
    s = datetime(start_dt.year, start_dt.month, start_dt.day)
    e = datetime(end_dt.year,   end_dt.month,   end_dt.day, 23, 59, 59)
    result = []
    for item in items:
        src = item.get("출처", "")
        dt  = item.get("pub_dt") if src == "유튜브" else parse_date(item)
        if dt is None: result.append(item)
        elif s <= dt <= e: result.append(item)
    return result


# ============================================================
# 품번/소분류 추출
# ============================================================
DATE_PATS = [
    r'\b20\d{6}\b', r'\b\d{4}[-./]\d{2}[-./]\d{2}\b',
    r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b',
    r'\b\d{4}년\s*\d{1,2}월', r'\b\d{1,2}월\s*\d{1,2}일',
]

def is_date_like(t):
    for p in DATE_PATS:
        if re.fullmatch(p, t.strip()): return True
    return bool(re.fullmatch(r'\d{6,8}', t.strip()))

def extract_product_code(text):
    raw_nums = re.findall(r'\b(\d{3,6})\b', text)
    codes = []
    for c in raw_nums:
        if is_date_like(c): continue
        if VALID_PRODUCT_CODES and c in VALID_PRODUCT_CODES: codes.append(c)
        elif not VALID_PRODUCT_CODES: codes.append(c)
    return ", ".join(dict.fromkeys(codes)) if codes else ""

def extract_price(text):
    prices = re.findall(r'\d{1,3}(?:,\d{3})*원', text)
    return ", ".join(dict.fromkeys(prices)) if prices else ""

SYNONYM_MAP = {
    "꽂이":"홀더","홀더":"꽂이","수납":"정리","정리":"수납",
    "바구니":"수납함","수납함":"바구니","케이스":"커버","커버":"케이스",
    "그릇":"용기","용기":"그릇","팬":"후라이팬","후라이팬":"팬",
    "집게":"클립","클립":"집게","수건":"타월","타월":"수건",
}

def extract_subcategory(text):
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

def match_product_name(code):
    if PRODUCT_DB.empty or not code: return ""
    for c in [c.strip() for c in code.split(",")]:
        row = PRODUCT_DB[PRODUCT_DB["품번"].astype(str).str.strip() == c]
        if not row.empty: return row.iloc[0]["품명"]
    return ""


# ============================================================
# 엑셀 생성
# ============================================================
def create_excel(data: list, start_dt: date, end_dt: date) -> io.BytesIO:
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "DAISO SNS ISSUE FINDER"
    headers = ["출처","검색어","소분류","품번","품명","가격언급","제목","링크","날짜","감성","확신도(%)","채널/카페명","조회수","좋아요","댓글수"]
    ws.append(headers)
    hf   = openpyxl.styles.Font(bold=True, color="0066CC", name="Malgun Gothic")
    hfil = openpyxl.styles.PatternFill(start_color="E8F1FB", end_color="E8F1FB", fill_type="solid")
    hbrd = openpyxl.styles.Border(bottom=openpyxl.styles.Side(style="thin", color="0066CC"))
    for c in range(1, len(headers)+1):
        cell = ws.cell(1, c); cell.font = hf; cell.fill = hfil; cell.border = hbrd
        cell.alignment = openpyxl.styles.Alignment(horizontal="center")
    col_bg  = {"긍정":"E8F5EE","부정":"FDEEEE","중립":"FFFBE8"}
    col_txt = {"긍정":"16A34A","부정":"DC2626","중립":"CA8A04"}
    for ri, row in enumerate(data, 2):
        ws.append([row.get(k,"") for k in ["출처","검색어","소분류","품번","품명","가격언급","title","link","날짜","감성","확신도","channel","views","likes","comments"]])
        s = row.get("감성","")
        if s in col_bg:
            ws.cell(ri,10).fill = openpyxl.styles.PatternFill(start_color=col_bg[s], end_color=col_bg[s], fill_type="solid")
            ws.cell(ri,10).font = openpyxl.styles.Font(color=col_txt[s], bold=True, name="Malgun Gothic")
    for letter, width in zip("ABCDEFGHIJKLMNO", [8,20,15,15,20,12,45,50,12,8,10,20,10,10,10]):
        ws.column_dimensions[letter].width = width
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf


# ============================================================
# 헬퍼
# ============================================================
SENT_BADGE = {"긍정":"badge-pos","부정":"badge-neg","중립":"badge-neu"}
def icon(label: str) -> str:
    return f'<span class="section-title-icon">{label}</span>'
def fmt_score(score) -> str:
    try: return f"{int(round(float(score)))}%"
    except: return f"{score}%"


# ============================================================
# ③ 관리자 버튼 (헤더 우측)
# ============================================================
admin_col1, admin_col2 = st.columns([10, 1])
with admin_col2:
    if st.session_state["admin_mode"]:
        if st.button("🔓 관리자", key="admin_toggle_btn", help="관리자 모드 ON — 클릭하여 로그아웃"):
            st.session_state["admin_mode"]       = False
            st.session_state["admin_show_login"] = False
            st.rerun()
        st.markdown('<span class="admin-badge-on">🔓 ADMIN</span>', unsafe_allow_html=True)
    else:
        if st.button("🔐 관리자", key="admin_toggle_btn", help="관리자 모드로 로그인"):
            st.session_state["admin_show_login"] = not st.session_state["admin_show_login"]
            st.rerun()

# 관리자 로그인 팝업
if st.session_state["admin_show_login"] and not st.session_state["admin_mode"]:
    with st.container():
        st.markdown("""
        <div class="admin-login-modal">
            <div class="admin-login-icon">🛡️</div>
            <div class="login-title" style="color:#7C3AED;">관리자 로그인</div>
            <div class="login-sub">관리자 전용 기능에 접근합니다</div>
        </div>
        """, unsafe_allow_html=True)
        _, mid_col, _ = st.columns([1, 2, 1])
        with mid_col:
            admin_pw = st.text_input("관리자 비밀번호", type="password",
                                     placeholder="비밀번호 입력",
                                     label_visibility="collapsed",
                                     key="admin_pw_input")
            login_col, cancel_col = st.columns(2)
            with login_col:
                if st.button("로그인", key="admin_login_confirm", use_container_width=True):
                    # ★ 버그수정: 따옴표 추가, secrets 또는 하드코딩 비밀번호 비교
                    if admin_pw == ADMIN_PASSWORD:
                        st.session_state["admin_mode"]       = True
                        st.session_state["admin_show_login"] = False
                        st.success("✅ 관리자 모드 활성화")
                        st.rerun()
                    else:
                        st.error("비밀번호가 틀렸습니다.")
            with cancel_col:
                if st.button("취소", key="admin_login_cancel", use_container_width=True):
                    st.session_state["admin_show_login"] = False
                    st.rerun()
    st.markdown("---")


# ============================================================
# ④ 관리자 패널
# ============================================================
if st.session_state["admin_mode"]:
    st.markdown("""
    <div class="admin-panel">
        <div class="admin-panel-title">
            <div class="admin-panel-icon">🛡</div>
            관리자 모드 — AI 재학습 키워드 관리
            <span class="admin-badge-on" style="margin-left:auto;">🔓 ADMIN ON</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    adm_tab1, adm_tab2, adm_tab3, adm_tab4 = st.tabs(
        ["➕ 키워드 추가", "🗑 키워드 삭제", "📋 현재 키워드 목록", "📜 재학습 로그"])

    with adm_tab1:
        st.markdown('<div class="admin-section">새 키워드 추가 → AI 분석에 즉시 반영</div>', unsafe_allow_html=True)
        ac1, ac2 = st.columns([2, 1])
        with ac1:
            new_kw_input = st.text_input("추가할 키워드", placeholder="예: 냄새나요  /  가성비 최고  /  다이소 쿠폰", key="admin_new_kw")
        with ac2:
            kw_type_sel = st.selectbox("키워드 유형", options=["neg", "pos", "promo", "exclude"],
                format_func=lambda x: {"neg":"🔴 부정 키워드","pos":"🟢 긍정 키워드","promo":"🟡 홍보 제외 키워드","exclude":"⛔ 제목 직접 제외"}[x],
                key="admin_kw_type")
        st.markdown("""
        <div class="param-guide-box">
            <b>🔴 부정 키워드</b> — 텍스트에 포함 시 부정 점수 가산 (룰베이스 × 0.8)<br>
            <b>🟢 긍정 키워드</b> — 텍스트에 포함 시 긍정 점수 가산<br>
            <b>🟡 홍보 제외</b> — 해당 키워드가 있고 부정어가 없으면 홍보성 글로 제외<br>
            <b>⛔ 제목 직접 제외</b> — 제목에 이 키워드가 포함되면 수집 결과에서 완전 제외
        </div>
        """, unsafe_allow_html=True)
        if st.button("✅ 키워드 추가 & AI 재학습 반영", key="admin_add_kw_btn", use_container_width=True):
            ok, msg = admin_apply_keyword(kw_type_sel, new_kw_input, "add")
            if ok:
                st.success(f"✅ {msg}")
                st.markdown('<span class="relearn-badge">🔄 AI 룰베이스 재학습 완료 — 다음 분석부터 적용됩니다</span>', unsafe_allow_html=True)
            else:
                st.warning(f"⚠ {msg}")

    with adm_tab2:
        st.markdown('<div class="admin-section">기존 키워드 삭제 → AI 분석에 즉시 반영</div>', unsafe_allow_html=True)
        del_type = st.selectbox("삭제할 키워드 유형", options=["neg", "pos", "promo", "exclude"],
            format_func=lambda x: {"neg":"🔴 부정 키워드","pos":"🟢 긍정 키워드","promo":"🟡 홍보 제외 키워드","exclude":"⛔ 제목 직접 제외"}[x],
            key="admin_del_kw_type")
        key_map_del = {"neg":"neg_kw_list","pos":"pos_kw_list","promo":"promo_kw_list","exclude":"exclude_title_kw_list"}
        kw_list_for_del = st.session_state[key_map_del[del_type]]
        if kw_list_for_del:
            del_target = st.selectbox("삭제할 키워드 선택", options=kw_list_for_del, key="admin_del_kw_target")
            if st.button("🗑 선택 키워드 삭제", key="admin_del_kw_btn", use_container_width=True):
                ok, msg = admin_apply_keyword(del_type, del_target, "remove")
                if ok:
                    st.success(f"✅ {msg}")
                    st.markdown('<span class="relearn-badge">🔄 AI 룰베이스 재학습 완료</span>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.warning(f"⚠ {msg}")
        else:
            st.info("해당 유형에 등록된 키워드가 없습니다.")

    with adm_tab3:
        st.markdown('<div class="admin-section">현재 등록된 키워드 전체 목록</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🔴 부정 키워드**")
            neg_tags = "".join([f'<span class="admin-kw-tag">{k}</span>' for k in get_neg_kw()])
            st.markdown(f'<div style="margin-bottom:1rem;">{neg_tags}</div>', unsafe_allow_html=True)
            st.markdown("**🟢 긍정 키워드**")
            pos_tags = "".join([f'<span class="admin-kw-tag" style="background:#F0FDF4;color:#16A34A;border-color:#A7F3D0;">{k}</span>' for k in get_pos_kw()])
            st.markdown(f'<div style="margin-bottom:1rem;">{pos_tags}</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown("**🟡 홍보 제외 키워드**")
            promo_tags = "".join([f'<span class="admin-kw-tag" style="background:#FEFCE8;color:#CA8A04;border-color:#FDE68A;">{k}</span>' for k in get_promo_kw()])
            st.markdown(f'<div style="margin-bottom:1rem;">{promo_tags}</div>', unsafe_allow_html=True)
            st.markdown("**⛔ 제목 직접 제외 키워드**")
            excl_tags = "".join([f'<span class="admin-kw-tag" style="background:#FEF2F2;color:#DC2626;border-color:#FCA5A5;">{k}</span>' for k in get_excl_kw()])
            st.markdown(f'<div>{excl_tags if excl_tags else "<span style=\'color:#718096;font-size:0.82rem;\'>없음</span>"}</div>', unsafe_allow_html=True)
        st.markdown("---")
        sc1, sc2, sc3, sc4 = st.columns(4)
        for col, label, count in [
            (sc1,"부정 키워드",len(get_neg_kw())),
            (sc2,"긍정 키워드",len(get_pos_kw())),
            (sc3,"홍보 제외",len(get_promo_kw())),
            (sc4,"직접 제외",len(get_excl_kw())),
        ]:
            with col:
                st.markdown(f'<div class="admin-stat-box"><div class="admin-stat-num">{count}</div><div class="admin-stat-label">{label}</div></div>', unsafe_allow_html=True)
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        if st.button("🔄 전체 키워드 기본값으로 초기화", key="admin_reset_kw"):
            st.session_state["neg_kw_list"]           = list(BASE_NEGATIVE_KW)
            st.session_state["pos_kw_list"]           = list(BASE_POSITIVE_KW)
            st.session_state["promo_kw_list"]         = list(BASE_PROMO_KW)
            st.session_state["exclude_title_kw_list"] = []
            st.session_state["admin_retrain_log"].append({"시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "내용": "[초기화] 전체 키워드를 기본값으로 리셋"})
            st.success("✅ 기본값으로 초기화 완료"); st.rerun()

    with adm_tab4:
        st.markdown('<div class="admin-section">AI 룰베이스 재학습 변경 이력</div>', unsafe_allow_html=True)
        log = st.session_state.get("admin_retrain_log", [])
        if log:
            log_df = pd.DataFrame(list(reversed(log)))
            st.dataframe(log_df, use_container_width=True, hide_index=True, height=300)
            st.download_button("📥 로그 CSV 다운로드", log_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "admin_retrain_log.csv", "text/csv")
        else:
            st.info("아직 재학습 이력이 없습니다.")

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
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;padding-bottom:1rem;border-bottom:1px solid #E2E8F0;margin-bottom:0.25rem;">
        <div style="width:32px;height:32px;background:#0066CC;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,102,204,0.3);">
            <span style="color:#FFFFFF;font-size:0.65rem;font-weight:900;letter-spacing:0.05em;font-family:'Inter',sans-serif;">D</span>
        </div>
        <div>
            <div style="font-weight:700;font-size:0.95rem;color:#1A202C;">DAISO ISSUE FINDER</div>
            <div style="font-size:0.68rem;color:#718096;">Created by 데이터분석팀</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 수집 채널 ──
    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.4rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/>
            </svg>
        </div>
        <span class="sb-section-text">CHANNEL</span>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        cb_col, icon_col = st.columns([1, 4])
        with cb_col:
            search_blog = st.checkbox("", value=True, key="cb_blog", label_visibility="collapsed")
        with icon_col:
            st.markdown('<div class="ch-row"><div class="ch-icon ch-naver">N</div><span class="ch-label">블로그</span></div>', unsafe_allow_html=True)

        cb_col2, icon_col2 = st.columns([1, 4])
        with cb_col2:
            search_cafe = st.checkbox("", value=True, key="cb_cafe", label_visibility="collapsed")
        with icon_col2:
            st.markdown('<div class="ch-row"><div class="ch-icon ch-naver">N</div><span class="ch-label">카페</span></div>', unsafe_allow_html=True)

    with col_right:
        cb_col3, icon_col3 = st.columns([1, 4])
        with cb_col3:
            search_kin = st.checkbox("", value=True, key="cb_kin", label_visibility="collapsed")
        with icon_col3:
            st.markdown('<div class="ch-row"><div class="ch-icon ch-naver">N</div><span class="ch-label">지식인</span></div>', unsafe_allow_html=True)

        cb_col4, icon_col4 = st.columns([1, 4])
        with cb_col4:
            search_yt = st.checkbox("", value=True, key="cb_yt", label_visibility="collapsed")
        with icon_col4:
            st.markdown("""<div class="ch-row"><div class="ch-icon ch-youtube"><svg width="9" height="9" viewBox="0 0 24 24" fill="#FFFFFF"><polygon points="5,3 19,12 5,21"/></svg></div><span class="ch-label">유튜브</span></div>""", unsafe_allow_html=True)

    # ── 검색어 ──
    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
        </div>
        <span class="sb-section-text">Searching Word</span>
    </div>
    """, unsafe_allow_html=True)

    keywords_input = st.text_area("", value="다이소 상품불량\n다이소 불량\n다이소 별로",
                                   height=80, label_visibility="collapsed",
                                   placeholder="줄바꿈으로 구분 · 최대 3개 (OR 조건)")
    st.markdown('<span class="sb-hint">줄바꿈으로 구분, 최대 3개 (OR 조건)<br>※ \'다이소\' 없으면 자동 추가됩니다</span>', unsafe_allow_html=True)

    # ── 수집 기간 ──
    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
        </div>
        <span class="sb-section-text">분석 기간</span>
    </div>
    """, unsafe_allow_html=True)

    dc1, dc2 = st.columns(2, gap="small")
    with dc1:
        st.markdown('<span class="date-label">시작일</span>', unsafe_allow_html=True)
        start_date = st.date_input("시작일", value=date(2026, 1, 1), label_visibility="collapsed", key="date_start")
    with dc2:
        st.markdown('<span class="date-label">종료일</span>', unsafe_allow_html=True)
        end_date = st.date_input("종료일", value=date.today(), label_visibility="collapsed", key="date_end")

    # ── 수집 개수 ──
    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
                <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
        </div>
        <span class="sb-section-text">분석개수</span>
    </div>
    """, unsafe_allow_html=True)

    display_count = st.number_input("", min_value=100, max_value=5000, value=100, step=100,
                                     label_visibility="collapsed",
                                     help="데이터 수집건수 (최소 100 ~ 최대 5,000, ±100)")
    st.markdown('<span class="sb-hint">데이터 수집건수 · 100 ~ 5,000 (±100)</span>', unsafe_allow_html=True)

    # ── 감성 파라미터 ──
    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
        </div>
        <span class="sb-section-text">감성 파라미터</span>
    </div>
    """, unsafe_allow_html=True)

    threshold = st.number_input("", min_value=40, max_value=95, value=55, step=5,
                                 label_visibility="collapsed",
                                 help="AI가 이 수치 이상의 확신도로 부정 판정 시에만 부정으로 등록")
    st.markdown('<span class="sb-hint">40~50% 민감 · 55~65% 권장 · 70%+ 엄격</span>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">⚙</div>
        <span class="sb-section-text">PARAMETER GUIDE</span>
    </div>
    <div class="param-guide-box">
        <b>📌 AI 모델 가중치 구성</b><br>
        • Multilingual Sentiment (tabularisai): <code>* 1.5</code> (Very Negative: <code>* 1.8</code>)<br>
        • KLUE-RoBERTa (Chamsol): <code>* 1.0</code><br>
        • 룰베이스 키워드: <code>* 0.8</code><br>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.6rem'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        run_btn = st.button("🔍 AI분석시작", use_container_width=True, key="run_btn")
    with btn_col2:
        stop_btn = st.button("⏹ 중지", use_container_width=True, key="stop_btn")


# ============================================================
# 중지 처리
# ============================================================
if stop_btn:
    st.session_state["analysis_stopped"] = True
    st.session_state["analysis_done"]    = False
    st.session_state["analysis_results"] = None
    st.warning("⏹ 분석이 중지되었습니다.")
    st.stop()


# ============================================================
# 분석 실행 (run_btn)
# ============================================================
if run_btn:
    st.session_state["analysis_stopped"] = False
    st.session_state["analysis_done"]    = False
    st.session_state["analysis_results"] = None
    st.session_state["dash_filter"]      = "전체"

    keywords_raw = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()][:3]
    if not keywords_raw:
        st.error("검색어를 최소 1개 입력해주세요."); st.stop()
    if not any([search_blog, search_kin, search_cafe, search_yt]):
        st.error("채널을 하나 이상 선택해주세요."); st.stop()
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦습니다."); st.stop()

    keywords = [build_naver_query(k) for k in keywords_raw]

    with st.spinner("AI 앙상블 모델 초기화 중... (Multilingual Sentiment + KLUE-RoBERTa)"):
        model_multi = load_multilingual()
        model_r     = load_roberta()

    # 수집 태스크 구성
    collect_tasks = []
    for kw in keywords:
        if search_blog: collect_tasks.append(("blog", kw, "블로그"))
        if search_kin:  collect_tasks.append(("kin",  kw, "지식인"))
        if search_cafe: collect_tasks.append(("cafe", kw, "카페"))
        if search_yt and YOUTUBE_API_KEY:
            collect_tasks.append(("yt",   kw, "유튜브"))

    prog      = st.progress(0)
    prog_text = st.empty()
    all_items = []; collect_log = []

    def _fetch(task):
        tp, kw, label = task
        if tp == "blog": return label, kw, collect_naver_paged(kw, "blog", display_count)
        if tp == "kin":  return label, kw, collect_naver_paged(kw, "kin",  display_count)
        if tp == "cafe": return label, kw, collect_cafe_paged(kw, display_count)
        if tp == "yt":   return label, kw, search_youtube(kw, max_results=min(display_count, 50))
        return label, kw, []

    total_tasks = len(collect_tasks)
    done_tasks  = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, t): t for t in collect_tasks}
        for fut in concurrent.futures.as_completed(futures):
            label, kw, items = fut.result()
            all_items.extend(items)
            collect_log.append(f"{label}/{kw}/{len(items)}건")
            done_tasks += 1
            prog.progress(done_tasks / max(total_tasks, 1))
            prog_text.markdown(f'<span style="font-size:0.78rem;color:#718096;">수집 중 {done_tasks}/{total_tasks} 완료</span>', unsafe_allow_html=True)
    prog.empty(); prog_text.empty()

    # 중복 제거
    seen, unique_items = set(), []
    for item in all_items:
        lnk = item.get("link","")
        if lnk not in seen: seen.add(lnk); unique_items.append(item)

    # 다이소 관련성 필터
    before_rel   = len(unique_items)
    unique_items = [it for it in unique_items if it.get("출처") in ("카페","지식인") or is_daiso_related(it)]
    rel_excluded = before_rel - len(unique_items)

    # 홍보성 글 제외
    before_promo   = len(unique_items)
    unique_items   = [it for it in unique_items if not is_promotional(it)]
    promo_excluded = before_promo - len(unique_items)

    # 관리자 제외
    before_admin   = len(unique_items)
    unique_items   = [it for it in unique_items if not is_admin_excluded(it)]
    admin_excluded = before_admin - len(unique_items)

    # 유심 관련 제외
    before_usim   = len(unique_items)
    unique_items  = [it for it in unique_items if not is_usim_related(it)]
    usim_excluded = before_usim - len(unique_items)

    # 날짜 필터
    filtered = filter_by_date(unique_items, start_date, end_date)
    if not filtered:
        st.warning("해당 기간에 결과가 없습니다. 날짜 범위나 검색어를 확인해주세요."); st.stop()

    # 수집 완료 안내
    notes = []
    if rel_excluded   > 0: notes.append(f"다이소 무관 <strong>{rel_excluded}</strong>건 제외")
    if promo_excluded > 0: notes.append(f"홍보성 글 <strong>{promo_excluded}</strong>건 제외")
    if admin_excluded > 0: notes.append(f"관리자 제외 <strong>{admin_excluded}</strong>건 제외")
    if usim_excluded  > 0: notes.append(f"유심 관련 <strong>{usim_excluded}</strong>건 제외")
    note_str = " &nbsp;·&nbsp; ".join(notes)
    if note_str: note_str = " &nbsp;·&nbsp; " + note_str

    st.markdown(f"""
    <div class="card" style="border-left:3px solid #0066CC;">
        <span style="font-size:0.85rem;color:#0066CC;font-weight:600;">
            ✅ 수집 완료 — 총 <strong>{len(filtered)}</strong>건 (중복 제거 후){note_str}
        </span><br>
        <span style="font-size:0.72rem;color:#718096;">{' &nbsp;|&nbsp; '.join(collect_log)}</span>
    </div>
    """, unsafe_allow_html=True)

    # AI 분석
    results      = []
    progress_bar = st.progress(0)
    status_text  = st.empty()
    BATCH        = 32
    total_f      = len(filtered)

    for batch_start in range(0, total_f, BATCH):
        batch = filtered[batch_start: batch_start + BATCH]
        texts, metas = [], []
        for item in batch:
            src   = item.get("출처","")
            title = clean_text(item.get("title",""))
            desc  = clean_text(item.get("description",""))
            full  = title + " " + desc
            texts.append(full)
            metas.append((src, item, title))

        e_batch = model_multi(texts, batch_size=BATCH, truncation=True, max_length=512) if model_multi else [None]*len(texts)
        r_batch = model_r(texts, batch_size=BATCH, truncation=True, max_length=512) if model_r else [None]*len(texts)

        for idx, (full, (src, item, title)) in enumerate(zip(texts, metas)):
            votes = {"긍정": 0.0, "부정": 0.0, "중립": 0.0}
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
                    best = "중립"; score = max(round(score * 0.7), 45)
                sentiment = best

            if score < threshold and sentiment != "중립":
                sentiment = "중립"

            date_str  = item.get("날짜","") if src == "유튜브" else (lambda dt: dt.strftime("%Y-%m-%d") if dt else "")(parse_date(item))
            prod_code = extract_product_code(full) if src != "유튜브" else ""
            prod_name = match_product_name(prod_code)

            results.append({
                "출처":    src, "검색어": item.get("검색어",""),
                "소분류":  extract_subcategory(full),
                "품번":    prod_code, "품명": prod_name,
                "가격언급":extract_price(full) if src != "유튜브" else "",
                "title":  title, "link": item.get("link",""),
                "날짜":   date_str, "감성": sentiment,
                "확신도": score,
                "channel":item.get("channel","") or item.get("cafename",""),
                "views":  item.get("views",""), "likes": item.get("likes",""),
                "comments":item.get("comments",""), "video_id":item.get("video_id",""),
            })

        done_so_far = min(batch_start + BATCH, total_f)
        progress_bar.progress(done_so_far / total_f)
        status_text.markdown(f'<span style="font-size:0.78rem;color:#718096;">AI 분석 중 {done_so_far} / {total_f}</span>', unsafe_allow_html=True)

    progress_bar.empty(); status_text.empty()

    # ★ 분석 결과를 session_state에 저장
    st.session_state["analysis_results"] = results
    st.session_state["analysis_done"]    = True
    st.session_state["_start_date"]      = start_date
    st.session_state["_end_date"]        = end_date
    st.rerun()  # 깔끔하게 재렌더


# ============================================================
# 결과 렌더링 (분석 완료된 경우)
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
                if c: all_codes.append(f"{c} {r.get('품명','') }".strip())
    code_cnt = Counter(all_codes)

    date_sent = {}
    for r in results:
        if r.get("날짜"):
            d = r["날짜"][:10]
            date_sent.setdefault(d, {"긍정":0,"부정":0,"중립":0})
            date_sent[d][r["감성"]] += 1

    # ── 탭 구성 ──
    tab_dash, tab_blog, tab_kin, tab_cafe, tab_yt = st.tabs(
        ["📊 대시보드", "📝 블로그", "💬 지식인", "☕ 카페", "▶ 유튜브"])

    # ─────────────────────────────────
    # 대시보드 탭
    # ─────────────────────────────────
    with tab_dash:
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("↑")} <span style="font-size:0.95rem;font-weight:600;">분석 요약</span></div>', unsafe_allow_html=True)

        # ★ 필터 버튼 — selectbox로 교체하여 rerun 없이 작동
        dash_filter = st.session_state["dash_filter"]

        # 라디오 버튼 스타일 필터
        filter_options = [f"전체 ({total})", f"긍정 ({pos})", f"부정 ({neg})", f"중립 ({neu})"]
        filter_map     = {f"전체 ({total})":"전체", f"긍정 ({pos})":"긍정", f"부정 ({neg})":"부정", f"중립 ({neu})":"중립"}

        # 현재 선택된 옵션 인덱스 찾기
        current_idx = 0
        for i, opt in enumerate(filter_options):
            if filter_map[opt] == dash_filter:
                current_idx = i; break

        selected_opt = st.radio(
            "필터",
            filter_options,
            index=current_idx,
            horizontal=True,
            label_visibility="collapsed",
            key="dash_radio"
        )
        st.session_state["dash_filter"] = filter_map[selected_opt]
        dash_filter = st.session_state["dash_filter"]

        # 메트릭 카드
        c1, c2, c3, c4 = st.columns(4)
        for col, cls, lbl, val in [(c1,"total","전체",total),(c2,"pos","긍정",pos),(c3,"neg","부정",neg),(c4,"neu","중립",neu)]:
            with col:
                pct = round(val/total*100) if total else 0
                st.markdown(f"""
                <div class="metric-card {cls}">
                    <div class="metric-label"><span class="metric-icon {cls}">{lbl}</span>{lbl}</div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-pct">{pct}%</div>
                </div>
                """, unsafe_allow_html=True)

        # 필터된 결과
        filtered_results = results if dash_filter == "전체" else [r for r in results if r["감성"] == dash_filter]
        st.markdown(f'<div style="font-size:0.78rem;color:#718096;margin:0.5rem 0;">현재 필터: <strong style="color:#0066CC;">{dash_filter}</strong> — {len(filtered_results)}건</div>', unsafe_allow_html=True)

        # 일자별 감성 추이
        if date_sent:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("📈")} <span style="font-size:0.95rem;font-weight:600;">일자별 감성 추이</span></div>', unsafe_allow_html=True)
            chart_rows = []
            for d, counts in date_sent.items():
                chart_rows.append({"날짜": d, "감성": "긍정", "건수": counts["긍정"]})
                chart_rows.append({"날짜": d, "감성": "부정", "건수": counts["부정"]})
            chart_df    = pd.DataFrame(chart_rows).sort_values("날짜")
            color_scale = alt.Scale(domain=["긍정","부정"], range=["#16A34A","#DC2626"])
            chart = (alt.Chart(chart_df)
                .mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X("날짜:O", axis=alt.Axis(title="", labelAngle=-45, labelFontSize=10)),
                    y=alt.Y("건수:Q", axis=alt.Axis(title="건수", titleFontSize=11)),
                    color=alt.Color("감성:N", scale=color_scale, legend=alt.Legend(title="감성")),
                    tooltip=[alt.Tooltip("날짜:O"), alt.Tooltip("감성:N"), alt.Tooltip("건수:Q")]
                ).properties(height=250)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=True, gridColor="#F0F0F0", domain=False))
            st.altair_chart(chart, use_container_width=True)

        # TOP 10
        filt_subs = []
        for r in filtered_results:
            if r.get("소분류"): filt_subs.extend([s.strip() for s in r["소분류"].split(",") if s.strip()])
        filt_sub_cnt = Counter(filt_subs)

        filt_codes = []
        for r in filtered_results:
            if r.get("품번"):
                for c in r["품번"].split(","):
                    c = c.strip()
                    if c: filt_codes.append(f"{c} {r.get('품명','') }".strip())
        filt_code_cnt = Counter(filt_codes)

        col_top1, col_top2 = st.columns(2)
        with col_top1:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("분류")} <span style="font-size:0.95rem;font-weight:600;">소분류 TOP 10</span></div>', unsafe_allow_html=True)
            html = ""
            for rank, (name, count) in enumerate(filt_sub_cnt.most_common(10), 1):
                cls = "r1" if rank == 1 else ""
                html += f'<div class="top-item"><div class="top-rank {cls}">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>'
            st.markdown(f'<div class="card">{html or "<span style=\'color:#718096;font-size:0.82rem;\'>소분류 데이터 없음</span>"}</div>', unsafe_allow_html=True)

        with col_top2:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("품번")} <span style="font-size:0.95rem;font-weight:600;">주요 품번+품명 TOP 10</span></div>', unsafe_allow_html=True)
            html2 = ""
            for rank, (name, count) in enumerate(filt_code_cnt.most_common(10), 1):
                cls = "r1" if rank == 1 else ""
                html2 += f'<div class="top-item"><div class="top-rank {cls}">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>'
            st.markdown(f'<div class="card">{html2 or "<span style=\'color:#718096;font-size:0.82rem;\'>품번 데이터 없음</span>"}</div>', unsafe_allow_html=True)

        # 글 목록
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("📋")} <span style="font-size:0.95rem;font-weight:600;">{dash_filter} 글 목록</span></div>', unsafe_allow_html=True)

        if "excluded_items" not in st.session_state:
            st.session_state["excluded_items"] = {}

        if filtered_results:
            for idx, r in enumerate(filtered_results[:30]):
                item_key = r.get("link", str(idx))
                if item_key in st.session_state["excluded_items"]:
                    continue

                _b     = SENT_BADGE.get(r["감성"], "")
                _sub   = ('<span>🗂 ' + r["소분류"] + '</span>') if r.get("소분류") else ""
                _code  = ('<span>🔢 ' + r["품번"]   + '</span>') if r.get("품번")   else ""
                _badge = f'<span class="{_b}">{r["감성"]} {fmt_score(r["확신도"])}</span>'
                _title = r["title"] or "(제목 없음)"

                # AI 요약 코멘트
                title_clean = clean_text(r.get("title",""))
                neg_found   = [kw for kw in get_neg_kw() if kw in title_clean]
                pos_found   = [kw for kw in get_pos_kw() if kw in title_clean]
                if r["감성"] == "부정" and neg_found:
                    summary = f"부정 키워드: {', '.join(neg_found[:3])} — 상품 품질/사용성 불만 가능성"
                elif r["감성"] == "긍정" and pos_found:
                    summary = f"긍정 키워드: {', '.join(pos_found[:3])} — 고객 만족 요인"
                elif r["감성"] == "부정":
                    summary = "AI 모델이 부정으로 판단 — 상세 내용 확인 필요"
                elif r["감성"] == "긍정":
                    summary = "AI 모델이 긍정으로 판단 — 강점 요인 확인"
                else:
                    summary = "중립적 언급 — 특별한 감성 경향 없음"

                _html = (
                    '<div class="result-card">'
                    '<div class="result-title">'
                    f'<a href="{r["link"]}" target="_blank" style="color:#1A202C;text-decoration:none;">{_title}</a>'
                    '</div>'
                    f'<div style="font-size:0.75rem;color:#4A5568;background:#F8F9FB;padding:0.4rem 0.6rem;border-radius:6px;margin:0.3rem 0;">💡 {summary}</div>'
                    '<div class="result-meta">'
                    f'<span>📍 {r["출처"]}</span>'
                    f'<span>🔍 {r["검색어"]}</span>'
                    f'<span>📅 {r["날짜"]}</span>'
                    + _sub + _code + _badge +
                    '</div>'
                    '</div>')
                st.markdown(_html, unsafe_allow_html=True)

                # 관리자 모드: 제외 UI
                if st.session_state["admin_mode"]:
                    with st.expander(f"🛡 관리자: 이 글 제외하기 (#{idx+1})", expanded=False):
                        excl_col1, excl_col2 = st.columns([3, 1])
                        with excl_col1:
                            reason = st.text_input("제외 사유", key=f"exclude_reason_{idx}", placeholder="예: 무관한 글 · 스팸 · 홍보성")
                        with excl_col2:
                            st.markdown("<div style='margin-top:1.6rem'></div>", unsafe_allow_html=True)
                            if st.button("제외 확정", key=f"exclude_btn_{idx}", use_container_width=True):
                                if reason.strip():
                                    st.session_state["admin_excluded_urls"][item_key] = reason.strip()
                                    st.session_state["admin_retrain_log"].append({
                                        "시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "내용": f"[URL제외] '{_title[:40]}' — 사유: {reason.strip()}"
                                    })
                                    # 결과에서도 즉시 제거
                                    st.session_state["analysis_results"] = [
                                        x for x in st.session_state["analysis_results"]
                                        if x.get("link","") != item_key
                                    ]
                                    st.success("✅ 제외 완료"); st.rerun()
                                else:
                                    st.warning("제외 사유를 입력해주세요.")

                        # 제목 키워드 자동 학습 제안
                        if r.get("title"):
                            kw_suggest = clean_text(r["title"])[:20]
                            st.markdown(f'<div style="font-size:0.75rem;color:#718096;margin-top:0.3rem;">💡 제목 키워드를 <b>⛔ 직접 제외 목록</b>에 등록하면 유사 글이 자동 필터링됩니다.</div>', unsafe_allow_html=True)
                            if st.button(f"🔄 AI 재학습: '{kw_suggest[:15]}...' 키워드 등록", key=f"relearn_btn_{idx}"):
                                ok, msg = admin_apply_keyword("exclude", kw_suggest, "add")
                                if ok:
                                    st.success(f"✅ AI 재학습 반영: {msg}")
                                else:
                                    st.info(f"ℹ {msg}")
        else:
            st.info(f"'{dash_filter}'으로 분류된 글이 없습니다.")

        # 제외된 항목 관리
        if st.session_state["admin_mode"] and st.session_state.get("admin_excluded_urls"):
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("🚫")} <span style="font-size:0.95rem;font-weight:600;">제외된 항목 ({len(st.session_state["admin_excluded_urls"])}건)</span></div>', unsafe_allow_html=True)
            excl_df = pd.DataFrame([{"URL": k[:60]+"...", "제외사유": v} for k, v in st.session_state["admin_excluded_urls"].items()])
            st.dataframe(excl_df, use_container_width=True, hide_index=True)
            if st.button("🗑 제외 목록 초기화", key="clear_excl_urls"):
                st.session_state["admin_excluded_urls"] = {}
                st.rerun()

        # 다운로드
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("↓")} <span style="font-size:0.95rem;font-weight:600;">결과 다운로드</span></div>', unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        with dl1:
            buf = create_excel(results, start_date, end_date)
            st.download_button("📥 EXCEL 다운로드", buf,
                f"ISSUE_{start_date}_{end_date}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        with dl2:
            csv_data = pd.DataFrame(results).to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSV 다운로드", csv_data.encode("utf-8-sig"),
                f"ISSUE_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)


    # ─────────────────────────────────
    # 채널별 상세 탭
    # ─────────────────────────────────
    def render_detail_tab(src_results, src_name):
        if not src_results:
            st.info(f"{src_name} 수집 결과가 없습니다."); return
        t  = len(src_results)
        p  = sum(1 for r in src_results if r["감성"]=="긍정")
        n  = sum(1 for r in src_results if r["감성"]=="부정")
        ne = sum(1 for r in src_results if r["감성"]=="중립")

        c1,c2,c3,c4 = st.columns(4)
        for col, cls, lbl, val in [(c1,"total","전체",t),(c2,"pos","긍정",p),(c3,"neg","부정",n),(c4,"neu","중립",ne)]:
            with col:
                st.markdown(f"""
                <div class="metric-card {cls}">
                    <div class="metric-label"><span class="metric-icon {cls}">{lbl}</span>{lbl}</div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-pct">{round(val/t*100) if t else 0}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        kw_stats = {}
        for r in src_results:
            kw = r.get("검색어","")
            kw_stats.setdefault(kw, {"긍정":0,"부정":0,"중립":0})
            kw_stats[kw][r["감성"]] += 1
        kw_rows = []
        for kw, s in kw_stats.items():
            t2 = sum(s.values())
            kw_rows.append({"검색어":kw,"긍정":s["긍정"],"부정":s["부정"],"중립":s["중립"],
                            "합계":t2,"부정률(%)":round(s["부정"]/t2*100,1) if t2 else 0})

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("검색")} <span style="font-size:0.95rem;font-weight:600;">검색어별 분포</span></div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(kw_rows), use_container_width=True, hide_index=True, height=160)

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.75rem;">{icon("목록")} <span style="font-size:0.95rem;font-weight:600;">상세 결과</span></div>', unsafe_allow_html=True)
        for r in src_results:
            _b     = SENT_BADGE.get(r["감성"], "")
            _sub   = ('<span>🗂 ' + r["소분류"]   + '</span>') if r.get("소분류")   else ""
            _code  = ('<span>🔢 ' + r["품번"]     + '</span>') if r.get("품번")     else ""
            _name  = ('<span>🏷 '  + r["품명"]     + '</span>') if r.get("품명")     else ""
            _price = ('<span>💰 ' + r["가격언급"] + '</span>') if r.get("가격언급") else ""
            _badge = f'<span class="{_b}">{r["감성"]} {fmt_score(r["확신도"])}</span>'
            _title = r["title"] or "(제목 없음)"
            st.markdown(
                '<div class="result-card">'
                '<div class="result-title">'
                f'<a href="{r["link"]}" target="_blank" style="color:#1A202C;text-decoration:none;">{_title}</a>'
                '</div>'
                '<div class="result-meta">'
                f'<span>🔍 {r["검색어"]}</span>'
                f'<span>📅 {r["날짜"]}</span>'
                + _sub + _code + _name + _price + _badge +
                '</div>'
                '</div>',
                unsafe_allow_html=True)

        src_csv = pd.DataFrame(src_results).to_csv(index=False, encoding="utf-8-sig")
        st.download_button(f"📥 {src_name} CSV 다운로드", src_csv.encode("utf-8-sig"),
            f"ISSUE_{src_name}_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

    with tab_blog:
        render_detail_tab([r for r in results if r["출처"]=="블로그"], "블로그")
    with tab_kin:
        render_detail_tab([r for r in results if r["출처"]=="지식인"], "지식인")
    with tab_cafe:
        render_detail_tab([r for r in results if r["출처"]=="카페"], "카페")

    with tab_yt:
        yt_results = [r for r in results if r["출처"]=="유튜브"]
        if not yt_results:
            if not YOUTUBE_API_KEY:
                st.warning("YOUTUBE_API_KEY가 secrets에 없습니다.")
            else:
                st.info("유튜브 수집 결과가 없습니다.")
        else:
            yt_t  = len(yt_results)
            yt_p  = sum(1 for r in yt_results if r["감성"]=="긍정")
            yt_n  = sum(1 for r in yt_results if r["감성"]=="부정")
            yt_ne = sum(1 for r in yt_results if r["감성"]=="중립")

            yc1,yc2,yc3,yc4 = st.columns(4)
            for col, cls, lbl, val in [(yc1,"total","영상",yt_t),(yc2,"pos","긍정",yt_p),(yc3,"neg","부정",yt_n),(yc4,"neu","중립",yt_ne)]:
                with col:
                    st.markdown(f"""
                    <div class="metric-card {cls}">
                        <div class="metric-label"><span class="metric-icon {cls}">{lbl}</span>{lbl}</div>
                        <div class="metric-value">{val}</div>
                        <div class="metric-pct">{round(val/yt_t*100) if yt_t else 0}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("영상")} <span style="font-size:0.95rem;font-weight:600;">영상 목록 (조회수 순)</span></div>', unsafe_allow_html=True)
            for r in sorted(yt_results, key=lambda x: x.get("views") or 0, reverse=True)[:20]:
                b        = SENT_BADGE.get(r["감성"],"")
                views    = f"{r['views']:,}"    if isinstance(r.get("views"),int)    else "-"
                likes    = f"{r['likes']:,}"    if isinstance(r.get("likes"),int)    else "-"
                comments = f"{r['comments']:,}" if isinstance(r.get("comments"),int) else "-"
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-title">
                        <a href="{r['link']}" target="_blank" style="color:#1A202C;text-decoration:none;">{r['title']}</a>
                    </div>
                    <div class="result-meta">
                        <span>📺 {r.get('channel','')}</span>
                        <span>📅 {r['날짜']}</span>
                        <span>▶ {views}</span>
                        <span>♥ {likes}</span>
                        <span>💬 {comments}</span>
                        <span class="{b}">{r['감성']} {fmt_score(r['확신도'])}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div style="margin-top:1.5rem;padding:1.25rem 1.5rem;background:#F8FAFC;border:1.5px dashed #CBD5E1;border-radius:10px;text-align:center;">
                <div style="font-size:0.9rem;font-weight:600;color:#64748B;margin-bottom:0.3rem;">💬 유튜브 댓글 감성분석</div>
                <div class="badge-coming" style="display:inline-flex;">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>추가 예정 기능입니다
                </div>
                <div style="font-size:0.75rem;color:#94A3B8;margin-top:0.5rem;">다음 버전에서 제공될 예정입니다</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;border-top:1px solid #E2E8F0;margin-top:2rem;">
        <span style="font-size:0.75rem;color:#A0AEC0;">DAISO SNS ISSUE FINDER · Multilingual Sentiment × KLUE-RoBERTa Ensemble · Created by 데이터분석팀</span>
    </div>
    """, unsafe_allow_html=True)
