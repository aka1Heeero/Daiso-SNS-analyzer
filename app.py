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
    page_title="DAISO SNS-LENS",
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
/* 달력 날짜 선택 input */
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
/* ── 날짜 입력 간격 축소 (3번 수정) ── */
[data-testid="stSidebar"] [data-testid="stDateInput"] {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] > label {
    display: none !important;
}
.date-label {
    font-size: 0.7rem;
    color: #718096;
    margin-bottom: 2px;
    display: block;
    line-height: 1.2;
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
.sb-hint { font-size: 0.68rem; color: var(--text3); margin-top: 0.15rem; display: block; line-height: 1.5; }

/* ── 채널 체크박스 인라인 (2번 수정) ── */
.channel-inline-row {
    display: flex; align-items: center; gap: 0.4rem;
    padding: 0.35rem 0; margin-bottom: 0.2rem;
}
.ch-icon {
    width: 22px; height: 22px; border-radius: 5px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; color: #FFFFFF !important;
    font-weight: 900; flex-shrink: 0;
}
.ch-naver   { background: #03C75A; }
.ch-youtube { background: #FF0000; }
.ch-label   { font-size: 0.82rem; font-weight: 500; color: var(--text); min-width: 36px; }

/* 체크박스를 인라인 아이콘 옆에 붙이기 위한 스타일 */
.channel-cb-wrap {
    display: flex; align-items: center; gap: 0; margin: 0;
}
.channel-cb-wrap .stCheckbox {
    margin: 0 !important; padding: 0 !important;
}
.channel-cb-wrap .stCheckbox > label {
    padding: 0 !important; gap: 0 !important; min-height: unset !important;
}
.channel-cb-wrap .stCheckbox > label > span:last-child {
    display: none !important;  /* 기본 라벨 텍스트 숨김 */
}

/* ── 숫자 입력 ── */
[data-testid="stNumberInput"] > div {
    border-radius: 8px !important;
}
[data-testid="stNumberInput"] button {
    color: var(--primary) !important;
}

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

/* ── 분석 시작 버튼 — 노란색, 굵고 크게 (5번 수정) ── */
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
#MainMenu, footer, header { visibility: hidden; }

/* 추가예정 뱃지 */
.badge-coming {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #F1F5F9; color: #64748B;
    border: 1px dashed #CBD5E1;
    padding: 0.35rem 0.75rem; border-radius: 6px;
    font-size: 0.78rem; font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


# ============================================== 비밀번호 인증
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="login-wrap">
        <div class="login-icon">🔵</div>
        <div class="login-title">DAISO SNS-LENS</div>
        <div class="login-sub">SNS 불만/감성 AI분석 시스템</div>
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

# ============================================== API키
NAVER_CLIENT_ID     = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
YOUTUBE_API_KEY     = st.secrets.get("YOUTUBE_API_KEY", "")


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
        return df
    except Exception as e:
        st.warning(f"⚠ 품명 DB 로드 실패: {e}")
        return pd.DataFrame(columns=["품번", "품명", "소분류"])

PRODUCT_DB = load_product_db()

def load_subcategories():
    if not PRODUCT_DB.empty and "소분류" in PRODUCT_DB.columns:
        return list(PRODUCT_DB["소분류"].dropna().unique())
    return []

SUBCATEGORIES = load_subcategories()


# ============================================== AI모델링 (앙상블)
@st.cache_resource
def load_electra():
    try:
        return pipeline("text-classification", model="snunlp/KR-ELECTRA-discriminator",
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
    "수량적음", "색이다름", "색상상이", "성능과장", "원산지 불명확", "색감차이",
    "과포장", "과점착", "색번짐", "이염",
]
POSITIVE_KW = [
    "좋아요","좋았","만족","추천","재구매","최고","훌륭","완벽","편리","예뻐",
    "가성비","합리적","대박","꿀템","강추","마음에 들","만족스럽","굿","짱"
]
LABEL_MAP = {
    "positive":"호평","pos":"호평","LABEL_2":"호평","호평":"호평",
    "negative":"악평","neg":"악평","LABEL_0":"악평","악평":"악평",
    "neutral":"중립","neu":"중립","LABEL_1":"중립","중립":"중립",
    "부정":"악평","긍정":"호평",
}

def rule_based(text: str):
    neg = sum(1 for kw in NEGATIVE_KW if kw in text)
    pos = sum(1 for kw in POSITIVE_KW if kw in text)
    if neg > pos:  return "악평", min(0.6 + neg * 0.07, 0.97)
    if pos > neg:  return "호평", min(0.55 + pos * 0.07, 0.97)
    return "중립", 0.50

def ai_ensemble(text: str, model_e, model_r) -> tuple:
    votes = {"호평": 0.0, "악평": 0.0, "중립": 0.0}
    electra_neg_score = 0.0
    if model_e:
        try:
            for it in model_e(text[:512])[0]:
                lbl = LABEL_MAP.get(it["label"])
                if lbl:
                    votes[lbl] += it["score"] * 1.6
                    if lbl == "악평": electra_neg_score = it["score"]
        except Exception: pass
    if model_r:
        try:
            for it in model_r(text[:512])[0]:
                lbl = LABEL_MAP.get(it["label"])
                if lbl: votes[lbl] += it["score"] * 1.0
        except Exception: pass
    rule_lbl, rule_sc = rule_based(text)
    votes[rule_lbl] += rule_sc * 0.6
    total = sum(votes.values())
    if total == 0: return "중립", 50.0
    best  = max(votes, key=votes.get)
    score = round(votes[best] / total * 100, 1)
    neg_kw_cnt = sum(1 for kw in NEGATIVE_KW if kw in text)
    if best == "악평" and not (electra_neg_score >= 0.60 and neg_kw_cnt >= 2):
        best = "중립"; score = max(score * 0.7, 45.0)
    return best, score


# ============================
# 네이버 검색
# ============================
def search_naver(query: str, search_type: str = "blog", display: int = 100) -> list:
    url     = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    params  = {"query": query, "display": min(display, 100), "sort": "date"}
    try:
        items = requests.get(url, headers=headers, params=params, timeout=10).json().get("items", [])
    except Exception:
        items = []
    label = "블로그" if search_type == "blog" else "지식인"
    for item in items: item["출처"] = label; item["검색어"] = query
    return items

def search_naver_cafe(query: str, display: int = 100) -> list:
    url     = "https://openapi.naver.com/v1/search/cafearticle.json"
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    params  = {"query": query, "display": min(display, 100), "sort": "date"}
    try:
        items = requests.get(url, headers=headers, params=params, timeout=10).json().get("items", [])
    except Exception:
        items = []
    result = []
    for item in items:
        cn = item.get("cafename", "")
        if "다이소" in cn or "DAISO" in cn.upper():
            item["출처"] = "카페"; item["검색어"] = query; item["channel"] = cn
            result.append(item)
    return result


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
        if len(ds) == 8: return datetime.strptime(ds, "%Y%m%d")
        return datetime.strptime(ds[:16], "%a, %d %b %Y")
    except: return None

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


# ============================
# 품번·소분류 추출
# ============================
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
    raw   = re.findall(r'\b(?:[A-Za-z]{1,4}[-_]?\d{3,7}|\d{3,6}[-_][A-Za-z]{1,4}|NO\.?\s?\d{2,6})\b', text)
    codes = [c for c in raw if not is_date_like(c)]
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
        row = PRODUCT_DB[PRODUCT_DB["품번"].astype(str) == c]
        if not row.empty: return row.iloc[0]["품명"]
    return ""


# ============================
# 엑셀 생성
# ============================
def create_excel(data: list, start_dt: date, end_dt: date) -> io.BytesIO:
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "DAISO SNS LENS"
    headers = ["출처","검색어","소분류","품번","품명","가격언급","제목","링크","날짜","감성","확신도(%)","채널/카페명","조회수","좋아요","댓글수"]
    ws.append(headers)
    hf   = openpyxl.styles.Font(bold=True, color="0066CC", name="Malgun Gothic")
    hfil = openpyxl.styles.PatternFill(start_color="E8F1FB", end_color="E8F1FB", fill_type="solid")
    hbrd = openpyxl.styles.Border(bottom=openpyxl.styles.Side(style="thin", color="0066CC"))
    for c in range(1, len(headers)+1):
        cell = ws.cell(1, c); cell.font = hf; cell.fill = hfil; cell.border = hbrd
        cell.alignment = openpyxl.styles.Alignment(horizontal="center")
    col_bg  = {"호평":"E8F5EE","악평":"FDEEEE","중립":"FFFBE8"}
    col_txt = {"호평":"16A34A","악평":"DC2626","중립":"CA8A04"}
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
SENT_BADGE = {"호평":"badge-pos","악평":"badge-neg","중립":"badge-neu"}

def icon(label: str) -> str:
    return f'<span class="section-title-icon">{label}</span>'


# ============================
# 앱 헤더 (1번 수정: 다이소 로고 SVG 포함)
# ============================
st.markdown("""
<div class="app-header">
    <div style="display:flex;align-items:center;gap:0.5rem;flex-shrink:0;">
        <!-- 다이소 로고: 파란 원 + DAISO 텍스트 워드마크 형태 -->
        <div style="
            width:48px; height:48px;
            background:#0066CC;
            border-radius:50%;
            display:flex; align-items:center; justify-content:center;
            flex-shrink:0;
            box-shadow:0 2px 6px rgba(0,102,204,0.35);
        ">
            <svg width="30" height="20" viewBox="0 0 60 38" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- D -->
                <path d="M0 2 H8 Q16 2 16 10 Q16 18 8 18 H0 Z
                         M4 5 V15 H8 Q12 15 12 10 Q12 5 8 5 Z" fill="#FFFFFF"/>
                <!-- A -->
                <path d="M18 18 L24 2 L30 18 M20.5 12 H27.5" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
                <!-- I -->
                <rect x="33" y="2" width="3.5" height="16" rx="1" fill="#FFFFFF"/>
                <!-- S -->
                <path d="M40 15 Q40 18 44 18 Q48 18 48 14.5 Q48 11 44 10 Q40 9 40 5.5 Q40 2 44 2 Q48 2 48 5"
                      stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
                <!-- O -->
                <ellipse cx="54" cy="10" rx="5" ry="8" stroke="#FFFFFF" stroke-width="3" fill="none"/>
            </svg>
        </div>
        <div style="
            font-size:1.35rem; font-weight:900;
            color:#0066CC; letter-spacing:0.12em;
            font-family:'Inter',sans-serif;
            line-height:1;
        ">DAISO</div>
    </div>
    <div style="width:1px;height:36px;background:#E2E8F0;margin:0 0.25rem;flex-shrink:0;"></div>
    <div>
        <div class="header-title">SNS-LENS · 불만 감성분석</div>
        <div class="header-sub">네이버 블로그 · 지식인 · 다이소 카페 · 유튜브 &nbsp;|&nbsp; KR-ELECTRA × KLUE-RoBERTa 앙상블</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================
# 사이드바
# ============================
with st.sidebar:
    # 로고 영역
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;padding-bottom:1rem;border-bottom:1px solid #E2E8F0;margin-bottom:0.25rem;">
        <div style="width:32px;height:32px;background:#0066CC;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,102,204,0.3);">
            <span style="color:#FFFFFF;font-size:0.65rem;font-weight:900;letter-spacing:0.05em;font-family:'Inter',sans-serif;">D</span>
        </div>
        <div>
            <div style="font-weight:700;font-size:0.95rem;color:#1A202C;">DAISO SNS-LENS</div>
            <div style="font-size:0.68rem;color:#718096;">Created by 데이터분석팀</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── ① 수집 채널 ──────────────────────────────────────
    st.markdown("""
    <div class="sb-section">
        <div class="sb-section-icon" style="color:#FFFFFF;">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/>
            </svg>
        </div>
        <span class="sb-section-text">수집 채널</span>
    </div>
    """, unsafe_allow_html=True)

    # ── 2번 수정: [아이콘][라벨][체크박스] 인라인 배치 ──
    # 블로그
    cb1, cb2 = st.columns([5, 1])
    with cb1:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.4rem;height:32px;">
            <div style="width:22px;height:22px;background:#03C75A;border-radius:5px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="color:#FFFFFF;font-size:0.6rem;font-weight:900;">N</span>
            </div>
            <span style="font-size:0.82rem;font-weight:500;color:#1A202C;">블로그</span>
        </div>""", unsafe_allow_html=True)
    with cb2:
        search_blog = st.checkbox("", value=True, key="cb_blog", label_visibility="collapsed")

    # 지식인
    cb3, cb4 = st.columns([5, 1])
    with cb3:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.4rem;height:32px;">
            <div style="width:22px;height:22px;background:#03C75A;border-radius:5px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="color:#FFFFFF;font-size:0.6rem;font-weight:900;">N</span>
            </div>
            <span style="font-size:0.82rem;font-weight:500;color:#1A202C;">지식인</span>
        </div>""", unsafe_allow_html=True)
    with cb4:
        search_kin = st.checkbox("", value=True, key="cb_kin", label_visibility="collapsed")

    # 카페
    cb5, cb6 = st.columns([5, 1])
    with cb5:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.4rem;height:32px;">
            <div style="width:22px;height:22px;background:#03C75A;border-radius:5px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="color:#FFFFFF;font-size:0.6rem;font-weight:900;">N</span>
            </div>
            <span style="font-size:0.82rem;font-weight:500;color:#1A202C;">카페</span>
        </div>""", unsafe_allow_html=True)
    with cb6:
        search_cafe = st.checkbox("", value=True, key="cb_cafe", label_visibility="collapsed")

    # 유튜브
    cb7, cb8 = st.columns([5, 1])
    with cb7:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.4rem;height:32px;">
            <div style="width:22px;height:22px;background:#FF0000;border-radius:5px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="#FFFFFF"><polygon points="5,3 19,12 5,21"/></svg>
            </div>
            <span style="font-size:0.82rem;font-weight:500;color:#1A202C;">유튜브</span>
        </div>""", unsafe_allow_html=True)
    with cb8:
        search_yt = st.checkbox("", value=True, key="cb_yt", label_visibility="collapsed")

    # ── ② 검색어 ────────────────────────────────────────────
    st.markdown("""
    <div class="sb-section">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
        </div>
        <span class="sb-section-text">검색어</span>
    </div>
    """, unsafe_allow_html=True)
    keywords_input = st.text_area("", value="다이소 상품불량\n다이소 불량\n다이소 별로",
                                  height=120, label_visibility="collapsed",
                                  placeholder="줄바꿈으로 구분 · 최대 10개")
    st.markdown('<span class="sb-hint">한 줄 = 검색어 1개 (OR 조건 수집, 최대 10개)</span>', unsafe_allow_html=True)

    # ── ③ 수집 기간 (간격 축소) ─────────────────────────────
    st.markdown("""
    <div class="sb-section">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
        </div>
        <span class="sb-section-text">수집 기간</span>
    </div>
    """, unsafe_allow_html=True)

    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown('<span class="date-label">시작일</span>', unsafe_allow_html=True)
        start_date = st.date_input("시작일", value=date(2025, 1, 1), label_visibility="collapsed", key="date_start")
    with dc2:
        st.markdown('<span class="date-label">종료일</span>', unsafe_allow_html=True)
        end_date = st.date_input("종료일", value=date.today(), label_visibility="collapsed", key="date_end")

    # ── ④ 수집 개수 (최대 5,000건으로 변경) ─────────────────
    st.markdown("""
    <div class="sb-section">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
                <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
        </div>
        <span class="sb-section-text">수집 개수</span>
    </div>
    """, unsafe_allow_html=True)
    display_count = st.number_input(
        "", min_value=10, max_value=5000, value=100, step=10,
        label_visibility="collapsed",
        help="키워드당 수집할 최대 건수 (10 ~ 5,000)"
    )
    st.markdown('<span class="sb-hint">키워드당 수집 건수 · 최소 10 / 최대 5,000<br>※ 네이버 API는 1회 최대 100건 제한 (자동 분할 수집)</span>', unsafe_allow_html=True)

    # ── ⑤ 악평 확신도 ───────────────────────────────────────
    st.markdown("""
    <div class="sb-section">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
        </div>
        <span class="sb-section-text">악평 확신도 임계값</span>
    </div>
    """, unsafe_allow_html=True)
    threshold = st.number_input(
        "", min_value=40, max_value=95, value=60, step=5,
        label_visibility="collapsed",
        help="AI가 이 수치 이상의 확신도로 부정 판정 시에만 악평으로 등록"
    )
    st.markdown("""
    <span class="sb-hint">
    · <b>40~55%</b> : 민감 — 불확실한 글도 악평 포함<br>
    · <b>60~70%</b> : 권장 — 명확한 불만 위주 수집<br>
    · <b>75%+</b> &nbsp;: 엄격 — 확실한 악평만 수집
    </span>
    """, unsafe_allow_html=True)

    # ── ⑥ 유튜브 댓글 — 추가예정 ────────────────────────────
    st.markdown("""
    <div class="sb-section">
        <div class="sb-section-icon">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
            </svg>
        </div>
        <span class="sb-section-text">유튜브 댓글 분석</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="badge-coming">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        추가 예정 기능입니다
    </div>
    <span class="sb-hint" style="margin-top:0.35rem;">유튜브 댓글 감성분석은 다음 버전에서 제공됩니다</span>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("분석 시작", use_container_width=True)
    # (6번 수정: expander 두 개 완전 제거)


# ============================
# 분석 실행
# ============================
if run_btn:
    keywords = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()][:10]
    if not keywords:
        st.error("검색어를 최소 1개 입력해주세요."); st.stop()
    if not any([search_blog, search_kin, search_cafe, search_yt]):
        st.error("채널을 하나 이상 선택해주세요."); st.stop()
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦습니다. 날짜를 확인해주세요."); st.stop()

    with st.spinner("AI 앙상블 모델 초기화 중... (KR-ELECTRA + KLUE-RoBERTa)"):
        model_e = load_electra()
        model_r = load_roberta()

    def collect_naver_paged(query, search_type, total):
        all_items = []
        fetched = 0
        start_idx = 1
        per_page = 100
        while fetched < total:
            url     = f"https://openapi.naver.com/v1/search/{search_type}.json"
            headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
            params  = {"query": query, "display": per_page, "start": start_idx, "sort": "date"}
            try:
                resp  = requests.get(url, headers=headers, params=params, timeout=10)
                items = resp.json().get("items", [])
            except Exception:
                break
            if not items: break
            label = "블로그" if search_type == "blog" else "지식인"
            for item in items: item["출처"] = label; item["검색어"] = query
            all_items.extend(items)
            fetched   += len(items)
            start_idx += per_page
            if len(items) < per_page: break
        return all_items[:total]

    def collect_cafe_paged(query, total):
        all_items = []
        fetched = 0; start_idx = 1; per_page = 100
        while fetched < total:
            url     = "https://openapi.naver.com/v1/search/cafearticle.json"
            headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
            params  = {"query": query, "display": per_page, "start": start_idx, "sort": "date"}
            try:
                items = requests.get(url, headers=headers, params=params, timeout=10).json().get("items", [])
            except Exception: break
            if not items: break
            for item in items:
                cn = item.get("cafename","")
                if "다이소" in cn or "DAISO" in cn.upper():
                    item["출처"] = "카페"; item["검색어"] = query; item["channel"] = cn
                    all_items.append(item)
            fetched   += len(items)
            start_idx += per_page
            if len(items) < per_page: break
        return all_items[:total]

    all_items, collect_log = [], []
    prog = st.progress(0)
    total_steps = len(keywords) * sum([search_blog, search_kin, search_cafe, search_yt])
    step = 0

    for kw in keywords:
        if search_blog:
            r = collect_naver_paged(kw, "blog", display_count)
            all_items.extend(r); collect_log.append(f"블로그/{kw}/{len(r)}건")
            step += 1; prog.progress(step / max(total_steps, 1))
        if search_kin:
            r = collect_naver_paged(kw, "kin", display_count)
            all_items.extend(r); collect_log.append(f"지식인/{kw}/{len(r)}건")
            step += 1; prog.progress(step / max(total_steps, 1))
        if search_cafe:
            r = collect_cafe_paged(kw, display_count)
            all_items.extend(r); collect_log.append(f"카페/{kw}/{len(r)}건")
            step += 1; prog.progress(step / max(total_steps, 1))
        if search_yt and YOUTUBE_API_KEY:
            r = search_youtube(kw, max_results=min(display_count, 50))
            all_items.extend(r); collect_log.append(f"유튜브/{kw}/{len(r)}건")
            step += 1; prog.progress(step / max(total_steps, 1))
    prog.empty()

    seen, unique_items = set(), []
    for item in all_items:
        lnk = item.get("link","")
        if lnk not in seen: seen.add(lnk); unique_items.append(item)

    USIM_EXCLUDE_KW = [
        "유심","USIM","유심칩","유심카드","심카드","SIM카드",
        "통신사","SKT","KT","LGU+","알뜰폰","eSIM","이심",
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

    usim_note = f" &nbsp;·&nbsp; 유심 관련 <strong>{usim_excluded}</strong>건 제외" if usim_excluded > 0 else ""
    st.markdown(f"""
    <div class="card" style="border-left:3px solid #0066CC;">
        <span style="font-size:0.85rem;color:#0066CC;font-weight:600;">
        ✅ 수집 완료 — 총 <strong>{len(filtered)}</strong>건 (중복 제거 후){usim_note}
        </span><br>
        <span style="font-size:0.72rem;color:#718096;">{' &nbsp;|&nbsp; '.join(collect_log)}</span>
    </div>
    """, unsafe_allow_html=True)

    results = []
    progress_bar = st.progress(0)
    status_text  = st.empty()

    for i, item in enumerate(filtered):
        src   = item.get("출처","")
        title = clean_text(item.get("title",""))
        desc  = clean_text(item.get("description",""))
        full  = title + " " + desc

        sentiment, score = ai_ensemble(full, model_e, model_r)
        if score < threshold and sentiment != "중립":
            sentiment = "중립"

        date_str = item.get("날짜","") if src == "유튜브" else (
            lambda dt: dt.strftime("%Y-%m-%d") if dt else ""
        )(parse_date(item))

        prod_code = extract_product_code(full) if src != "유튜브" else ""
        prod_name = match_product_name(prod_code)

        results.append({
            "출처":    src, "검색어": item.get("검색어",""),
            "소분류":  extract_subcategory(full),
            "품번":    prod_code, "품명": prod_name,
            "가격언급":extract_price(full) if src != "유튜브" else "",
            "title":  title, "link": item.get("link",""),
            "날짜":   date_str, "감성": sentiment, "확신도": score,
            "channel":item.get("channel","") or item.get("cafename",""),
            "views":  item.get("views",""), "likes": item.get("likes",""),
            "comments":item.get("comments",""), "video_id":item.get("video_id",""),
        })

        progress_bar.progress((i+1)/len(filtered))
        status_text.markdown(f'<span style="font-size:0.78rem;color:#718096;">분석 중 {i+1} / {len(filtered)}</span>', unsafe_allow_html=True)

    progress_bar.empty(); status_text.empty()

    tab_dash, tab_blog, tab_kin, tab_cafe, tab_yt = st.tabs([
        "📊 대시보드", "📝 블로그", "💬 지식인", "☕ 카페", "▶ 유튜브"
    ])

    total = len(results)
    pos   = sum(1 for r in results if r["감성"]=="호평")
    neg   = sum(1 for r in results if r["감성"]=="악평")
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
        if r["감성"] == "악평" and r.get("날짜"):
            month = r["날짜"][:7]
            date_neg[month] = date_neg.get(month, 0) + 1

    with tab_dash:
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("↑")} <span style="font-size:0.95rem;font-weight:600;">분석 요약</span></div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for col, cls, lbl, val, pct, ic_txt in [
            (c1,"total","전체 수집",  str(total), "100%",                                    "전체"),
            (c2,"pos",  "호평",      str(pos),   f"{round(pos/total*100) if total else 0}%","호평"),
            (c3,"neg",  "악평",      str(neg),   f"{round(neg/total*100) if total else 0}%","악평"),
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

        if date_neg:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("월")} <span style="font-size:0.95rem;font-weight:600;">월별 악평 건수</span></div>', unsafe_allow_html=True)
            chart_df = pd.DataFrame(list(date_neg.items()), columns=["월","악평수"]).sort_values("월")
            chart = (
                alt.Chart(chart_df)
                .mark_bar(color="#0066CC", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("월:O", axis=alt.Axis(title="", labelAngle=0, labelFontSize=12)),
                    y=alt.Y("악평수:Q", axis=alt.Axis(title="악평 건수", titleFontSize=11)),
                    tooltip=[alt.Tooltip("월:O", title="월"), alt.Tooltip("악평수:Q", title="건수")]
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
            st.markdown(f'<div class="card">{html or "<span style=\'color:#718096;font-size:0.82rem;\'>소분류 데이터 없음</span>"}</div>', unsafe_allow_html=True)

        with col_top2:
            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("품번")} <span style="font-size:0.95rem;font-weight:600;">주요 품번+품명 TOP 10</span></div>', unsafe_allow_html=True)
            html2 = ""
            for rank, (name, count) in enumerate(code_cnt.most_common(10), 1):
                cls = "r1" if rank == 1 else ""
                html2 += f'<div class="top-item"><div class="top-rank {cls}" style="color:{"#FFFFFF" if rank==1 else "var(--primary)"};">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>'
            st.markdown(f'<div class="card">{html2 or "<span style=\'color:#718096;font-size:0.82rem;\'>품번 데이터 없음</span>"}</div>', unsafe_allow_html=True)

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("악평")} <span style="font-size:0.95rem;font-weight:600;">주요 악평 글 목록</span></div>', unsafe_allow_html=True)
        neg_results = [r for r in results if r["감성"] == "악평"]
        if neg_results:
            for r in neg_results[:20]:
                b = SENT_BADGE.get(r["감성"],"")
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-title">
                        <a href="{r['link']}" target="_blank" style="color:#1A202C;text-decoration:none;">{r['title'] or '(제목 없음)'}</a>
                    </div>
                    <div class="result-meta">
                        <span>📍 {r['출처']}</span>
                        <span>🔍 {r['검색어']}</span>
                        <span>📅 {r['날짜']}</span>
                        {'<span>🗂 ' + r['소분류'] + '</span>' if r.get('소분류') else ''}
                        {'<span>🔢 ' + r['품번'] + '</span>' if r.get('품번') else ''}
                        <span><span class="{b}">{r['감성']} {r['확신도']}%</span></span>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("악평으로 분류된 글이 없습니다.")

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("↓")} <span style="font-size:0.95rem;font-weight:600;">결과 다운로드</span></div>', unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        with dl1:
            buf = create_excel(results, start_date, end_date)
            st.download_button("📥 EXCEL 다운로드", buf,
                f"LENS_{start_date}_{end_date}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        with dl2:
            csv = pd.DataFrame(results).to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSV 다운로드", csv.encode("utf-8-sig"),
                f"LENS_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

    def render_detail_tab(src_results, src_name):
        if not src_results:
            st.info(f"{src_name} 수집 결과가 없습니다."); return
        t  = len(src_results)
        p  = sum(1 for r in src_results if r["감성"]=="호평")
        n  = sum(1 for r in src_results if r["감성"]=="악평")
        ne = sum(1 for r in src_results if r["감성"]=="중립")

        c1,c2,c3,c4 = st.columns(4)
        for col, cls, lbl, val, ic_txt in [
            (c1,"total","전체",str(t),"전체"),
            (c2,"pos","호평",str(p),"호평"),
            (c3,"neg","악평",str(n),"악평"),
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

        kw_stats = {}
        for r in src_results:
            kw = r.get("검색어","")
            kw_stats.setdefault(kw, {"호평":0,"악평":0,"중립":0})
            kw_stats[kw][r["감성"]] += 1
        kw_rows = []
        for kw, s in kw_stats.items():
            t2 = sum(s.values())
            kw_rows.append({"검색어":kw,"호평":s["호평"],"악평":s["악평"],"중립":s["중립"],
                            "합계":t2,"악평률(%)":round(s["악평"]/t2*100,1) if t2 else 0})
        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0 0 0.75rem;">{icon("검색")} <span style="font-size:0.95rem;font-weight:600;">검색어별 분포</span></div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(kw_rows), use_container_width=True, hide_index=True, height=160)

        st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.75rem;">{icon("목록")} <span style="font-size:0.95rem;font-weight:600;">상세 결과</span></div>', unsafe_allow_html=True)
        for r in src_results:
            b = SENT_BADGE.get(r["감성"],"")
            st.markdown(f"""
            <div class="result-card">
                <div class="result-title">
                    <a href="{r['link']}" target="_blank" style="color:#1A202C;text-decoration:none;">{r['title'] or '(제목 없음)'}</a>
                </div>
                <div class="result-meta">
                    <span>🔍 {r['검색어']}</span>
                    <span>📅 {r['날짜']}</span>
                    {'<span>🗂 ' + r['소분류'] + '</span>' if r.get('소분류') else ''}
                    {'<span>🔢 ' + r['품번'] + '</span>' if r.get('품번') else ''}
                    {'<span>🏷 ' + r['품명'] + '</span>' if r.get('품명') else ''}
                    {'<span>💰 ' + r['가격언급'] + '</span>' if r.get('가격언급') else ''}
                    <span><span class="{b}">{r['감성']} {r['확신도']}%</span></span>
                </div>
            </div>""", unsafe_allow_html=True)

        src_csv = pd.DataFrame(src_results).to_csv(index=False, encoding="utf-8-sig")
        st.download_button(f"📥 {src_name} CSV 다운로드", src_csv.encode("utf-8-sig"),
            f"LENS_{src_name}_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

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
            yt_p  = sum(1 for r in yt_results if r["감성"]=="호평")
            yt_n  = sum(1 for r in yt_results if r["감성"]=="악평")
            yt_ne = sum(1 for r in yt_results if r["감성"]=="중립")
            yc1,yc2,yc3,yc4 = st.columns(4)
            for col, cls, lbl, val, ic_txt in [
                (yc1,"total","영상",str(yt_t),"영상"),
                (yc2,"pos","호평",str(yt_p),"호평"),
                (yc3,"neg","악평",str(yt_n),"악평"),
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

            st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem;">{icon("영상")} <span style="font-size:0.95rem;font-weight:600;">영상 목록 (조회수 순)</span></div>', unsafe_allow_html=True)
            for r in sorted(yt_results, key=lambda x: x.get("views") or 0, reverse=True)[:20]:
                b = SENT_BADGE.get(r["감성"],"")
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
                        <span><span class="{b}">{r['감성']} {r['확신도']}%</span></span>
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown("""
            <div style="margin-top:1.5rem;padding:1.25rem 1.5rem;background:#F8FAFC;border:1.5px dashed #CBD5E1;border-radius:10px;text-align:center;">
                <div style="font-size:0.9rem;font-weight:600;color:#64748B;margin-bottom:0.3rem;">💬 유튜브 댓글 감성분석</div>
                <div class="badge-coming" style="display:inline-flex;">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    추가 예정 기능입니다
                </div>
                <div style="font-size:0.75rem;color:#94A3B8;margin-top:0.5rem;">다음 버전에서 제공될 예정입니다</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;border-top:1px solid #E2E8F0;margin-top:2rem;">
        <span style="font-size:0.75rem;color:#A0AEC0;">DAISO SNS-LENS · KR-ELECTRA × KLUE-RoBERTa Ensemble · Created by 데이터분석팀</span>
    </div>
    """, unsafe_allow_html=True)
