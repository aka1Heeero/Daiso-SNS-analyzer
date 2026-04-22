import streamlit as st
import requests
import openpyxl
import re
import io
import time
import gspread
import pandas as pd
import altair as alt
from datetime import datetime
from google.oauth2.service_account import Credentials
from transformers import pipeline
from collections import Counter

# ============================
# 페이지 설정
# ============================
st.set_page_config(
    page_title="DAISO LENS AI 고객 불만 분석",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# CSS — 클린 화이트 + 블루 포인트
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

/* 사이드바 */
[data-testid="stSidebar"] {
    background: var(--bg-white) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important;
}
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.12) !important;
}

/* 헤더 */
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
    font-size: 1.1rem; color: white; flex-shrink: 0;
}
.header-title {
    font-size: 1.25rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.01em;
}
.header-sub {
    font-size: 0.78rem; color: var(--text3);
    margin-top: 0.1rem;
}

/* 카드 */
.card {
    background: var(--bg-white);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}
.card-title {
    font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--text3); margin-bottom: 0.75rem;
    display: flex; align-items: center; gap: 0.4rem;
}
.card-title-icon {
    width: 20px; height: 20px;
    background: var(--primary);
    border-radius: 5px;
    display: inline-flex; align-items: center; justify-content: center;
    color: white; font-size: 0.65rem;
}

/* 메트릭 카드 */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
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
    display: flex; align-items: center; gap: 0.4rem;
}
.metric-icon {
    width: 22px; height: 22px; background: var(--primary);
    border-radius: 6px; display: inline-flex;
    align-items: center; justify-content: center;
    color: white; font-size: 0.7rem;
}
.metric-icon.pos { background: var(--pos); }
.metric-icon.neg { background: var(--neg); }
.metric-icon.neu { background: var(--neu); }
.metric-value {
    font-family: 'Inter', sans-serif; font-size: 2.2rem;
    font-weight: 600; color: var(--text); line-height: 1;
}
.metric-pct { font-size: 0.78rem; color: var(--text3); margin-top: 0.3rem; }

/* 섹션 타이틀 */
.section-title {
    font-size: 0.95rem; font-weight: 600; color: var(--text);
    margin: 1.5rem 0 0.75rem;
    display: flex; align-items: center; gap: 0.5rem;
}
.section-title-icon {
    width: 24px; height: 24px; background: var(--primary);
    border-radius: 6px; display: inline-flex;
    align-items: center; justify-content: center;
    color: white; font-size: 0.75rem; flex-shrink: 0;
}

/* 감성 뱃지 */
.badge-pos { background: var(--pos-bg); color: var(--pos); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neg { background: var(--neg-bg); color: var(--neg); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.badge-neu { background: var(--neu-bg); color: var(--neu); padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }

/* TOP 아이템 */
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
.top-rank.r1 { background: var(--primary); color: white; }
.top-name { flex: 1; font-size: 0.85rem; color: var(--text); }
.top-count {
    font-size: 0.78rem; font-weight: 600; color: var(--primary);
    background: var(--primary-lt); padding: 2px 8px; border-radius: 20px;
}

/* 결과 행 카드 */
.result-card {
    background: var(--bg-white); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.5rem;
    box-shadow: var(--shadow); transition: box-shadow 0.2s;
}
.result-card:hover { box-shadow: var(--shadow-md); }
.result-title { font-size: 0.9rem; font-weight: 500; color: var(--text); margin-bottom: 0.4rem; }
.result-meta { font-size: 0.75rem; color: var(--text3); display: flex; gap: 0.75rem; flex-wrap: wrap; }
.result-meta span { display: flex; align-items: center; gap: 0.2rem; }

/* 로그인 */
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
    font-size: 1.4rem; color: white;
}
.login-title {
    font-size: 1.3rem; font-weight: 700; color: var(--text);
    margin-bottom: 0.25rem;
}
.login-sub { font-size: 0.82rem; color: var(--text3); margin-bottom: 1.5rem; }

/* 사이드바 라벨 */
.sb-label {
    font-size: 0.72rem; font-weight: 600; color: var(--text2);
    text-transform: uppercase; letter-spacing: 0.06em;
    margin: 1rem 0 0.3rem; display: block;
}
.sb-hint { font-size: 0.7rem; color: var(--text3); margin-top: 0.2rem; display: block; }

/* 진행바 */
.stProgress > div > div > div > div {
    background: var(--primary) !important; border-radius: 4px !important;
}
.stProgress > div > div > div {
    background: var(--border) !important; border-radius: 4px !important; height: 6px !important;
}

/* 버튼 */
.stButton > button {
    background: var(--primary) !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important; font-weight: 500 !important;
    padding: 0.55rem 1.25rem !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #0052A3 !important;
    box-shadow: 0 4px 12px rgba(0,102,204,0.3) !important;
}
.stDownloadButton > button {
    background: var(--bg-white) !important; color: var(--primary) !important;
    border: 1.5px solid var(--primary) !important; border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.875rem !important; font-weight: 500 !important;
    width: 100% !important;
}
.stDownloadButton > button:hover {
    background: var(--primary-lt) !important;
}

/* 탭 */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid var(--border) !important;
    gap: 0 !important;
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

/* 구분선 */
hr { border: none; border-top: 1px solid var(--border) !important; margin: 1rem 0 !important; }

/* 체크박스 */
.stCheckbox > label { font-size: 0.875rem !important; }

/* 데이터프레임 */
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; }

/* 슬라이더 */
.stSlider > div > div > div > div { background: var(--primary) !important; }

/* 알림 */
.stAlert { border-radius: 8px !important; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================
# 비밀번호 인증
# ============================
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="login-wrap">
        <div class="login-icon">🔵</div>
        <div class="login-title">LENS</div>
        <div class="login-sub">불만 SNS 감성분석 시스템</div>
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


# ============================
# API 키
# ============================
NAVER_CLIENT_ID     = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
YOUTUBE_API_KEY     = st.secrets.get("YOUTUBE_API_KEY", "")


# ============================
# Google Sheets — 품명 DB 로드
# ============================
@st.cache_data(ttl=3600)
def load_product_db():
    """
    Google Sheets에서 품번/품명/소분류 DataFrame을 로드.
    secrets.toml에 [gcp_service_account] 및 GSHEET_URL 필요.
    """
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        gc   = gspread.authorize(creds)
        sh   = gc.open_by_url(st.secrets["GSHEET_URL"])
        df   = pd.DataFrame(sh.sheet1.get_all_records())
        # 컬럼명 정규화
        df.columns = [c.strip() for c in df.columns]
        return df   # 품번 | 품명 | 소분류
    except Exception as e:
        st.warning(f"⚠ 품명 DB 로드 실패 (Google Sheets 미연결): {e}")
        return pd.DataFrame(columns=["품번", "품명", "소분류"])

PRODUCT_DB = load_product_db()

# ============================
# 소분류 목록 — Google Sheets에서 자동 추출
# ============================
def load_subcategories():
    if not PRODUCT_DB.empty and "소분류" in PRODUCT_DB.columns:
        return list(PRODUCT_DB["소분류"].dropna().unique())
    return []

SUBCATEGORIES = load_subcategories()


# ============================
# AI 앙상블 모델 (3종)
# ============================
@st.cache_resource
def load_electra():
    """1순위: KR-ELECTRA — 한국어 소비자 리뷰 최적화"""
    try:
        return pipeline(
            "text-classification",
            model="snunlp/KR-ELECTRA-discriminator",
            truncation=True, max_length=512, top_k=None, device=-1
        )
    except Exception:
        return None

@st.cache_resource
def load_roberta():
    """2순위: KLUE-RoBERTa — 한국어 감성 fine-tuned"""
    try:
        return pipeline(
            "text-classification",
            model="Chamsol/klue-roberta-sentiment-classification",
            truncation=True, max_length=512, top_k=None, device=-1
        )
    except Exception:
        return None


# ============================
# 키워드 룰베이스
# ============================
NEGATIVE_KW = [
    "불만","짜증","별로","최악","실망","환불","불량","교환","이상해","형편없",
    "쓰레기","구려","나빠","고장","터졌","망가","깨졌","불편","아쉬워","위험",
    "조심","주의","문제","하자","뜯겨","냄새","오염","불결","지저분","더럽",
    "싸구려","허접","대충","클레임","AS","환급","반품","재구매 안","비추","별점 1",
    "별점1","1점","속았","낚였","사기","뻥","가짜","품질 나쁜","품질이 나쁜",
    "뚜껑이 안","뚜껑이 깨","잘 안 돼","안 되는","못 쓰겠","못써","쓸모없"
]
POSITIVE_KW = [
    "좋아요","좋았","만족","추천","재구매","최고","훌륭","완벽","편리","예뻐",
    "가성비","합리적","대박","꿀템","강추","마음에 들","만족스럽","굿","짱"
]

LABEL_MAP = {
    # KR-ELECTRA 레이블
    "positive":"호평","pos":"호평","LABEL_2":"호평","호평":"호평",
    "negative":"악평","neg":"악평","LABEL_0":"악평","악평":"악평",
    "neutral":"중립","neu":"중립","LABEL_1":"중립","중립":"중립",
    # KLUE-RoBERTa 레이블 (0=부정,1=중립,2=긍정 또는 문자열)
    "부정":"악평","긍정":"호평",
}

def rule_based(text: str):
    neg = sum(1 for kw in NEGATIVE_KW if kw in text)
    pos = sum(1 for kw in POSITIVE_KW if kw in text)
    if neg > pos:   return "악평", min(0.6 + neg * 0.07, 0.97)
    if pos > neg:   return "호평", min(0.55 + pos * 0.07, 0.97)
    return "중립", 0.50

def ai_ensemble(text: str, model_e, model_r) -> tuple:
    """
    앙상블 가중치:
      KR-ELECTRA  × 1.6  (메인)
      KLUE-RoBERTa × 1.0  (보조)
      룰베이스     × 0.6  (보정)

    악평 확정 조건:
      ELECTRA 부정 60% 이상 AND 네거티브 키워드 2개 이상
      → 과검출 방지 (요구사항 4번)
    """
    votes = {"호평": 0.0, "악평": 0.0, "중립": 0.0}
    electra_neg_score = 0.0

    if model_e:
        try:
            for it in model_e(text[:512])[0]:
                lbl = LABEL_MAP.get(it["label"])
                if lbl:
                    votes[lbl] += it["score"] * 1.6
                    if lbl == "악평":
                        electra_neg_score = it["score"]
        except Exception:
            pass

    if model_r:
        try:
            for it in model_r(text[:512])[0]:
                lbl = LABEL_MAP.get(it["label"])
                if lbl:
                    votes[lbl] += it["score"] * 1.0
        except Exception:
            pass

    rule_lbl, rule_sc = rule_based(text)
    votes[rule_lbl] += rule_sc * 0.6

    total = sum(votes.values())
    if total == 0:
        return "중립", 50.0

    best  = max(votes, key=votes.get)
    score = round(votes[best] / total * 100, 1)

    # ── 과검출 방지 로직 ──────────────────────────────────
    neg_kw_cnt = sum(1 for kw in NEGATIVE_KW if kw in text)
    # 악평으로 판정되려면: ELECTRA 부정 ≥60% AND 네거티브 키워드 ≥2개
    if best == "악평" and not (electra_neg_score >= 0.60 and neg_kw_cnt >= 2):
        best  = "중립"
        score = max(score * 0.7, 45.0)

    return best, score


# ============================
# 네이버 검색
# ============================
def search_naver(query: str, search_type: str = "blog", display: int = 100) -> list:
    url     = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    params  = {"query": query, "display": display, "sort": "date"}
    try:
        resp  = requests.get(url, headers=headers, params=params, timeout=10)
        items = resp.json().get("items", [])
    except Exception:
        items = []
    label = "블로그" if search_type == "blog" else "지식인"
    for item in items:
        item["출처"] = label
        item["검색어"] = query
    return items

def search_naver_cafe(query: str, display: int = 100) -> list:
    url     = "https://openapi.naver.com/v1/search/cafearticle.json"
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    params  = {"query": query, "display": display, "sort": "date"}
    try:
        resp  = requests.get(url, headers=headers, params=params, timeout=10)
        items = resp.json().get("items", [])
    except Exception:
        items = []
    result = []
    for item in items:
        cafe_name = item.get("cafename", "")
        if "다이소" in cafe_name or "DAISO" in cafe_name.upper():
            item["출처"]   = "카페"
            item["검색어"] = query
            item["channel"] = cafe_name
            result.append(item)
    return result


# ============================
# YouTube
# ============================
def search_youtube(query: str, max_results: int = 30) -> list:
    if not YOUTUBE_API_KEY:
        return []
    try:
        resp = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "key": YOUTUBE_API_KEY, "q": query, "part": "snippet",
            "type": "video", "maxResults": min(max_results, 50),
            "order": "date", "relevanceLanguage": "ko", "regionCode": "KR"
        }, timeout=10)
        data  = resp.json()
    except Exception:
        return []
    if "error" in data:
        return []
    items     = data.get("items", [])
    video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
    stats_map = {}
    if video_ids:
        try:
            sr = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
                "key": YOUTUBE_API_KEY, "id": ",".join(video_ids), "part": "statistics"
            }, timeout=10)
            for sv in sr.json().get("items", []):
                stats_map[sv["id"]] = sv.get("statistics", {})
        except Exception:
            pass
    results = []
    for item in items:
        vid_id  = item.get("id", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        stats   = stats_map.get(vid_id, {})
        pub_raw = snippet.get("publishedAt", "")
        try:
            pub_dt  = datetime.strptime(pub_raw[:10], "%Y-%m-%d")
            pub_str = pub_dt.strftime("%Y-%m-%d")
        except Exception:
            pub_dt = None; pub_str = pub_raw[:10]
        results.append({
            "출처": "유튜브", "검색어": query, "video_id": vid_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", "")[:300],
            "channel": snippet.get("channelTitle", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "link": f"https://www.youtube.com/watch?v={vid_id}",
            "날짜": pub_str, "pub_dt": pub_dt,
            "views":    int(stats.get("viewCount",    0) or 0),
            "likes":    int(stats.get("likeCount",    0) or 0),
            "comments": int(stats.get("commentCount", 0) or 0),
        })
    return results

def fetch_youtube_comments(video_id: str, max_results: int = 30) -> list:
    if not YOUTUBE_API_KEY:
        return []
    try:
        resp = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params={
            "key": YOUTUBE_API_KEY, "videoId": video_id, "part": "snippet",
            "maxResults": max_results, "order": "relevance", "textFormat": "plainText"
        }, timeout=10)
        data = resp.json()
    except Exception:
        return []
    if "error" in data:
        return []
    comments = []
    for item in data.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "text":      top.get("textDisplay", ""),
            "likes":     top.get("likeCount", 0),
            "published": top.get("publishedAt", "")[:10]
        })
    return comments


# ============================
# 날짜 파싱 & 필터
# ============================
def parse_date(item: dict):
    ds = item.get("postdate") or item.get("pubDate", "")
    try:
        if len(ds) == 8:
            return datetime.strptime(ds, "%Y%m%d")
        return datetime.strptime(ds[:16], "%a, %d %b %Y")
    except Exception:
        return None

def filter_by_date(items: list, start: str, end: str) -> list:
    s = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end,   "%Y%m%d")
    result = []
    for item in items:
        dt = item.get("pub_dt") if item.get("출처") == "유튜브" else parse_date(item)
        if dt and s <= dt <= e:
            result.append(item)
    return result

def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    return text.strip()


# ============================
# 품번 추출 (날짜형 제외)
# ============================
DATE_PATS = [
    r'\b20\d{6}\b', r'\b\d{4}[-./]\d{2}[-./]\d{2}\b',
    r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b',
    r'\b\d{4}년\s*\d{1,2}월', r'\b\d{1,2}월\s*\d{1,2}일',
]
def is_date_like(token: str) -> bool:
    for p in DATE_PATS:
        if re.fullmatch(p, token.strip()):
            return True
    return bool(re.fullmatch(r'\d{6,8}', token.strip()))

def extract_product_code(text: str) -> str:
    raw   = re.findall(r'\b(?:[A-Za-z]{1,4}[-_]?\d{3,7}|\d{3,6}[-_][A-Za-z]{1,4}|NO\.?\s?\d{2,6})\b', text)
    codes = [c for c in raw if not is_date_like(c)]
    return ", ".join(dict.fromkeys(codes)) if codes else ""

def extract_price(text: str) -> str:
    prices = re.findall(r'\d{1,3}(?:,\d{3})*원', text)
    return ", ".join(dict.fromkeys(prices)) if prices else ""


# ============================
# 소분류 매칭 — Lv.2.5 (1→2→3차 단계별)
# ============================
# 동의어 사전 (필요시 확장)
SYNONYM_MAP = {
    "꽂이":    "홀더", "홀더":    "꽂이",
    "수납":    "정리", "정리":    "수납",
    "바구니":  "수납함", "수납함": "바구니",
    "케이스":  "커버", "커버":    "케이스",
    "그릇":    "용기", "용기":    "그릇",
    "팬":      "후라이팬", "후라이팬": "팬",
    "집게":    "클립", "클립":    "집게",
    "수건":    "타월", "타월":    "수건",
}

def extract_subcategory(text: str) -> str:
    if not SUBCATEGORIES:
        return ""
    text_lower = text

    # 1차: 완전 매칭
    found = [s for s in SUBCATEGORIES if s in text_lower]
    if found:
        return ", ".join(dict.fromkeys(found))

    # 2차: 동의어 사전 치환 후 재매칭
    text_syn = text_lower
    for word, syn in SYNONYM_MAP.items():
        text_syn = text_syn.replace(word, syn)
    found2 = [s for s in SUBCATEGORIES if s in text_syn]
    if found2:
        return ", ".join(dict.fromkeys(found2))

    # 3차: 핵심 키워드(2글자 이상 형태소) 부분 매칭
    tokens = re.findall(r'[가-힣]{2,}', text_lower)
    found3 = []
    for s in SUBCATEGORIES:
        s_tokens = re.findall(r'[가-힣]{2,}', s)
        if any(t in tokens for t in s_tokens if len(t) >= 2):
            found3.append(s)
    if found3:
        # 가장 많이 겹치는 소분류 1개만 반환
        def overlap(s):
            s_t = re.findall(r'[가-힣]{2,}', s)
            return sum(1 for t in s_t if t in tokens)
        found3.sort(key=overlap, reverse=True)
        return found3[0]

    return ""

def match_product_name(code: str) -> str:
    """품번으로 품명 조회"""
    if PRODUCT_DB.empty or not code:
        return ""
    for c in [c.strip() for c in code.split(",")]:
        row = PRODUCT_DB[PRODUCT_DB["품번"].astype(str) == c]
        if not row.empty:
            return row.iloc[0]["품명"]
    return ""


# ============================
# 엑셀 생성
# ============================
def create_excel(data: list, start_date: str, end_date: str) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "LENS 분석결과"
    headers = ["출처","검색어","소분류","품번","품명","가격언급","제목","링크","날짜","감성","확신도(%)","채널/카페명","조회수","좋아요","댓글수"]
    ws.append(headers)
    hf   = openpyxl.styles.Font(bold=True, color="0066CC", name="Malgun Gothic")
    hfil = openpyxl.styles.PatternFill(start_color="E8F1FB", end_color="E8F1FB", fill_type="solid")
    hbrd = openpyxl.styles.Border(bottom=openpyxl.styles.Side(style="thin", color="0066CC"))
    for c in range(1, len(headers)+1):
        cell = ws.cell(1, c)
        cell.font = hf; cell.fill = hfil; cell.border = hbrd
        cell.alignment = openpyxl.styles.Alignment(horizontal="center")
    col_bg  = {"호평":"E8F5EE","악평":"FDEEEE","중립":"FFFBE8"}
    col_txt = {"호평":"16A34A","악평":"DC2626","중립":"CA8A04"}
    for ri, row in enumerate(data, 2):
        ws.append([
            row.get("출처",""), row.get("검색어",""), row.get("소분류",""),
            row.get("품번",""),  row.get("품명",""),  row.get("가격언급",""),
            row.get("title",""), row.get("link",""), row.get("날짜",""),
            row.get("감성",""),  row.get("확신도",0.0),
            row.get("channel",""), row.get("views",""), row.get("likes",""), row.get("comments","")
        ])
        s = row.get("감성","")
        if s in col_bg:
            ws.cell(ri, 10).fill = openpyxl.styles.PatternFill(
                start_color=col_bg[s], end_color=col_bg[s], fill_type="solid")
            ws.cell(ri, 10).font = openpyxl.styles.Font(
                color=col_txt[s], bold=True, name="Malgun Gothic")
    for letter, width in zip("ABCDEFGHIJKLMNO", [8,20,15,15,20,12,45,50,12,8,10,20,10,10,10]):
        ws.column_dimensions[letter].width = width
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf


# ============================
# 헬퍼
# ============================
SENT_BADGE = {"호평":"badge-pos","악평":"badge-neg","중립":"badge-neu"}
SENT_EMOJI = {"호평":"😊","악평":"😞","중립":"😐"}

def icon(emoji: str) -> str:
    return f'<span class="section-title-icon">{emoji}</span>'

def card_icon(emoji: str) -> str:
    return f'<span class="card-title-icon">{emoji}</span>'


# ============================
# 앱 헤더
# ============================
st.markdown("""
<div class="app-header">
    <div class="header-icon">🔵</div>
    <div>
        <div class="header-title">LENS · 불만 SNS 감성분석</div>
        <div class="header-sub">네이버 블로그 · 지식인 · 다이소 카페 · 유튜브 | KR-ELECTRA × KLUE-RoBERTa 앙상블</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================
# 사이드바
# ============================
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;padding-bottom:1rem;border-bottom:1px solid #E2E8F0;margin-bottom:0.5rem;">
        <div style="width:32px;height:32px;background:#0066CC;border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-size:0.9rem;">🔵</div>
        <div>
            <div style="font-weight:700;font-size:0.95rem;color:#1A202C;">LENS 설정</div>
            <div style="font-size:0.7rem;color:#718096;">분석 조건 입력</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<span class="sb-label">🔍 검색어 (줄바꿈 구분 · 최대 10개)</span>', unsafe_allow_html=True)
    keywords_input = st.text_area("", value="다이소 불만\n다이소 짜증\n다이소 별로",
                                  height=130, label_visibility="collapsed")
    st.markdown('<span class="sb-hint">각 줄 = 개별 검색어 (OR 조건으로 수집)</span>', unsafe_allow_html=True)

    st.markdown('<span class="sb-label">📅 수집 기간</span>', unsafe_allow_html=True)
    dc1, dc2 = st.columns(2)
    with dc1: start_date = st.text_input("시작일", value="20250101", help="YYYYMMDD")
    with dc2: end_date   = st.text_input("종료일", value="20250315", help="YYYYMMDD")

    st.markdown('<span class="sb-label">📡 수집 채널</span>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        search_blog = st.checkbox("블로그",      value=True)
        search_cafe = st.checkbox("다이소 카페", value=True)
    with cc2:
        search_kin  = st.checkbox("지식인",      value=True)
        search_yt   = st.checkbox("유튜브",       value=True)

    st.markdown('<span class="sb-label">📊 수집 개수 (건/키워드)</span>', unsafe_allow_html=True)
    display_count = st.slider("", 10, 100, 50, step=10, label_visibility="collapsed")

    st.markdown('<span class="sb-label">🎯 악평 확신도 임계값 (%)</span>', unsafe_allow_html=True)
    threshold = st.slider("", 40, 90, 60, step=5, label_visibility="collapsed",
                          help="이 수치 미만이면 중립으로 분류")

    st.markdown('<span class="sb-label">📺 유튜브 댓글 분석</span>', unsafe_allow_html=True)
    analyze_yt_comments = st.checkbox("댓글도 감성분석", value=True)
    yt_comment_count    = st.slider("댓글 수집 건수", 10, 100, 30, step=10)

    st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("🔵 분석 시작", use_container_width=True)

    with st.expander("📌 YouTube API 키 발급"):
        st.markdown("""
**Step 1** Google Cloud Console 접속  
https://console.cloud.google.com

**Step 2** 새 프로젝트 생성

**Step 3** YouTube Data API v3 활성화  
API 및 서비스 → 라이브러리 → 검색 → 사용 설정

**Step 4** API 키 생성  
사용자 인증 정보 → API 키 → 복사

**Step 5** secrets.toml 등록  
```
YOUTUBE_API_KEY = "AIzaSy..."
```
무료 일일 할당량 **10,000 유닛**
        """)

    with st.expander("📌 Google Sheets 품명 DB 연동"):
        st.markdown("""
**시트 컬럼 구조**  
`품번 | 품명 | 소분류`

**Step 1** Google Cloud → Sheets API 활성화  
**Step 2** 서비스 계정 생성 → JSON 키 다운로드  
**Step 3** 시트 공유 → 서비스 계정 이메일 → 뷰어 권한  
**Step 4** secrets.toml 등록  
```
GSHEET_URL = "https://docs.google.com/..."

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\\n..."
client_email = "...@....iam.gserviceaccount.com"
```
캐시 주기: **1시간** (ttl=3600)
        """)


# ============================
# 분석 실행
# ============================
if run_btn:
    keywords = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()][:10]
    if not keywords:
        st.error("검색어를 최소 1개 입력해주세요."); st.stop()
    if not any([search_blog, search_kin, search_cafe, search_yt]):
        st.error("채널을 하나 이상 선택해주세요."); st.stop()

    # 모델 로드 알림
    with st.spinner("AI 앙상블 모델 초기화 중... (KR-ELECTRA + KLUE-RoBERTa)"):
        model_e = load_electra()
        model_r = load_roberta()

    # ── 데이터 수집 ──────────────────────────────────────
    all_items, collect_log = [], []
    prog_collect = st.progress(0)
    for idx, kw in enumerate(keywords):
        if search_blog:
            r = search_naver(kw, "blog", display_count)
            all_items.extend(r); collect_log.append(f"블로그/{kw}/{len(r)}건")
        if search_kin:
            r = search_naver(kw, "kin", display_count)
            all_items.extend(r); collect_log.append(f"지식인/{kw}/{len(r)}건")
        if search_cafe:
            r = search_naver_cafe(kw, display_count)
            all_items.extend(r); collect_log.append(f"카페/{kw}/{len(r)}건")
        if search_yt and YOUTUBE_API_KEY:
            r = search_youtube(kw, max_results=min(display_count, 50))
            all_items.extend(r); collect_log.append(f"유튜브/{kw}/{len(r)}건")
        prog_collect.progress((idx+1)/len(keywords))
    prog_collect.empty()

    # 중복 제거
    seen, unique_items = set(), []
    for item in all_items:
        lnk = item.get("link", "")
        if lnk not in seen:
            seen.add(lnk); unique_items.append(item)

    # 날짜 필터
    filtered = filter_by_date(unique_items, start_date, end_date)
    if not filtered:
        st.warning("해당 기간에 결과가 없습니다. 날짜 범위를 넓혀보세요."); st.stop()

    st.markdown(f"""
    <div class="card" style="border-left:3px solid #0066CC;">
        <span style="font-size:0.85rem;color:#0066CC;font-weight:600;">
        ✅ 수집 완료 — 총 <strong>{len(filtered)}</strong>건 (중복 제거 후)
        </span><br>
        <span style="font-size:0.72rem;color:#718096;">{' &nbsp;|&nbsp; '.join(collect_log)}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── 감성 분석 ─────────────────────────────────────────
    results, yt_comment_results = [], []
    progress_bar = st.progress(0)
    status_text  = st.empty()

    for i, item in enumerate(filtered):
        src   = item.get("출처", "")
        title = clean_text(item.get("title", ""))
        desc  = clean_text(item.get("description", ""))
        full  = title + " " + desc

        sentiment, score = ai_ensemble(full, model_e, model_r)
        if score < threshold and sentiment != "중립":
            sentiment = "중립"

        if src == "유튜브":
            date_str = item.get("날짜", "")
        else:
            dt = parse_date(item)
            date_str = dt.strftime("%Y-%m-%d") if dt else ""

        prod_code = extract_product_code(full) if src != "유튜브" else ""
        prod_name = match_product_name(prod_code)

        row = {
            "출처":    src,
            "검색어":  item.get("검색어", ""),
            "소분류":  extract_subcategory(full),
            "품번":    prod_code,
            "품명":    prod_name,
            "가격언급":extract_price(full) if src != "유튜브" else "",
            "title":  title,
            "link":   item.get("link", ""),
            "날짜":   date_str,
            "감성":   sentiment,
            "확신도": score,
            "channel":item.get("channel","") or item.get("cafename",""),
            "views":  item.get("views",""),
            "likes":  item.get("likes",""),
            "comments":item.get("comments",""),
            "video_id":item.get("video_id",""),
            "thumbnail":item.get("thumbnail",""),
        }
        results.append(row)

        if src == "유튜브" and analyze_yt_comments and item.get("video_id"):
            for cm in fetch_youtube_comments(item["video_id"], yt_comment_count):
                cs, csc = ai_ensemble(cm["text"], model_e, model_r)
                if csc < threshold and cs != "중립": cs = "중립"
                yt_comment_results.append({
                    "검색어": item.get("검색어",""), "video_id": item["video_id"],
                    "영상제목": title, "댓글": cm["text"],
                    "좋아요": cm["likes"], "날짜": cm["published"],
                    "감성": cs, "확신도": csc,
                })

        progress_bar.progress((i+1)/len(filtered))
        status_text.markdown(
            f'<span style="font-size:0.78rem;color:#718096;">분석 중 {i+1} / {len(filtered)}</span>',
            unsafe_allow_html=True)

    progress_bar.empty(); status_text.empty()

    # ============================
    # 탭 구성
    # ============================
    tab_dash, tab_blog, tab_kin, tab_cafe, tab_yt = st.tabs([
        "📊 대시보드", "📝 블로그", "💬 지식인", "☕ 카페", "▶ 유튜브"
    ])

    # ── 공통 집계 ──────────────────────────────────────────
    total = len(results)
    pos   = sum(1 for r in results if r["감성"]=="호평")
    neg   = sum(1 for r in results if r["감성"]=="악평")
    neu   = sum(1 for r in results if r["감성"]=="중립")

    # 소분류 집계
    all_subs = []
    for r in results:
        if r.get("소분류"):
            all_subs.extend([s.strip() for s in r["소분류"].split(",") if s.strip()])
    sub_cnt = Counter(all_subs)

    # 품번+품명 집계
    all_codes = []
    for r in results:
        if r.get("품번"):
            for c in r["품번"].split(","):
                c = c.strip()
                if c:
                    nm = r.get("품명","")
                    all_codes.append(f"{c} {nm}".strip())
    code_cnt = Counter(all_codes)

    # 일자별 악평 건수
    date_neg = {}
    for r in results:
        if r["감성"] == "악평" and r.get("날짜"):
            try:
                month = r["날짜"][:7]  # YYYY-MM
                date_neg[month] = date_neg.get(month, 0) + 1
            except Exception:
                pass

    # ── 📊 대시보드 ────────────────────────────────────────
    with tab_dash:
        # ① 메트릭 카드
        st.markdown(f'{icon("📈")} <span style="font-size:0.95rem;font-weight:600;">분석 요약</span>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for col, cls, lbl, val, pct, em in [
            (c1,"total","전체 수집",  str(total), "100%",                                    "📋"),
            (c2,"pos",  "호평",      str(pos),   f"{round(pos/total*100) if total else 0}%","😊"),
            (c3,"neg",  "악평",      str(neg),   f"{round(neg/total*100) if total else 0}%","😞"),
            (c4,"neu",  "중립",      str(neu),   f"{round(neu/total*100) if total else 0}%","😐"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card {cls}">
                    <div class="metric-label">
                        <span class="metric-icon {cls}">{em}</span>{lbl}
                    </div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-pct">{pct}</div>
                </div>
                """, unsafe_allow_html=True)

        # ① 대시보드 서브 메트릭 (소분류 수 / 품번 수 / 품명 수)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        d1, d2, d3 = st.columns(3)
        sub_unique   = len(sub_cnt)
        code_unique  = len(set(r["품번"] for r in results if r.get("품번")))
        name_unique  = len(set(r["품명"] for r in results if r.get("품명")))
        for col, lbl, val, ic in [
            (d1,"소분류 수",   str(sub_unique),  "🗂"),
            (d2,"품번 수",     str(code_unique), "🔢"),
            (d3,"품명 수",     str(name_unique), "🏷"),
        ]:
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center;padding:1rem;">
                    <div style="font-size:1.5rem;">{ic}</div>
                    <div style="font-size:1.6rem;font-weight:700;color:#0066CC;font-family:'Inter',sans-serif;">{val}</div>
                    <div style="font-size:0.72rem;color:#718096;margin-top:0.2rem;">{lbl}</div>
                </div>
                """, unsafe_allow_html=True)

        # ② 월별 불만건수 그래프
        if date_neg:
            st.markdown(f'{icon("📅")} <span style="font-size:0.95rem;font-weight:600;">월별 악평 건수</span>', unsafe_allow_html=True)
            chart_df = pd.DataFrame(list(date_neg.items()), columns=["월","악평수"]).sort_values("월")
            chart = (
                alt.Chart(chart_df)
                .mark_bar(color="#0066CC", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("월:O", axis=alt.Axis(title="", labelAngle=0)),
                    y=alt.Y("악평수:Q", axis=alt.Axis(title="악평 건수")),
                    tooltip=["월","악평수"]
                )
                .properties(height=220)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=False, domain=False)
            )
            st.altair_chart(chart, use_container_width=True)

        # ③ TOP10
        col_top1, col_top2 = st.columns(2)
        with col_top1:
            st.markdown(f'{icon("🏷")} <span style="font-size:0.95rem;font-weight:600;">소분류 TOP 10</span>', unsafe_allow_html=True)
            html = ""
            for rank, (name, count) in enumerate(sub_cnt.most_common(10), 1):
                cls = "r1" if rank == 1 else ""
                html += f'<div class="top-item"><div class="top-rank {cls}">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>'
            st.markdown(f'<div class="card">{html if html else "<span style=\'color:#718096;font-size:0.82rem;\'>소분류 데이터 없음</span>"}</div>', unsafe_allow_html=True)

        with col_top2:
            st.markdown(f'{icon("🔢")} <span style="font-size:0.95rem;font-weight:600;">주요 품번+품명 TOP 10</span>', unsafe_allow_html=True)
            html2 = ""
            for rank, (name, count) in enumerate(code_cnt.most_common(10), 1):
                cls = "r1" if rank == 1 else ""
                html2 += f'<div class="top-item"><div class="top-rank {cls}">{rank}</div><div class="top-name">{name}</div><div class="top-count">{count}건</div></div>'
            st.markdown(f'<div class="card">{html2 if html2 else "<span style=\'color:#718096;font-size:0.82rem;\'>품번 데이터 없음</span>"}</div>', unsafe_allow_html=True)

        # ④ 글 내용 출력 (악평 TOP 20)
        st.markdown(f'{icon("📄")} <span style="font-size:0.95rem;font-weight:600;">주요 악평 글 목록</span>', unsafe_allow_html=True)
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
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("악평으로 분류된 글이 없습니다.")

        # 다운로드
        st.markdown(f'{icon("⬇")} <span style="font-size:0.95rem;font-weight:600;">결과 다운로드</span>', unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        with dl1:
            buf = create_excel(results, start_date, end_date)
            st.download_button("📥 EXCEL 다운로드", buf,
                f"LENS_{start_date}_{end_date}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        with dl2:
            df_all = pd.DataFrame(results)
            csv = df_all.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSV 다운로드", csv.encode("utf-8-sig"),
                f"LENS_{start_date}_{end_date}.csv", "text/csv", use_container_width=True)

    # ── 채널별 상세 결과 공통 함수 ────────────────────────
    def render_detail_tab(src_results, src_name):
        if not src_results:
            st.info(f"{src_name} 수집 결과가 없습니다.")
            return
        t  = len(src_results)
        p  = sum(1 for r in src_results if r["감성"]=="호평")
        n  = sum(1 for r in src_results if r["감성"]=="악평")
        ne = sum(1 for r in src_results if r["감성"]=="중립")

        c1,c2,c3,c4 = st.columns(4)
        for col, cls, lbl, val, em in [
            (c1,"total","전체",str(t),"📋"),
            (c2,"pos","호평",str(p),"😊"),
            (c3,"neg","악평",str(n),"😞"),
            (c4,"neu","중립",str(ne),"😐"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card {cls}">
                    <div class="metric-label"><span class="metric-icon {cls}">{em}</span>{lbl}</div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-pct">{round(int(val)/t*100) if t else 0}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        # 검색어별 분포
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
        st.markdown(f'{icon("🔍")} <span style="font-size:0.95rem;font-weight:600;">검색어별 분포</span>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(kw_rows), use_container_width=True, hide_index=True, height=160)

        st.markdown(f'{icon("📄")} <span style="font-size:0.95rem;font-weight:600;">상세 결과</span>', unsafe_allow_html=True)
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
            </div>
            """, unsafe_allow_html=True)

        src_csv = pd.DataFrame(src_results).to_csv(index=False, encoding="utf-8-sig")
        st.download_button(f"📥 {src_name} CSV 다운로드",
            src_csv.encode("utf-8-sig"),
            f"LENS_{src_name}_{start_date}_{end_date}.csv",
            "text/csv", use_container_width=True)

    # ── 📝 블로그 ──────────────────────────────────────────
    with tab_blog:
        render_detail_tab([r for r in results if r["출처"]=="블로그"], "블로그")

    # ── 💬 지식인 ─────────────────────────────────────────
    with tab_kin:
        render_detail_tab([r for r in results if r["출처"]=="지식인"], "지식인")

    # ── ☕ 카페 ───────────────────────────────────────────
    with tab_cafe:
        render_detail_tab([r for r in results if r["출처"]=="카페"], "카페")

    # ── ▶ 유튜브 ─────────────────────────────────────────
    with tab_yt:
        yt_results = [r for r in results if r["출처"]=="유튜브"]
        if not yt_results:
            if not YOUTUBE_API_KEY:
                st.warning("YOUTUBE_API_KEY가 secrets에 없습니다. 사이드바 안내를 참고하세요.")
            else:
                st.info("유튜브 수집 결과가 없습니다.")
        else:
            yt_t = len(yt_results)
            yt_p = sum(1 for r in yt_results if r["감성"]=="호평")
            yt_n = sum(1 for r in yt_results if r["감성"]=="악평")
            yt_ne = sum(1 for r in yt_results if r["감성"]=="중립")

            yc1,yc2,yc3,yc4 = st.columns(4)
            for col, cls, lbl, val, em in [
                (yc1,"total","영상",str(yt_t),"▶"),
                (yc2,"pos","호평",str(yt_p),"😊"),
                (yc3,"neg","악평",str(yt_n),"😞"),
                (yc4,"neu","중립",str(yt_ne),"😐"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="metric-card {cls}">
                        <div class="metric-label"><span class="metric-icon {cls}">{em}</span>{lbl}</div>
                        <div class="metric-value">{val}</div>
                        <div class="metric-pct">{round(int(val)/yt_t*100) if yt_t else 0}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(f'{icon("▶")} <span style="font-size:0.95rem;font-weight:600;">영상 목록 (조회수 순)</span>', unsafe_allow_html=True)
            for r in sorted(yt_results, key=lambda x: x.get("views") or 0, reverse=True)[:20]:
                b = SENT_BADGE.get(r["감성"],"")
                views    = f"{r['views']:,}"    if isinstance(r.get("views"),    int) else "-"
                likes    = f"{r['likes']:,}"    if isinstance(r.get("likes"),    int) else "-"
                comments = f"{r['comments']:,}" if isinstance(r.get("comments"), int) else "-"
                st.markdown(f"""
                <div class="result-card" style="display:flex;gap:1rem;align-items:flex-start;">
                    <div style="flex:1;">
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
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 댓글 분석
            if yt_comment_results:
                st.markdown(f'{icon("💬")} <span style="font-size:0.95rem;font-weight:600;">댓글 감성 분석</span>', unsafe_allow_html=True)
                cm_t  = len(yt_comment_results)
                cm_p  = sum(1 for c in yt_comment_results if c["감성"]=="호평")
                cm_n  = sum(1 for c in yt_comment_results if c["감성"]=="악평")
                cm_ne = sum(1 for c in yt_comment_results if c["감성"]=="중립")
                cc1,cc2,cc3,cc4 = st.columns(4)
                for col, cls, lbl, val, em in [
                    (cc1,"total","댓글",str(cm_t),"💬"),
                    (cc2,"pos","호평",str(cm_p),"😊"),
                    (cc3,"neg","악평",str(cm_n),"😞"),
                    (cc4,"neu","중립",str(cm_ne),"😐"),
                ]:
                    with col:
                        st.markdown(f"""
                        <div class="metric-card {cls}">
                            <div class="metric-label"><span class="metric-icon {cls}">{em}</span>{lbl}</div>
                            <div class="metric-value">{val}</div>
                        </div>
                        """, unsafe_allow_html=True)

                cm_df = pd.DataFrame(yt_comment_results)[["검색어","영상제목","댓글","날짜","좋아요","감성","확신도"]]
                st.dataframe(cm_df, use_container_width=True, height=360, hide_index=True)

                cm_wb = openpyxl.Workbook(); cm_ws = cm_wb.active; cm_ws.title="유튜브댓글"
                cm_ws.append(["검색어","영상제목","댓글","날짜","좋아요","감성","확신도"])
                for row in yt_comment_results:
                    cm_ws.append([row.get(k,"") for k in ["검색어","영상제목","댓글","날짜","좋아요","감성","확신도"]])
                cm_buf = io.BytesIO(); cm_wb.save(cm_buf); cm_buf.seek(0)
                st.download_button("📥 댓글 분석 EXCEL", cm_buf,
                    f"LENS_YT_Comments_{start_date}_{end_date}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)

    # 하단
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;border-top:1px solid #E2E8F0;margin-top:2rem;">
        <span style="font-size:0.75rem;color:#A0AEC0;">LENS · 불만 SNS 감성분석 시스템 · KR-ELECTRA × KLUE-RoBERTa Ensemble</span>
    </div>
    """, unsafe_allow_html=True)
