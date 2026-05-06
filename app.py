import streamlit as st
import requests
import openpyxl
import re
import io
import gspread
import pandas as pd
import altair as alt
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
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* ── 사이드바 ── */
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

/* ── 날짜 입력 간격 축소 ── */
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
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] > label {
    display: none !important;
}
.date-label {
    font-size: 0.7rem;
    color: #718096;
    margin-top: 0;
    margin-bottom: 0.1rem;
    display: block;
    line-height: 1.1;
}
[data-testid="stSidebar"] [data-testid="column"] {
    gap: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* ── 헤더 ── */
.app-header {
    background: var(--bg-white);
    border-bottom: 1px solid var(--border);
    padding: 1.25rem 2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    border-radius: 12px;
    box-shadow: var(--shadow);
}
.header-icon {
    width: 40px; height: 40px;
    background: var(--primary);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; color: #FFFFFF !important; flex-shrink: 0;
}
.header-title {
    font-size: 1.25rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.01em;
}
.header-sub {
    font-size: 0.78rem; color: var(--text3);
    margin-top: 0.1rem;
}

/* ── 카드 ── */
.card {
    background: var(--bg-white);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

/* ── 메트릭 카드 ── */
.metric-card {
    flex: 1; background: var(--bg-white);
    border: 1px solid var(--border); border-radius: 12px;
    padding: 1.25rem 1.5rem; box-shadow: var(--shadow);
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
    width: 22px; height: 22px;
    background: var(--primary);
    border-radius: 6px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #FFFFFF !important;
    font-size: 0.68rem; font-weight: 700;
    flex-shrink: 0; line-height: 1;
}
.metric-icon.pos { background: var(--pos);  color: #FFFFFF !important; }
.metric-icon.neg { background: var(--neg);  color: #FFFFFF !important; }
.metric-icon.neu { background: var(--neu);  color: #FFFFFF !important; }
.metric-value {
    font-family: 'Inter', sans-serif; font-size: 2.2rem;
    font-weight: 600; color: var(--text); line-height: 1;
}
.metric-pct { font-size: 0.78rem; color: var(--text3); margin-top: 0.3rem; }

/* ── 섹션 타이틀 아이콘 ── */
.section-title-icon {
    width: 24px; height: 24px;
    background: var(--primary);
    border-radius: 6px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #FFFFFF !important;
    font-size: 0.75rem; font-weight: 700;
    flex-shrink: 0; vertical-align: middle;
}

/* ── 감성 뱃지 ── */
.badge-pos { background: var(--pos-bg); color: var(--pos); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neg { background: var(--neg-bg); color: var(--neg); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neu { background: var(--neu-bg); color: var(--neu); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-sub { background: var(--primary-lt); color: var(--primary); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
/* ── TOP 아이템 ── */
.top-item {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.6rem 0; border-bottom: 1px solid var(--border);
}
.top-item:last-child { border-bottom: none; }
.top-rank {
    width: 26px; height: 26px; background: var(--primary-lt);
    border-radius: 6px; display: flex; align-items: center;
    justify-content: center; font-size: 0.72rem; font-weight: 700;
    color: var(--primary); flex-shrink: 0;
}
.top-rank.r1 { background: var(--primary); color: #FFFFFF !important; }
.top-name { flex: 1; font-size: 0.85rem; color: var(--text); }
.top-count {
    font-size: 0.78rem; font-weight: 600; color: var(--primary);
    background: var(--primary-lt); padding: 2px 8px; border-radius: 20px;
}

/* ── 결과 카드 ── */
.result-card {
    background: var(--bg-white); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.5rem;
    box-shadow: var(--shadow); transition: box-shadow 0.2s;
}
.result-card:hover { box-shadow: var(--shadow-md); }
.result-title { font-size: 0.9rem; font-weight: 500; color: var(--text); margin-bottom: 0.4rem; }
.result-meta { font-size: 0.75rem; color: var(--text3); display: flex; gap: 0.75rem; flex-wrap: wrap; }
.result-meta span { display: flex; align-items: center; gap: 0.2rem; }

/* ── 로그인 ── */
.login-wrap {
    max-width: 380px; margin: 5rem auto;
    background: var(--bg-white); border: 1px solid var(--border);
    border-radius: 16px; padding: 2.5rem 2rem; text-align: center;
    box-shadow: var(--shadow-md);
}
.login-icon {
    width: 52px; height: 52px; background: var(--primary);
    border-radius: 14px; margin: 0 auto 1rem;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; color: #FFFFFF !important;
}
.login-title { font-size: 1.3rem; font-weight: 700; color: var(--text); margin-bottom: 0.25rem; }
.login-sub { font-size: 0.82rem; color: var(--text3); margin-bottom: 1.5rem; }

/* ── 사이드바 섹션 헤더 ── */
.sb-section {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.55rem 0.7rem;
    background: var(--primary-lt);
    border-left: 3px solid var(--primary);
    border-radius: 0 6px 6px 0;
    margin: 1rem 0 0.5rem;
}
.sb-section-icon {
    width: 20px; height: 20px;
    background: var(--primary);
    border-radius: 5px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #FFFFFF !important;
    font-size: 0.62rem; font-weight: 700; flex-shrink: 0;
}
.sb-section-text {
    font-size: 0.72rem; font-weight: 700;
    color: var(--primary) !important;
    text-transform: uppercase; letter-spacing: 0.07em;
}
.sb-hint { font-size: 0.68rem; color: var(--text3); margin-top: 0.05rem; display: block; line-height: 1.3; }

/* ── 채널 체크박스 ── */
.ch-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0;
    min-height: 32px;
}
.ch-icon {
    width: 20px; height: 20px; border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.55rem; color: #FFFFFF !important;
    font-weight: 900; flex-shrink: 0;
}
.ch-naver   { background: #03C75A; }
.ch-youtube { background: #FF0000; }
.ch-label   {
    font-size: 0.82rem; font-weight: 500;
    color: var(--text) !important;
    line-height: 1;
}

/* ── 숫자 입력 ── */
[data-testid="stNumberInput"] > div { border-radius: 8px !important; }
[data-testid="stNumberInput"] button { color: var(--primary) !important; }

/* ── 버튼 기본 ── */
.stButton > button {
    background: var(--primary) !important; color: #FFFFFF !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important; font-weight: 600 !important;
    padding: 0.6rem 1.25rem !important; transition: all 0.2s !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    background: #0052A3 !important;
    box-shadow: 0 4px 12px rgba(0,102,204,0.3) !important;
}

/* ── 분석 시작 버튼 — 노란색 ── */
[data-testid="stSidebar"] .stButton > button {
    background: #FFD600 !important;
    color: #1A202C !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.03em !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(255,214,0,0.35) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #F5C800 !important;
    box-shadow: 0 4px 14px rgba(255,214,0,0.5) !important;
    color: #1A202C !important;
}
[data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button {
    background: #E2E8F0 !important;
    color: #DC2626 !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button:hover {
    background: #FEE2E2 !important;
    color: #DC2626 !important;
}

.stDownloadButton > button {
    background: var(--bg-white) !important; color: var(--primary) !important;
    border: 1.5px solid var(--primary) !important; border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important; font-weight: 500 !important;
    width: 100% !important;
}
.stDownloadButton > button:hover { background: var(--primary-lt) !important; }

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid var(--border) !important; gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.85rem !important; font-weight: 500 !important;
    color: var(--text3) !important; background: transparent !important;
    border: none !important; border-bottom: 2px solid transparent !important;
    padding: 0.6rem 1.2rem !important; border-radius: 0 !important;
    margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom-color: var(--primary) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem !important; }

/* ── 기타 ── */
.stProgress > div > div > div > div { background: var(--primary) !important; border-radius: 4px !important; }
.stProgress > div > div > div { background: var(--border) !important; border-radius: 4px !important; height: 6px !important; }
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; }
.stAlert { border-radius: 8px !important; }
hr { border: none; border-top: 1px solid var(--border) !important; margin: 1rem 0 !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="collapsedControl"] { visibility: visible !important; display: block !important; }

.badge-coming {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #F1F5F9; color: #64748B;
    border: 1px dashed #CBD5E1;
    padding: 0.35rem 0.75rem; border-radius: 6px;
    font-size: 0.78rem; font-weight: 500;
}

/* 체크박스 세로 정렬 */
[data-testid="stSidebar"] .stCheckbox {
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: unset !important;
}
[data-testid="stSidebar"] .stCheckbox label {
    padding: 0 !important;
    min-height: unset !important;
    gap: 0 !important;
}

/* ── 감성 파라미터 안내 박스 ── */
.param-guide-box {
    background: #F0F7FF;
    border: 1.5px solid #B3D1F5;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin: 0.5rem 0 1rem;
    font-size: 0.78rem;
    color: #1A202C;
    line-height: 1.7;
}
.param-guide-box b { color: #0066CC; }
.param-guide-box code {
    background: #E8F1FB; color: #0052A3;
    border-radius: 4px; padding: 1px 5px;
    font-size: 0.74rem; font-family: monospace;
}

/* ── 카페 날짜 안내 뱃지 ── */
.cafe-date-note {
    background: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 6px;
    padding: 0.3rem 0.6rem;
    font-size: 0.68rem;
    color: #15803D;
    margin-top: 0.25rem;
    display: block;
    line-height: 1.4;
}

/* ── 관리자 모드 ── */
.admin-badge-on {
    background: #7C3AED; color: #fff; padding: 2px 8px;
    border-radius: 4px; font-size: 0.7rem; font-weight: 700;
}
.admin-login-modal { text-align: center; padding: 1.5rem 0 0.5rem; }
.admin-login-icon { font-size: 2rem; }
</style>
""", unsafe_allow_html=True)


# ============================================== 비밀번호 인증
def check_password():
    if st.session_state.get("authenticated"):
        return True

    def _try_login():
        if st.session_state.get("login_pw", "") == st.secrets.get("PASSWORD", ""):
            st.session_state.authenticated = True
        else:
            st.session_state["_login_error"] = True

    st.markdown("""
    <div class="login-wrap">
        <div class="login-icon">🔵</div>
        <div class="login-title">DAISO SNS ISSUE FINDER</div>
        <div class="login-sub">다이소 SNS 상품불량 수집 AI시스템</div>
    </div>
    """, unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        st.text_input(
            "", type="password", placeholder="비밀번호 입력",
            label_visibility="collapsed",
            key="login_pw",
            on_change=_try_login,
        )
        if st.button("로그인", use_container_width=True):
            _try_login()
        if st.session_state.pop("_login_error", False):
            st.error("비밀번호가 올바르지 않습니다.")
        if st.session_state.get("authenticated"):
            st.rerun()
    return False

if not check_password():
    st.stop()

# ============================================== API키
NAVER_CLIENT_ID     = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
YOUTUBE_API_KEY     = st.secrets.get("YOUTUBE_API_KEY", "")
ADMIN_PASSWORD      = st.secrets.get("ADMIN_PASSWORD", "admin1234")

# ============================================== 관리자 모드 세션 초기화
for _k, _v in {"admin_mode": False, "admin_show_login": False, "admin_exclude_kws": []}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ============================================== 구글시트 연동 (keyword / exclude_urls)
SHEET_ID = "1iZS_bBlmZaMRFfW-l6XTP5zUZzit3vxhSIogEB-ynDM"

def _get_gspread_client(readonly=True):
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"] if readonly else [
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_keywords_from_sheet():
    """구글시트 [keyword] 탭에서 neg/pos/promo/exclude 키워드 로드."""
    try:
        gc = _get_gspread_client()
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet("keyword")
        rows = ws.get_all_records()
        result = {"neg": [], "pos": [], "promo": [], "exclude": []}
        for r in rows:
            t = r.get("type", "").strip().lower()
            kw = r.get("keyword", "").strip()
            if t in result and kw:
                result[t].append(kw)
        return result
    except Exception as e:
        st.warning(f"⚠ keyword 시트 로드 실패: {e}")
        return {"neg": [], "pos": [], "promo": [], "exclude": []}

@st.cache_data(ttl=600)
def load_excluded_urls_from_sheet():
    """구글시트 [exclude_urls] 탭에서 제외 URL 목록 로드."""
    try:
        gc = _get_gspread_client()
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet("exclude_urls")
        rows = ws.get_all_records()
        return {r.get("url", "").strip() for r in rows if r.get("url", "").strip()}
    except Exception as e:
        st.warning(f"⚠ exclude_urls 시트 로드 실패: {e}")
        return set()

def append_keyword_to_sheet(kw_type, keyword):
    """구글시트 [keyword] 탭에 키워드 추가."""
    try:
        gc = _get_gspread_client(readonly=False)
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet("keyword")
        ws.append_row([kw_type, keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        load_keywords_from_sheet.clear()
    except Exception as e:
        st.error(f"시트 저장 실패: {e}")

def append_excluded_url_to_sheet(url, reason="관리자 제외"):
    """구글시트 [exclude_urls] 탭에 URL 추가."""
    try:
        gc = _get_gspread_client(readonly=False)
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet("exclude_urls")
        ws.append_row([url, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        load_excluded_urls_from_sheet.clear()
    except Exception as e:
        st.error(f"시트 저장 실패: {e}")

# 시트에서 키워드 로드
_sheet_kw = load_keywords_from_sheet()
EXCLUDED_URLS_FROM_SHEET = load_excluded_urls_from_sheet()


# ============================================== 구글시트 불러오기 (품번,품명,소분류)
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

# ── 제외할 소분류 (직접 수정) ──
EXCLUDE_SUBCATEGORIES = ["차", "자"]

# ============================================== AI모델링 (KLUE-RoBERTa + 룰베이스)
@st.cache_resource
def load_roberta():
    try:
        return pipeline("text-classification", model="Chamsol/klue-roberta-sentiment-classification",
                        truncation=True, max_length=128, top_k=None, device=-1)
    except Exception:
        return None


# ============================
# 룰베이스 & 앙상블
# ============================
NEGATIVE_KW = [
    "불만","짜증","별로","최악","실망","환불","불량","교환","이상해","형편없",
    "쓰레기","구려","나빠","고장","터졌","망가","깨졌","불편","아쉬워","위험",
    "조심","주의","문제","하자","뜯겨","냄새","오염","불결","지저분","더럽",
    "싸구려","허접","대충","클레임","AS","환급","반품","재구매 안","비추","별점 1",
    "별점1","1점","속았","낚였","사기","뻥","가짜","품질 나쁜","품질이 나쁜",
    "뚜껑이 안","뚜껑이 깨","잘 안 돼","안 되는","못 쓰겠","못써","쓸모없어",
    "수량적음","색이다름","색상상이","성능과장","원산지 불명확","색감차이",
    "과포장","과점착","색번짐","이염","후회","별로야","별로네","글쎄","그냥저냥",
    "생각보다 별로","기대 이하","실패","구매실패","돈낭비","돈 낭비","비싸","불합리",
    "사지마","사지 마","추천안","추천 안","별1","1개","뒤틀","휘어","금방망가",
    "금방 망가","오래못가","오래 못가","금방부서","금방 부서","변질","변질되","변질됐","부서지","부서졌","터지","터졌",
    "녹았","녹았어요","녹았네요","녹이 슬음","녹이 슬었","녹이 슬었어요","녹이 슬었네요","녹이 슨","녹이 슨거","녹이 슨것",
]
POSITIVE_KW = [
    "좋아요","좋았","만족","추천","재구매","최고","훌륭","완벽","편리","예뻐",
    "가성비","합리적","대박","꿀템","강추","마음에 들","만족스럽","굿","짱",
    "갓성비","득템","완전좋","완전 좋","행복","사랑","최애","예쁘다","예쁜",
    "지림","지려","감탄","감동","최적","최상의","맘에 쏙","맘에 들어","맘에 들었"
]

PROMO_KW = [
    "다이소 매장", "다이소 오픈", "다이소 신상", "다이소 신제품", "다이소 근처",
    "다이소 위치", "다이소 영업시간", "다이소 매장 위치", "다이소 점포",
    "다이소 방문", "다이소 주차", "다이소에서 구입", "다이소 쇼핑",
    "홍보", "광고", "제품을 받았습니다", "제공받아", "협찬", "무료로 받",
    "내돈내산 아닌", "리뷰어", "체험단", "서포터즈", "내돈내산아님",
    "다이소 하울", "다이소 추천템", "다이소 인기템", "다이소 꿀템 추천",
    "다이소 추천 아이템", "다이소 베스트", "다이소 신상품 추천","매장 옆", "매장 근처", "매장 앞", "매장 뒤", "매장 주변",
    "도전", "챌린지", "이벤트", "할인", "세일", "쿠폰", "프로모션", "특가"
]

PROMO_PATTERNS = [
    r"제공.{0,5}받", r"협찬", r"체험단", r"서포터즈",
    r"소정의\s*원고료", r"원고료.*지급", r"광고.*포함",
    r"링크.*통해.*구매", r"할인\s*코드", r"쿠폰\s*코드",
]

TITLE_PROMO_KW = ["추천", "하울", "꿀템", "인생템", "갓성비", "득템", "베스트", "추천템"]

# 구글시트 키워드 병합
NEGATIVE_KW = list(set(NEGATIVE_KW + _sheet_kw.get("neg", [])))
POSITIVE_KW = list(set(POSITIVE_KW + _sheet_kw.get("pos", [])))
PROMO_KW    = list(set(PROMO_KW + _sheet_kw.get("promo", [])))
SHEET_EXCLUDE_KW = _sheet_kw.get("exclude", [])

def is_promotional(item: dict) -> bool:
    title = clean_text(item.get("title", ""))
    desc  = clean_text(item.get("description", ""))
    full  = title + " " + desc
    promo_hit = sum(1 for kw in PROMO_KW if kw in full)
    pattern_hit = sum(1 for p in PROMO_PATTERNS if re.search(p, full))
    neg_hit = sum(1 for kw in NEGATIVE_KW if kw in full)
    title_promo = sum(1 for kw in TITLE_PROMO_KW if kw in title)
    if (promo_hit >= 1 or pattern_hit >= 1 or title_promo >= 1) and neg_hit <= 1:
        return True
    return False


LABEL_MAP = {
    "positive":"긍정","pos":"긍정","LABEL_2":"긍정","긍정":"긍정",
    "negative":"부정","neg":"부정","LABEL_0":"부정","부정":"부정",
    "neutral":"중립","neu":"중립","LABEL_1":"중립","중립":"중립",
    "부정":"부정","긍정":"긍정",
}

def rule_based(text: str):
    neg = sum(1 for kw in NEGATIVE_KW if kw in text)
    pos = sum(1 for kw in POSITIVE_KW if kw in text)
    if neg > pos:  return "부정", min(0.65 + neg * 0.08, 0.98)
    if pos > neg:  return "긍정", min(0.60 + pos * 0.08, 0.98)
    return "중립", 0.50

def ensemble_sentiment(roberta_output, full_text: str, threshold: int) -> tuple:
    votes = {"긍정": 0.0, "부정": 0.0, "중립": 0.0}

    roberta_neg_prob = 0.0
    if roberta_output:
        try:
            for it in roberta_output:
                lbl = LABEL_MAP.get(it["label"])
                if lbl:
                    votes[lbl] += it["score"] * 2.0
                    if lbl == "부정":
                        roberta_neg_prob = it["score"]
        except Exception:
            pass

    rule_lbl, rule_sc = rule_based(full_text)
    votes[rule_lbl] += rule_sc * 1.2

    total = sum(votes.values())
    if total == 0:
        return "중립", 50
    best  = max(votes, key=votes.get)
    score = round(votes[best] / total * 100)
    neg_kw_cnt = sum(1 for kw in NEGATIVE_KW if kw in full_text)

    if neg_kw_cnt >= 3:
        return "부정", max(score, 75)
    if roberta_neg_prob >= 0.5 and neg_kw_cnt >= 1:
        return "부정", max(score, 70)
    if roberta_neg_prob >= 0.4 and neg_kw_cnt >= 2:
        return "부정", max(score, 65)

    if score < threshold and best != "중립":
        return "중립", max(score - 10, 40)

    return best, score


# ============================
# 다이소 관련성 필터
# ============================
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


# ============================
# 네이버 블로그 수집 (페이징)
# ============================
def collect_naver_paged(query: str, search_type: str, total: int) -> list:
    all_items = []
    per_page  = 100
    start_idx = 1
    label = "블로그"

    while len(all_items) < total:
        if start_idx > 1000:
            break
        remaining = total - len(all_items)
        fetch_cnt = min(per_page, remaining, 1000 - start_idx + 1)
        if fetch_cnt <= 0:
            break

        url     = f"https://openapi.naver.com/v1/search/{search_type}.json"
        headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
        params  = {"query": query, "display": fetch_cnt, "start": start_idx, "sort": "date"}
        try:
            resp  = requests.get(url, headers=headers, params=params, timeout=10)
            items = resp.json().get("items", [])
        except Exception:
            break

        if not items:
            break

        for item in items:
            item["출처"]   = label
            item["검색어"] = query
        all_items.extend(items)
        start_idx += fetch_cnt

        if len(items) < fetch_cnt:
            break

    return all_items[:total]


# ============================
# 네이버 카페 수집 (페이징)
# ============================
def collect_cafe_paged(query: str, total: int) -> list:
    all_items = []
    per_page  = 100
    start_idx = 1

    while len(all_items) < total:
        if start_idx > 1000:
            break
        remaining = total - len(all_items)
        fetch_cnt = min(per_page, remaining, 1000 - start_idx + 1)
        if fetch_cnt <= 0:
            break

        url     = "https://openapi.naver.com/v1/search/cafearticle.json"
        headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
        params  = {"query": query, "display": fetch_cnt, "start": start_idx, "sort": "date"}
        try:
            resp  = requests.get(url, headers=headers, params=params, timeout=10)
            items = resp.json().get("items", [])
        except Exception:
            break

        if not items:
            break

        for item in items:
            item["출처"]   = "카페"
            item["검색어"] = query
            item["channel"] = item.get("cafename", "")

        all_items.extend(items)
        start_idx += fetch_cnt

        if len(items) < fetch_cnt:
            break

    return all_items[:total]


# ============================
# YouTube
# ============================
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


# ============================
# 날짜 파싱 & 필터
# ============================
def parse_date(item: dict):
    ds = item.get("postdate") or item.get("pubDate", "")
    try:
        if len(ds) == 8:
            return datetime.strptime(ds, "%Y%m%d")
        return datetime.strptime(ds[:25], "%a, %d %b %Y %H:%M:%S")
    except:
        try:
            return datetime.strptime(ds[:16], "%a, %d %b %Y")
        except:
            return None

def filter_by_date(items: list, start_dt: date, end_dt: date) -> list:
    s = datetime(start_dt.year, start_dt.month, start_dt.day)
    e = datetime(end_dt.year,   end_dt.month,   end_dt.day, 23, 59, 59)
    result = []
    for item in items:
        dt = item.get("pub_dt") if item.get("출처") == "유튜브" else parse_date(item)
        if dt and s <= dt <= e: result.append(item)
    return result

def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    return text.strip()

def is_admin_excluded(item):
    url = item.get("link", "")
    if url in EXCLUDED_URLS_FROM_SHEET:
        return True
    full = clean_text(item.get("title","")) + " " + clean_text(item.get("description",""))
    all_exclude_kws = st.session_state.get("admin_exclude_kws", []) + SHEET_EXCLUDE_KW
    return any(kw in full for kw in all_exclude_kws)


# ============================
# 품번 추출
# ============================
DATE_PATS = [
    r'\b20\d{6}\b', r'\b\d{4}[-./]\d{2}[-./]\d{2}\b',
    r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b',
    r'\b\d{4}년\s*\d{1,2}월', r'\b\d{1,2}월\s*\d{1,2}일',
]
def is_date_like(t):
    for p in DATE_PATS:
        if re.fullmatch(p, t.strip()): return True
    return bool(re.fullmatch(r'20\d{6}', t.strip()))

def extract_product_code(text):
    raw_nums = re.findall(r'\b(\d{4,11})\b', text)
    codes = []
    for c in raw_nums:
        if is_date_like(c):
            continue
        if VALID_PRODUCT_CODES and c in VALID_PRODUCT_CODES:
            codes.append(c)
        elif not VALID_PRODUCT_CODES:
            codes.append(c)
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


# ============================
# 엑셀 생성
# ============================
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


# ============================
# 헬퍼
# ============================
SENT_BADGE = {"긍정":"badge-pos","부정":"badge-neg","중립":"badge-neu"}

def icon(label: str) -> str:
    return f'<span class="section-title-icon">{label}</span>'

def fmt_score(score) -> str:
    try:
        return f"{int(round(float(score)))}%"
    except:
        return f"{score}%"


# ============================
# 관리자 모드 버튼 & 로그인
# ============================
admin_col1, admin_col2 = st.columns([10, 1])
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
        st.markdown("""<div class="admin-login-modal"><div class="admin-login-icon">🛡️</div><div style="font-size:1.1rem;font-weight:700;color:#7C3AED;margin-top:0.5rem;">관리자 로그인</div><div style="font-size:0.8rem;color:#718096;">관리자 전용 기능에 접근합니다</div><div style="font-size:0.72rem;color:#A0AEC0;margin-top:0.3rem;">※ 일반 로그인과 별도의 관리자 전용 비밀번호입니다</div></div>""", unsafe_allow_html=True)
        _, mid_col, _ = st.columns([1, 2, 1])
        with mid_col:
            def _admin_enter():
                pw = st.session_state.get("admin_pw_input", "")
                if pw == ADMIN_PASSWORD:
                    st.session_state["admin_mode"] = True
                    st.session_state["admin_show_login"] = False
                else:
                    st.session_state["_admin_login_error"] = True

            st.text_input(
                "관리자 비밀번호", type="password",
                placeholder="비밀번호 입력 후 엔터",
                label_visibility="collapsed",
                key="admin_pw_input",
                on_change=_admin_enter,
            )
            if st.session_state.pop("_admin_login_error", False):
                st.error("비밀번호가 틀렸습니다.")
            # 엔터로 성공한 경우 rerun
            if st.session_state.get("admin_mode") and st.session_state.get("admin_show_login") is False:
                st.rerun()
            lc, cc = st.columns(2)
            with lc:
                if st.button("로그인", key="admin_login_confirm", use_container_width=True):
                    _admin_enter()
                    if st.session_state.get("admin_mode"):
                        st.rerun()
            with cc:
                if st.button("취소", key="admin_login_cancel", use_container_width=True):
                    st.session_state["admin_show_login"] = False
                    st.rerun()
    st.markdown("---")

# ============================
# 앱 헤더
# ============================
st.markdown("""
<div class="app-header">
    <div style="display:flex;align-items:center;gap:0.5rem;flex-shrink:0;">
        <div style="
            width:48px; height:48px;
            background:#0066CC;
            border-radius:50%;
            display:flex; align-items:center; justify-content:center;
            flex-shrink:0;
            box-shadow:0 2px 6px rgba(0,102,204,0.35);
        ">
            <svg width="30" height="20" viewBox="0 0 60 38" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M0 2 H8 Q16 2 16 10 Q16 18 8 18 H0 Z M4 5 V15 H8 Q12 15 12 10 Q12 5 8 5 Z" fill="#FFFFFF"/>
                <path d="M18 18 L24 2 L30 18 M20.5 12 H27.5" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
                <rect x="33" y="2" width="3.5" height="16" rx="1" fill="#FFFFFF"/>
                <path d="M40 15 Q40 18 44 18 Q48 18 48 14.5 Q48 11 44 10 Q40 9 40 5.5 Q40 2 44 2 Q48 2 48 5"
                      stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
                <ellipse cx="54" cy="10" rx="5" ry="8" stroke="#FFFFFF" stroke-width="3" fill="none"/>
            </svg>
        </div>
        <div style="
            font-size:1.35rem; font-weight:900;
            color:#0066CC; letter-spacing:0.12em;
            font-family:'Inter',sans-serif;
            line-height:1;
        ">D</div>
    </div>
    <div style="width:1px;height:36px;background:#E2E8F0;margin:0 0.25rem;flex-shrink:0;"></div>
    <div>
        <div class="header-title">SNS Issue Finder : 고객 불만 AI 자동 분석</div>
        <div class="header-sub">네이버 블로그 · 카페 · 유튜브 &nbsp;|&nbsp; KLUE-RoBERTa + 룰베이스 앙상블</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================
# 사이드바
# ============================
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

    row1_left, row1_right = st.columns(2)
    with row1_left:
        cb_col, icon_col = st.columns([1, 4])
        with cb_col:
            search_blog = st.checkbox("", value=True, key="cb_blog", label_visibility="collapsed")
        with icon_col:
            st.markdown("""<div class="ch-row">
                <div class="ch-icon ch-naver">N</div>
                <span class="ch-label">블로그</span>
            </div>""", unsafe_allow_html=True)

    with row1_right:
        cb_col2, icon_col2 = st.columns([1, 4])
        with cb_col2:
            search_cafe = st.checkbox("", value=True, key="cb_cafe", label_visibility="collapsed")
        with icon_col2:
            st.markdown("""<div class="ch-row">
                <div class="ch-icon ch-naver">N</div>
                <span class="ch-label">카페</span>
            </div>""", unsafe_allow_html=True)

    row2_left, row2_right = st.columns(2)
    with row2_left:
        cb_col3, icon_col3 = st.columns([1, 4])
        with cb_col3:
            search_yt = st.checkbox("", value=True, key="cb_yt", label_visibility="collapsed")
        with icon_col3:
            st.markdown("""<div class="ch-row">
                <div class="ch-icon ch-youtube">
                    <svg width="9" height="9" viewBox="0 0 24 24" fill="#FFFFFF"><polygon points="5,3 19,12 5,21"/></svg>
                </div>
                <span class="ch-label">유튜브</span>
            </div>""", unsafe_allow_html=True)

    with row2_right:
        st.markdown("""<div class="ch-row" style="opacity:0.4;cursor:not-allowed;">
            <div style="width:20px;height:20px;border-radius:4px;background:#CBD5E1;display:flex;align-items:center;justify-content:center;font-size:0.55rem;color:#FFFFFF;font-weight:900;flex-shrink:0;">N</div>
            <span style="font-size:0.82rem;font-weight:500;color:#718096;line-height:1;text-decoration:line-through;">지식인</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
        </div>
        <span class="sb-section-text">분석 검색어</span>
    </div>
    """, unsafe_allow_html=True)
    keywords_input = st.text_area("", value="다이소 상품불량\n다이소 불량\n다이소 별로",
                                  height=95, label_visibility="collapsed",
                                  placeholder="줄바꿈으로 구분 · 최대 3개")
    st.markdown('<span class="sb-hint">줄바꿈으로 구분, 최대 3개<br>※ \'다이소\' 없으면 자동 추가됩니다</span>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
        </div>
        <span class="sb-section-text">분석 기간</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top:0.6rem"></div>', unsafe_allow_html=True)

    dc1, dc2 = st.columns(2, gap="small")
    with dc1:
        st.markdown('<span class="date-label">시작일</span>', unsafe_allow_html=True)
        start_date = st.date_input("시작일", value=date(2026, 1, 1), label_visibility="collapsed", key="date_start")
    with dc2:
        st.markdown('<span class="date-label">종료일</span>', unsafe_allow_html=True)
        end_date = st.date_input("종료일", value=date.today(), label_visibility="collapsed", key="date_end")

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
    display_count = st.number_input(
        "", min_value=50, max_value=1000, value=100, step=50,
        label_visibility="collapsed",
        help="CPU 환경 권장 수집건수 (최소 50 ~ 최대 1,000)"
    )
    st.markdown('<span class="sb-hint">CPU 권장: 100~300건 · 최대 1,000건</span>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
        </div>
        <span class="sb-section-text">감성 파라미터</span>
    </div>
    """, unsafe_allow_html=True)
    threshold = st.number_input(
        "", min_value=40, max_value=95, value=55, step=5,
        label_visibility="collapsed",
        help="AI가 이 수치 이상의 확신도로 부정 판정 시에만 부정으로 등록"
    )

    st.markdown("""
    <div class="sb-section" style="margin:0.5rem 0 0.3rem;">
        <div class="sb-section-icon">⚙</div>
        <span class="sb-section-text">감성 파라미터 가이드</span>
    </div>
    <div class="param-guide-box">
        <b>📌 감성 파라미터 조정</b><br>
        • <code>40~50%</code> → 민감하게 수집 (부정 많이 잡힘)<br>
        • <code>55~65%</code> → 권장 (정확도 균형)<br>
        • <code>70%+</code> → 엄격 (확실한 부정만)<br><br>
        <b>📌 룰베이스 키워드 직접 추가</b><br>
        코드 내 <code>NEGATIVE_KW</code> 리스트에 단어를 추가하면 해당 단어가 포함된 글을 부정으로 가중처리합니다.<br><br>
        <b>📌 홍보성 글 제외</b><br>
        <code>PROMO_KW</code> 리스트에 단어 추가 시 홍보성으로 판단해 자동 제외합니다.<br><br>
        <b>📌 현재 AI 모델 가중치 </b><br>
        • KLUE-RoBERTa 가중치: <code>* 2.0</code> (메인 모델)<br>
        • 룰베이스 가중치: <code>* 1.2</code> (키워드 보강)<br>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.6rem'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        run_btn = st.button("분석 시작", use_container_width=True)
    with btn_col2:
        stop_btn = st.button("중지", use_container_width=True)

    if st.session_state["admin_mode"]:
        st.markdown("---")
        st.markdown('<span style="font-size:0.8rem;font-weight:700;color:#7C3AED;">🛡️ 관리자 — 키워드/URL 관리</span>', unsafe_allow_html=True)

        _kw_type_map = {"제외": "exclude", "부정": "neg", "긍정": "pos", "홍보": "promo"}
        kw_type_label = st.selectbox("유형", list(_kw_type_map.keys()), key="admin_kw_type", label_visibility="collapsed")
        kw_type = _kw_type_map[kw_type_label]
        new_kw = st.text_input("키워드", key="admin_new_kw", label_visibility="collapsed", placeholder="추가할 키워드 입력")
        if st.button("➕ 시트에 키워드 추가", key="admin_add_kw", use_container_width=True) and new_kw.strip():
            append_keyword_to_sheet(kw_type, new_kw.strip())
            if kw_type == "exclude":
                st.session_state["admin_exclude_kws"].append(new_kw.strip())
            st.success(f"✅ [{kw_type}] '{new_kw.strip()}' 시트 저장 완료")
            st.rerun()

        st.markdown('<span style="font-size:0.75rem;color:#718096;">현재 세션 제외 키워드:</span>', unsafe_allow_html=True)
        for i, kw in enumerate(st.session_state["admin_exclude_kws"]):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f'<span style="font-size:0.78rem;">{kw}</span>', unsafe_allow_html=True)
            if c2.button("✕", key=f"admin_del_kw_{i}"):
                st.session_state["admin_exclude_kws"].pop(i)
                st.rerun()


# ============================
# 분석 실행
# ============================
if run_btn:
    if stop_btn:
        st.warning("분석이 중지되었습니다.")
        st.stop()
    keywords_raw = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()][:3]
    if not keywords_raw:
        st.error("검색어를 최소 1개 입력해주세요."); st.stop()
    if not any([search_blog, search_cafe, search_yt]):
        st.error("채널을 하나 이상 선택해주세요."); st.stop()
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦습니다. 날짜를 확인해주세요."); st.stop()

    keywords = [build_naver_query(k) for k in keywords_raw]

    with st.spinner("KLUE-RoBERTa 모델 로드 중..."):
        model_r = load_roberta()

    if model_r is None:
        st.warning("⚠ KLUE-RoBERTa 로드 실패 — 룰베이스만으로 판정합니다.")
    else:
        st.markdown(
            '<div style="background:#F0FDF4;border:1px solid #A7F3D0;border-radius:8px;'
            'padding:0.6rem 1rem;font-size:0.82rem;color:#16A34A;font-weight:600;margin-bottom:0.5rem;">'
            '✅ KLUE-RoBERTa 모델 정상 로드 완료 (CPU 최적화)</div>',
            unsafe_allow_html=True
        )

    collect_tasks = []
    for kw in keywords:
        if search_blog: collect_tasks.append(("blog", kw, "블로그"))
        if search_cafe: collect_tasks.append(("cafe", kw, "카페"))
        if search_yt and YOUTUBE_API_KEY:
            collect_tasks.append(("yt", kw, "유튜브"))

    prog      = st.progress(0)
    prog_text = st.empty()
    all_items = []; collect_log = []

    def _fetch(task):
        tp, kw, label = task
        if tp == "blog": return label, kw, collect_naver_paged(kw, "blog", display_count)
        if tp == "cafe": return label, kw, collect_cafe_paged(kw, display_count)
        if tp == "yt":   return label, kw, search_youtube(kw, max_results=min(display_count, 50))
        return label, kw, []

    import concurrent.futures
    total_tasks = len(collect_tasks)
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch, t): t for t in collect_tasks}
        for fut in concurrent.futures.as_completed(futures):
            label, kw, items = fut.result()
            all_items.extend(items)
            collect_log.append(f"{label}/{kw}/{len(items)}건")
            done += 1
            prog.progress(done / max(total_tasks, 1))
            prog_text.markdown(f'<span style="font-size:0.78rem;color:#718096;">수집 중 {done}/{total_tasks} 완료</span>', unsafe_allow_html=True)

    prog.empty(); prog_text.empty()

    seen, unique_items = set(), []
    for item in all_items:
        lnk = item.get("link","")
        if lnk not in seen: seen.add(lnk); unique_items.append(item)

    before_rel = len(unique_items)
    unique_items = [
        it for it in unique_items
        if it.get("출처") == "카페" or is_daiso_related(it)
    ]
    rel_excluded = before_rel - len(unique_items)

    before_promo = len(unique_items)
    unique_items = [it for it in unique_items if not is_promotional(it)]
    promo_excluded = before_promo - len(unique_items)

    unique_items = [it for it in unique_items if not is_admin_excluded(it)]

    USIM_EXCLUDE_KW = [
        "유심","USIM","유심칩","유심카드","심카드","SIM카드",
        "통신사","SKT","KT","LGU+","알뜰폰","eSIM","이심",
        "매장 옆","매장앞","매장 앞","매장 옆","옆 매장","옆가게","옆 매장",
        "유심기변","유심 기변","유심교체","유심 교체","유심 변경","유심변경",
        "해외유심","해외 유심","로밍유심","로밍 유심","글로벌유심","글로벌 유심",
        "다이소유심","다이소 유심","다이소심카드","다이소 심카드",
    ]
    def is_usim_related(it):
        text = (clean_text(it.get("title","")) + " " + clean_text(it.get("description",""))).upper()
        return any(kw.upper() in text for kw in USIM_EXCLUDE_KW)

    before_usim  = len(unique_items)
    unique_items = [it for it in unique_items if not is_usim_related(it)]
    usim_excluded = before_usim - len(unique_items)

    filtered = filter_by_date(unique_items, start_date, end_date)
    if not filtered:
        st.warning("해당 기간에 결과가 없습니다. 날짜 범위나 검색어를 확인해주세요."); st.stop()

    notes = []
    if rel_excluded > 0:    notes.append(f"다이소 무관 <strong>{rel_excluded}</strong>건 제외")
    if promo_excluded > 0:  notes.append(f"홍보성 글 <strong>{promo_excluded}</strong>건 제외")
    if usim_excluded > 0:   notes.append(f"유심 관련 <strong>{usim_excluded}</strong>건 제외")
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

    results = []
    progress_bar = st.progress(0)
    status_text  = st.empty()

    BATCH   = 32
    total_f = len(filtered)

    for batch_start in range(0, total_f, BATCH):
        batch = filtered[batch_start: batch_start + BATCH]
        texts, metas = [], []
        for item in batch:
            src   = item.get("출처","")
            title = clean_text(item.get("title",""))
            desc  = clean_text(item.get("description",""))
            full  = (title + " " + desc)[:200]
            texts.append(full)
            metas.append((src, item, title))

        r_batch = model_r(texts, batch_size=BATCH, truncation=True, max_length=128) if model_r else [None]*len(texts)

        for idx, (full, (src, item, title)) in enumerate(zip(texts, metas)):
            sentiment, score = ensemble_sentiment(r_batch[idx], full, threshold)

            date_str = item.get("날짜","") if src == "유튜브" else (
                lambda dt: dt.strftime("%Y-%m-%d") if dt else ""
            )(parse_date(item))

            prod_code = extract_product_code(full)
            prod_name = match_product_name(prod_code)
            subcategory = extract_subcategory(full)
            price_mention = extract_price(full) if src != "유튜브" else ""

            results.append({
                "출처":    src,
                "검색어":  item.get("검색어",""),
                "소분류":  subcategory,
                "품번":    prod_code,
                "품명":    prod_name,
                "가격언급": price_mention,
                "title":  title,
                "link":   item.get("link",""),
                "날짜":   date_str,
                "감성":   sentiment,
                "확신도": score,
                "channel": item.get("channel","") or item.get("cafename",""),
                "views":   item.get("views",""),
                "likes":   item.get("likes",""),
                "comments":item.get("comments",""),
                "video_id":item.get("video_id",""),
            })

        done_so_far = min(batch_start + BATCH, total_f)
        progress_bar.progress(done_so_far / total_f)
        status_text.markdown(
            f'<span style="font-size:0.78rem;color:#718096;">AI 분석 중 {done_so_far} / {total_f} &nbsp;|&nbsp; KLUE-RoBERTa + 룰베이스</span>',
            unsafe_allow_html=True
        )

    progress_bar.empty(); status_text.empty()

    if EXCLUDE_SUBCATEGORIES:
        results = [r for r in results if not any(es in (r.get("소분류") or "") for es in EXCLUDE_SUBCATEGORIES)]

    # ── 분석 결과를 session_state에 저장 (sort/filter rerun 후에도 유지) ──
    st.session_state["analysis_results"] = results
    st.session_state["analysis_start_date"] = start_date
    st.session_state["analysis_end_date"] = end_date

    # ── 결과가 session_state에 있으면 항상 탭 렌더링 ──
    if "analysis_results" in st.session_state and st.session_state["analysis_results"]:
        results    = st.session_state["analysis_results"]
        start_date = st.session_state["analysis_start_date"]
        end_date   = st.session_state["analysis_end_date"]
        "📊 대시보드", "📝 블로그", "☕ 카페", "▶ 유튜브"]

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

    date_neg = {}
    for r in results:
        if r["감성"] == "부정" and r.get("날짜"):
            month = r["날짜"][:7]
            date_neg[month] = date_neg.get(month, 0) + 1

    with tab_dash:
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("↑")} <span style="font-size:0.95rem;font-weight:600;">분석 요약</span></div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for col, cls, lbl, val, pct, ic_txt in [
            (c1,"total","전체 수집",  str(total), "100%",                                    "전체"),
            (c2,"pos",  "긍정",      str(pos),   f"{round(pos/total*100) if total else 0}%","긍정"),
            (c3,"neg",  "부정",      str(neg),   f"{round(neg/total*100) if total else 0}%","부정"),
            (c4,"neu",  "중립",      str(neu),   f"{round(neu/total*100) if total else 0}%","중립"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card {cls}">
                    <div class="metric-label">
                        <span class="metric-icon {cls}" style="color:#FFFFFF !important;">{ic_txt}</span>
                        {lbl}
                    </div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-pct">{pct}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        d1, d2, d3 = st.columns(3)
        sub_u  = len(sub_cnt)
        code_u = len(set(r["품번"] for r in results if r.get("품번")))
        name_u = len(set(r["품명"] for r in results if r.get("품명")))
        for col, lbl, val in [(d1,"소분류 수",str(sub_u)),(d2,"품번 수",str(code_u)),(d3,"품명 수",str(name_u))]:
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center;padding:1rem 0.75rem;">
                    <div style="font-size:1.6rem;font-weight:700;color:#0066CC;font-family:'Inter',sans-serif;">{val}</div>
                    <div style="font-size:0.72rem;color:#718096;margin-top:0.2rem;font-weight:500;">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        date_pos = {}
        for r in results:
            if r["감성"] == "긍정" and r.get("날짜"):
                month = r["날짜"][:7]
                date_pos[month] = date_pos.get(month, 0) + 1

        all_months = sorted(set(list(date_neg.keys()) + list(date_pos.keys())))
        if all_months:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("월")} <span style="font-size:0.95rem;font-weight:600;">월별 긍정/부정 추이</span></div>', unsafe_allow_html=True)
            chart_data = []
            for m in all_months:
                chart_data.append({"월": m, "건수": date_pos.get(m, 0), "감성": "긍정"})
                chart_data.append({"월": m, "건수": date_neg.get(m, 0), "감성": "부정"})
            chart_df = pd.DataFrame(chart_data)
            chart = (
                alt.Chart(chart_df)
                .mark_line(point=True, strokeWidth=2.5)
                .encode(
                    x=alt.X("월:O", axis=alt.Axis(title="", labelAngle=0, labelFontSize=12)),
                    y=alt.Y("건수:Q", axis=alt.Axis(title="건수", titleFontSize=11)),
                    color=alt.Color("감성:N", scale=alt.Scale(domain=["긍정","부정"], range=["#16A34A","#DC2626"]), legend=alt.Legend(title=None)),
                    tooltip=[alt.Tooltip("월:O", title="월"), alt.Tooltip("감성:N", title="감성"), alt.Tooltip("건수:Q", title="건수")]
                )
                .properties(height=220)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=False, domain=False)
            )
            st.altair_chart(chart, use_container_width=True)

        col_top1, col_top2 = st.columns(2)
        with col_top1:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("분류")} <span style="font-size:0.95rem;font-weight:600;">소분류 TOP 10</span></div>', unsafe_allow_html=True)
            html = ""
            for rank, (name, count) in enumerate(sub_cnt.most_common(10), 1):
                cls = "r1" if rank == 1 else ""
                html += f'<div class="top-item"><div class="top-rank {cls}" style="color:{"#FFFFFF" if rank==1 else "var(--primary)"};">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>'
            empty_sub_html = "<span style='color:#718096;font-size:0.82rem;'>소분류 데이터 없음</span>"
            st.markdown(f'<div class="card">{html or empty_sub_html}</div>', unsafe_allow_html=True)

        with col_top2:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("품번")} <span style="font-size:0.95rem;font-weight:600;">주요 품번+품명 TOP 10</span></div>', unsafe_allow_html=True)
            html2 = ""
            for rank, (name, count) in enumerate(code_cnt.most_common(10), 1):
                cls = "r1" if rank == 1 else ""
                html2 += f'<div class="top-item"><div class="top-rank {cls}" style="color:{"#FFFFFF" if rank==1 else "var(--primary)"};">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>'
            empty_code_html = "<span style='color:#718096;font-size:0.82rem;'>품번 데이터 없음</span>"
            st.markdown(f'<div class="card">{html2 or empty_code_html}</div>', unsafe_allow_html=True)

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("부정")} <span style="font-size:0.95rem;font-weight:600;">주요 부정 글 목록</span></div>', unsafe_allow_html=True)
        neg_results = [r for r in results if r["감성"] == "부정"]
        if neg_results:
            for r in neg_results[:20]:
                _b    = SENT_BADGE.get(r["감성"], "")
                _sub  = ('<span class="badge-sub">🗂 ' + r["소분류"] + '</span>') if r.get("소분류") else ""
                _code = ('<span class="badge-sub">🔢 ' + r["품번"]   + '</span>') if r.get("품번")   else ""
                _name = ('<span>🏷 '  + r["품명"]   + '</span>') if r.get("품명")   else ""
                _badge = '<span class="' + _b + '">' + r["감성"] + ' ' + fmt_score(r["확신도"]) + '</span>'
                _title = r["title"] or "(제목 없음)"
                _html  = (
                    '<div class="result-card">'
                    '<div class="result-title">'
                    '<a href="' + r["link"] + '" target="_blank" style="color:#1A202C;text-decoration:none;">' + _title + '</a>'
                    '</div>'
                    '<div class="result-meta">'
                    '<span>📍 ' + r["출처"] + '</span>'
                    '<span>🔍 ' + r["검색어"] + '</span>'
                    '<span>📅 ' + r["날짜"] + '</span>'
                    + _sub + _code + _name + _badge +
                    '</div>'
                    '</div>'
                )
                st.markdown(_html, unsafe_allow_html=True)
        else:
            st.info("부정으로 분류된 글이 없습니다.")

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("↓")} <span style="font-size:0.95rem;font-weight:600;">결과 다운로드</span></div>', unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        with dl1:
            buf = create_excel(results, start_date, end_date)
            st.download_button("📥 EXCEL 다운로드", buf,
                f"ISSUE_{start_date}_{end_date}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        with dl2:
            csv = pd.DataFrame(results).to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSV 다운로드", csv.encode("utf-8-sig"),
                f"ISSUE_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

    def render_detail_tab(src_results, src_name):
        if not src_results:
            st.info(f"{src_name} 수집 결과가 없습니다."); return
        t  = len(src_results)
        p  = sum(1 for r in src_results if r["감성"]=="긍정")
        n  = sum(1 for r in src_results if r["감성"]=="부정")
        ne = sum(1 for r in src_results if r["감성"]=="중립")

        c1, c2, c3, c4 = st.columns(4)
        for col, cls, lbl, val, ic_txt in [
            (c1,"total","전체",str(t),"전체"),
            (c2,"pos","긍정",str(p),"긍정"),
            (c3,"neg","부정",str(n),"부정"),
            (c4,"neu","중립",str(ne),"중립"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card {cls}">
                    <div class="metric-label">
                        <span class="metric-icon {cls}" style="color:#FFFFFF !important;">{ic_txt}</span>{lbl}
                    </div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-pct">{round(int(val)/t*100) if t else 0}%</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        sort_opt = st.selectbox("정렬", ["부정 높은순", "부정 낮은순", "최신 날짜순", "오래된 날짜순"], key=f"sort_{src_name}", label_visibility="collapsed")
        if sort_opt == "부정 높은순":
            src_results = sorted(src_results, key=lambda x: x.get("확신도", 0) if x.get("감성") == "부정" else 0, reverse=True)
        elif sort_opt == "부정 낮은순":
            src_results = sorted(src_results, key=lambda x: x.get("확신도", 0) if x.get("감성") == "부정" else 100)
        elif sort_opt == "최신 날짜순":
            src_results = sorted(src_results, key=lambda x: x.get("날짜", ""), reverse=True)
        elif sort_opt == "오래된 날짜순":
            src_results = sorted(src_results, key=lambda x: x.get("날짜", ""))

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.75rem;">{icon("목록")} <span style="font-size:0.95rem;font-weight:600;">상세 결과 ({len(src_results)}건)</span></div>', unsafe_allow_html=True)

        PAGE_SIZE = 20
        total_pages = (len(src_results) - 1) // PAGE_SIZE + 1
        page_key = f"page_{src_name}"
        if page_key not in st.session_state:
            st.session_state[page_key] = 1
        current_page = st.session_state[page_key]

        start_idx = (current_page - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        page_results = src_results[start_idx:end_idx]

        for idx, r in enumerate(page_results):
            _b     = SENT_BADGE.get(r["감성"], "")
            _sub   = ('<span class="badge-sub">🗂 ' + r["소분류"]   + '</span>') if r.get("소분류")   else ""
            _code  = ('<span class="badge-sub">🔢 ' + r["품번"]     + '</span>') if r.get("품번")     else ""
            _name  = ('<span>🏷 '  + r["품명"]     + '</span>') if r.get("품명")     else ""
            _price = ('<span>💰 ' + r["가격언급"] + '</span>') if r.get("가격언급") else ""
            _badge = '<span class="' + _b + '">' + r["감성"] + ' ' + fmt_score(r["확신도"]) + '</span>'
            _title = r["title"] or "(제목 없음)"
            if st.session_state.get("admin_mode"):
                col_chk, col_card = st.columns([0.3, 9.7])
                with col_chk:
                    st.checkbox("", key=f"chk_{src_name}_{current_page}_{idx}", label_visibility="collapsed")
                with col_card:
                    st.markdown(
                        '<div class="result-card"><div class="result-title">'
                        '<a href="' + r["link"] + '" target="_blank" style="color:#1A202C;text-decoration:none;">' + _title + '</a>'
                        '</div><div class="result-meta">'
                        '<span>🔍 ' + r["검색어"] + '</span><span>📅 ' + r["날짜"] + '</span>'
                        + _sub + _code + _name + _price + _badge +
                        '</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="result-card"><div class="result-title">'
                    '<a href="' + r["link"] + '" target="_blank" style="color:#1A202C;text-decoration:none;">' + _title + '</a>'
                    '</div><div class="result-meta">'
                    '<span>🔍 ' + r["검색어"] + '</span><span>📅 ' + r["날짜"] + '</span>'
                    + _sub + _code + _name + _price + _badge +
                    '</div></div>', unsafe_allow_html=True)

        if st.session_state.get("admin_mode"):
            checked_urls = [page_results[i]["link"] for i in range(len(page_results))
                           if st.session_state.get(f"chk_{src_name}_{current_page}_{i}")]
            if st.button(f"🚫 선택한 글 제외 ({len(checked_urls)}건)", key=f"bulk_exc_{src_name}_{current_page}", disabled=len(checked_urls)==0):
                for url in checked_urls:
                    append_excluded_url_to_sheet(url, reason="관리자 일괄 제외")
                st.success(f"✅ {len(checked_urls)}건 제외 완료 → 시트 저장됨 (다음 분석 시 자동 필터링됩니다)")

        if total_pages > 1:
            pg_col1, pg_col2, pg_col3 = st.columns([1, 2, 1])
            with pg_col1:
                if st.button("◀ 이전", key=f"prev_{src_name}", disabled=(current_page <= 1)):
                    st.session_state[page_key] = current_page - 1
                    st.rerun()
            with pg_col2:
                st.markdown(f'<div style="text-align:center;font-size:0.85rem;color:#4A5568;padding:0.5rem;">{current_page} / {total_pages} 페이지</div>', unsafe_allow_html=True)
            with pg_col3:
                if st.button("다음 ▶", key=f"next_{src_name}", disabled=(current_page >= total_pages)):
                    st.session_state[page_key] = current_page + 1
                    st.rerun()

        src_csv = pd.DataFrame(src_results).to_csv(index=False, encoding="utf-8-sig")
        st.download_button(f"📥 {src_name} 전체 CSV 다운로드 ({len(src_results)}건)", src_csv.encode("utf-8-sig"),
            f"ISSUE_{src_name}_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

    with tab_blog:
        render_detail_tab([r for r in results if r["출처"]=="블로그"], "블로그")

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
            yc1, yc2, yc3, yc4 = st.columns(4)
            for col, cls, lbl, val, ic_txt in [
                (yc1,"total","영상",str(yt_t),"영상"),
                (yc2,"pos","긍정",str(yt_p),"긍정"),
                (yc3,"neg","부정",str(yt_n),"부정"),
                (yc4,"neu","중립",str(yt_ne),"중립"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="metric-card {cls}">
                        <div class="metric-label">
                            <span class="metric-icon {cls}" style="color:#FFFFFF !important;">{ic_txt}</span>{lbl}
                        </div>
                        <div class="metric-value">{val}</div>
                        <div class="metric-pct">{round(int(val)/yt_t*100) if yt_t else 0}%</div>
                    </div>""", unsafe_allow_html=True)

            yt_sort_opt = st.selectbox("정렬", ["조회수 높은순", "부정 높은순", "부정 낮은순", "최신 날짜순", "오래된 날짜순"], key="sort_yt", label_visibility="collapsed")
            if yt_sort_opt == "조회수 높은순":
                yt_sorted = sorted(yt_results, key=lambda x: x.get("views") or 0, reverse=True)
            elif yt_sort_opt == "부정 높은순":
                yt_sorted = sorted(yt_results, key=lambda x: x.get("확신도", 0) if x.get("감성") == "부정" else 0, reverse=True)
            elif yt_sort_opt == "부정 낮은순":
                yt_sorted = sorted(yt_results, key=lambda x: x.get("확신도", 0) if x.get("감성") == "부정" else 100)
            elif yt_sort_opt == "최신 날짜순":
                yt_sorted = sorted(yt_results, key=lambda x: x.get("날짜", ""), reverse=True)
            elif yt_sort_opt == "오래된 날짜순":
                yt_sorted = sorted(yt_results, key=lambda x: x.get("날짜", ""))
            else:
                yt_sorted = yt_results

            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("영상")} <span style="font-size:0.95rem;font-weight:600;">영상 목록 ({len(yt_results)}건)</span></div>', unsafe_allow_html=True)

            PAGE_SIZE_YT = 20
            total_pages_yt = (len(yt_sorted) - 1) // PAGE_SIZE_YT + 1
            yt_page_key = "page_유튜브"
            if yt_page_key not in st.session_state:
                st.session_state[yt_page_key] = 1
            current_page_yt = st.session_state[yt_page_key]
            start_yt = (current_page_yt - 1) * PAGE_SIZE_YT
            page_yt = yt_sorted[start_yt:start_yt + PAGE_SIZE_YT]

            for yt_idx, r in enumerate(page_yt):
                b = SENT_BADGE.get(r["감성"],"")
                views    = f"{r['views']:,}"    if isinstance(r.get("views"),int)    else "-"
                likes    = f"{r['likes']:,}"    if isinstance(r.get("likes"),int)    else "-"
                comments = f"{r['comments']:,}" if isinstance(r.get("comments"),int) else "-"
                _sub  = ('<span class="badge-sub">🗂 ' + r["소분류"] + '</span>') if r.get("소분류") else ""
                _code = ('<span class="badge-sub">🔢 ' + r["품번"]   + '</span>') if r.get("품번")   else ""
                _name = ('<span>🏷 '  + r["품명"]   + '</span>') if r.get("품명")   else ""
                _badge = f'<span class="{b}">{r["감성"]} {fmt_score(r["확신도"])}</span>'
                _card_html = (
                    '<div class="result-card"><div class="result-title">'
                    f'<a href="{r["link"]}" target="_blank" style="color:#1A202C;text-decoration:none;">{r["title"]}</a>'
                    '</div><div class="result-meta">'
                    f'<span>📺 {r.get("channel","")}</span>'
                    f'<span>📅 {r["날짜"]}</span>'
                    f'<span>▶ {views}</span><span>♥ {likes}</span><span>💬 {comments}</span>'
                    f'{_sub}{_code}{_name}{_badge}'
                    '</div></div>'
                )
                if st.session_state.get("admin_mode"):
                    col_chk, col_card = st.columns([0.3, 9.7])
                    with col_chk:
                        st.checkbox("", key=f"chk_yt_{current_page_yt}_{yt_idx}", label_visibility="collapsed")
                    with col_card:
                        st.markdown(_card_html, unsafe_allow_html=True)
                else:
                    st.markdown(_card_html, unsafe_allow_html=True)

            if st.session_state.get("admin_mode"):
                checked_yt_urls = [page_yt[i]["link"] for i in range(len(page_yt))
                                   if st.session_state.get(f"chk_yt_{current_page_yt}_{i}")]
                if st.button(f"🚫 선택한 글 제외 ({len(checked_yt_urls)}건)", key=f"bulk_exc_yt_{current_page_yt}", disabled=len(checked_yt_urls)==0):
                    for url in checked_yt_urls:
                        append_excluded_url_to_sheet(url, reason="관리자 일괄 제외")
                    st.success(f"✅ {len(checked_yt_urls)}건 제외 완료 → 시트 저장됨 (다음 분석 시 자동 필터링됩니다)")

            if total_pages_yt > 1:
                yp1, yp2, yp3 = st.columns([1, 2, 1])
                with yp1:
                    if st.button("◀ 이전", key="prev_yt", disabled=(current_page_yt <= 1)):
                        st.session_state[yt_page_key] = current_page_yt - 1
                        st.rerun()
                with yp2:
                    st.markdown(f'<div style="text-align:center;font-size:0.85rem;color:#4A5568;padding:0.5rem;">{current_page_yt} / {total_pages_yt} 페이지</div>', unsafe_allow_html=True)
                with yp3:
                    if st.button("다음 ▶", key="next_yt", disabled=(current_page_yt >= total_pages_yt)):
                        st.session_state[yt_page_key] = current_page_yt + 1
                        st.rerun()

            yt_csv = pd.DataFrame(yt_results).to_csv(index=False, encoding="utf-8-sig")
            st.download_button(f"📥 유튜브 전체 CSV 다운로드 ({len(yt_results)}건)", yt_csv.encode("utf-8-sig"),
                f"ISSUE_유튜브_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;border-top:1px solid #E2E8F0;margin-top:2rem;">
        <span style="font-size:0.75rem;color:#A0AEC0;">DAISO SNS ISSUE FINDER · KLUE-RoBERTa + 룰베이스 앙상블 · Created by 데이터분석팀</span>
    </div>
    """, unsafe_allow_html=True)
