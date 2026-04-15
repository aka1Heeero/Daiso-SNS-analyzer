import streamlit as st
import requests
import openpyxl
import re
import io
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from collections import Counter
import pandas as pd

# ============================
# 페이지 설정
# ============================
st.set_page_config(
    page_title="LENS · 리뷰 감성분석",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# 고급 CSS 디자인
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;600;700&family=DM+Mono:ital,wght@0,300;0,400;1,300&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&display=swap');

:root {
    --bg:        #0c0c0e;
    --bg2:       #111116;
    --bg3:       #16161d;
    --border:    #2a2a35;
    --border2:   #353545;
    --accent:    #c8a96e;
    --accent2:   #e8c98e;
    --text:      #e8e4dc;
    --text2:     #9a9490;
    --text3:     #6a6460;
    --pos:       #4a9e6e;
    --neg:       #c05858;
    --neu:       #7878a8;
    --pos-bg:    rgba(74,158,110,0.10);
    --neg-bg:    rgba(192,88,88,0.10);
    --neu-bg:    rgba(120,120,168,0.10);
}

/* 전체 배경 */
.stApp {
    background-color: var(--bg) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(200,169,110,0.06) 0%, transparent 60%),
        repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.015) 40px),
        repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.015) 40px);
    color: var(--text) !important;
    font-family: 'Noto Serif KR', serif !important;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 2rem !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* 메인 헤더 */
.main-header {
    text-align: center;
    padding: 3.5rem 0 2rem;
    position: relative;
}
.main-header::before {
    content: '';
    display: block;
    width: 1px;
    height: 60px;
    background: linear-gradient(to bottom, transparent, var(--accent));
    margin: 0 auto 2rem;
}
.main-logo {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 4.5rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.35em !important;
    color: var(--accent) !important;
    line-height: 1 !important;
    margin: 0 !important;
}
.main-sub {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.25em !important;
    color: var(--text3) !important;
    margin-top: 0.6rem !important;
    text-transform: uppercase !important;
}
.main-desc {
    font-size: 0.88rem !important;
    color: var(--text2) !important;
    margin-top: 1.2rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.03em !important;
}
.main-header::after {
    content: '';
    display: block;
    width: 60px;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--accent), transparent);
    margin: 2rem auto 0;
}

/* 섹션 타이틀 */
.section-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.4rem !important;
    font-weight: 400 !important;
    color: var(--accent) !important;
    letter-spacing: 0.08em !important;
    border-left: 2px solid var(--accent) !important;
    padding-left: 0.8rem !important;
    margin: 2rem 0 1.2rem !important;
}

/* 카드 */
.glass-card {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    padding: 1.5rem !important;
    margin-bottom: 1rem !important;
    position: relative !important;
    overflow: hidden !important;
}
.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--accent), transparent);
    opacity: 0.4;
}

/* 메트릭 카드 */
.metric-card {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 1.6rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
.metric-card:hover { border-color: var(--border2); }
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.5rem;
}
.metric-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.8rem;
    font-weight: 300;
    line-height: 1;
    color: var(--text);
}
.metric-pct {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--text3);
    margin-top: 0.3rem;
}
.metric-card.pos { border-bottom: 2px solid var(--pos); }
.metric-card.neg { border-bottom: 2px solid var(--neg); }
.metric-card.neu { border-bottom: 2px solid var(--neu); }
.metric-card.total { border-bottom: 2px solid var(--accent); }

/* 배지 */
.badge-pos { background: var(--pos-bg); color: var(--pos); border: 1px solid var(--pos); border-radius: 2px; padding: 0.15rem 0.5rem; font-size: 0.72rem; font-family: 'DM Mono', monospace; }
.badge-neg { background: var(--neg-bg); color: var(--neg); border: 1px solid var(--neg); border-radius: 2px; padding: 0.15rem 0.5rem; font-size: 0.72rem; font-family: 'DM Mono', monospace; }
.badge-neu { background: var(--neu-bg); color: var(--neu); border: 1px solid var(--neu); border-radius: 2px; padding: 0.15rem 0.5rem; font-size: 0.72rem; font-family: 'DM Mono', monospace; }

/* 사이드바 레이블 */
.sidebar-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.3rem;
    margin-top: 1rem;
    display: block;
}

/* 구분선 */
.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 2rem 0;
}

/* 로그인 폼 */
.login-wrap {
    max-width: 340px;
    margin: 6rem auto;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 3rem 2.5rem;
    text-align: center;
    position: relative;
}
.login-wrap::before {
    content: '';
    display: block;
    width: 40px;
    height: 1px;
    background: var(--accent);
    margin: 0 auto 1.5rem;
}
.login-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.8rem;
    font-weight: 300;
    color: var(--accent);
    letter-spacing: 0.15em;
    margin-bottom: 0.4rem;
}
.login-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: var(--text3);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

/* 진행바 */
.stProgress > div > div > div > div {
    background: linear-gradient(to right, var(--accent), var(--accent2)) !important;
    border-radius: 0 !important;
}
.stProgress > div > div > div {
    background: var(--border) !important;
    border-radius: 0 !important;
    height: 2px !important;
}

/* 버튼 */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.25s !important;
}
.stButton > button:hover {
    background: var(--accent) !important;
    color: var(--bg) !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: var(--bg) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent2) !important;
    border-color: var(--accent2) !important;
}

/* 입력창 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    color: var(--text) !important;
    font-family: 'Noto Serif KR', serif !important;
    font-size: 0.88rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: none !important;
}

/* 슬라이더 */
.stSlider > div > div > div > div {
    background: var(--accent) !important;
}

/* 체크박스 */
.stCheckbox > label > div:first-child {
    border-color: var(--border2) !important;
    border-radius: 0 !important;
    background: transparent !important;
}
.stCheckbox > label > div:first-child[data-checked="true"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* 다운로드 버튼 */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
    width: 100% !important;
}
.stDownloadButton > button:hover {
    background: var(--accent) !important;
    color: var(--bg) !important;
}

/* 알림 */
.stAlert {
    border-radius: 0 !important;
    border-left-width: 2px !important;
    background: var(--bg3) !important;
}
.stInfo { border-left-color: var(--accent) !important; }
.stSuccess { border-left-color: var(--pos) !important; }
.stWarning { border-left-color: #a88040 !important; }
.stError { border-left-color: var(--neg) !important; }

/* 데이터프레임 */
.dataframe { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; }
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
}

/* 스크롤바 */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 0; }

/* Selectbox */
.stSelectbox > div > div {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    color: var(--text) !important;
}

/* 태그 입력 힌트 */
.keyword-hint {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: var(--text3);
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
    display: block;
}

/* TOP 5 리스트 */
.top-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--border);
}
.top-rank {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.4rem;
    font-weight: 300;
    color: var(--text3);
    min-width: 2rem;
}
.top-name { color: var(--text); font-size: 0.88rem; flex: 1; }
.top-count {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--accent);
}

/* 헤더 제거 */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================
# 비밀번호 체크
# ============================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.markdown("""
    <div class="login-wrap">
        <div class="login-title">LENS</div>
        <div class="login-sub">Review Intelligence System</div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        pw = st.text_input("", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        if st.button("ENTER", use_container_width=True, type="primary"):
            if pw == st.secrets.get("PASSWORD", ""):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("인증 실패")
    return False

if not check_password():
    st.stop()


# ============================
# API 키
# ============================
NAVER_CLIENT_ID     = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

# ============================
# 소분류 리스트 (secrets에서 로드)
# ============================
@st.cache_data
def load_subcategories():
    """secrets에 저장된 소분류 목록을 로드."""
    try:
        raw = st.secrets.get("SUBCATEGORIES", "")
        if isinstance(raw, list):
            return [s.strip() for s in raw if s.strip()]
        if raw:
            return [s.strip() for s in raw.split(",") if s.strip()]
    except Exception:
        pass
    return []

SUBCATEGORIES = load_subcategories()


# ============================
# AI 모델 로드
# ============================
@st.cache_resource
def load_model():
    """
    multilingual-sentiment-base: 다국어 지원 + 한국어 성능 우수
    3-class (pos / neg / neu) 분류 모델
    """
    model_name = "snunlp/KR-FinBert-SC"
    try:
        clf = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            truncation=True,
            max_length=512,
            top_k=None,          # 전체 확률 반환
            device=-1
        )
        return clf
    except Exception as e:
        st.warning(f"모델 로드 실패: {e}")
        return None


@st.cache_resource
def load_sentiment_model():
    """
    불만/호평 이진 특화 추가 모델
    cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual
    """
    try:
        clf = pipeline(
            "text-classification",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
            top_k=None,
            truncation=True,
            max_length=512,
            device=-1
        )
        return clf
    except Exception as e:
        return None


# ============================
# 네이버 검색
# ============================
def search_naver(query: str, search_type: str = "blog", display: int = 100) -> list:
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id":     NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": display, "sort": "date"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        items = response.json().get("items", [])
    except Exception:
        items = []
    source = "블로그" if search_type == "blog" else "지식인"
    for item in items:
        item["출처"] = source
        item["검색어"] = query
    return items


# ============================
# 텍스트 정제
# ============================
def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    return text.strip()


# ============================
# 날짜 파싱 & 필터링
# ============================
def parse_date(item: dict):
    date_str = item.get("postdate") or item.get("pubDate", "")
    try:
        if len(date_str) == 8:
            return datetime.strptime(date_str, "%Y%m%d")
        return datetime.strptime(date_str[:16], "%a, %d %b %Y")
    except Exception:
        return None


def filter_by_date(items: list, start: str, end: str) -> list:
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt   = datetime.strptime(end,   "%Y%m%d")
    return [
        item for item in items
        if parse_date(item) and start_dt <= parse_date(item) <= end_dt
    ]


# ============================
# 앙상블 감성 분석 (정밀도 향상)
# ============================
NEGATIVE_KEYWORDS = [
    "불만", "짜증", "별로", "최악", "실망", "환불", "불량", "교환", "이상해",
    "형편없", "쓰레기", "구려", "나빠", "고장", "터졌", "망가", "깨졌",
    "불편", "아쉬워", "위험", "조심", "주의", "문제", "하자", "뜯겨",
    "냄새", "오염", "불결", "지저분", "더럽", "싸구려", "허접", "대충",
    "클레임", "AS", "환급", "반품", "재구매 안", "비추", "별점 1", "⭐"
]

POSITIVE_KEYWORDS = [
    "좋아요", "좋았", "만족", "추천", "재구매", "최고", "훌륭", "완벽",
    "편리", "예뻐", "가성비", "합리적", "대박", "꿀템", "강추"
]

def rule_based_sentiment(text: str) -> tuple:
    """키워드 기반 감성 스코어 (보조용)."""
    text_lower = text.lower()
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    if neg_count > pos_count:
        return "악평", min(0.6 + neg_count * 0.08, 0.95)
    elif pos_count > neg_count:
        return "호평", min(0.55 + pos_count * 0.08, 0.95)
    return "중립", 0.5


def ai_sentiment_ensemble(text: str, model_a, model_b=None) -> tuple:
    """
    앙상블 감성 분석:
    1. KR-FinBert (3-class)
    2. XLM-RoBERTa multilingual (3-class)
    3. 키워드 룰 기반
    → 가중 투표로 최종 결정
    """
    label_map = {
        "positive": "호평", "pos": "호평", "LABEL_2": "호평", "호평": "호평",
        "negative": "악평", "neg": "악평", "LABEL_0": "악평", "악평": "악평",
        "neutral":  "중립", "neu": "중립", "LABEL_1": "중립", "중립": "중립",
    }

    votes = {"호평": 0.0, "악평": 0.0, "중립": 0.0}

    # ① 모델 A (KR-FinBert)
    if model_a:
        try:
            result_a = model_a(text[:512])[0]  # top_k=None → list
            for item in result_a:
                lbl = label_map.get(item["label"], None)
                if lbl:
                    votes[lbl] += item["score"] * 1.5   # 가중치 1.5
        except Exception:
            pass

    # ② 모델 B (XLM-RoBERTa)
    if model_b:
        try:
            result_b = model_b(text[:512])[0]
            for item in result_b:
                lbl = label_map.get(item["label"], None)
                if lbl:
                    votes[lbl] += item["score"] * 1.0
        except Exception:
            pass

    # ③ 키워드 룰 기반 (보조)
    rule_lbl, rule_score = rule_based_sentiment(text)
    votes[rule_lbl] += rule_score * 0.6

    # 최종 결정
    total = sum(votes.values())
    if total == 0:
        return "중립", 50.0

    best_label = max(votes, key=votes.get)
    best_score = round(votes[best_label] / total * 100, 1)

    # 직접 불만 키워드가 명확히 있으면 악평 강제 보정
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    if neg_count >= 3 and best_label != "악평":
        best_label = "악평"
        best_score = max(best_score, 72.0)

    return best_label, best_score


# ============================
# 품번 추출 (날짜 패턴 제외)
# ============================
DATE_PATTERNS = [
    r'\b20\d{6}\b',           # 20250101
    r'\b\d{4}[-./]\d{2}[-./]\d{2}\b',  # 2025-01-01
    r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b',
    r'\b\d{4}년\s*\d{1,2}월',
    r'\b\d{1,2}월\s*\d{1,2}일',
]

def is_date_like(token: str) -> bool:
    """토큰이 날짜처럼 생겼는지 판단."""
    for pat in DATE_PATTERNS:
        if re.fullmatch(pat, token.strip()):
            return True
    # 순수 숫자 6~8자리 → 날짜로 간주
    if re.fullmatch(r'\d{6,8}', token.strip()):
        return True
    return False


def extract_product_code(text: str) -> str:
    """품번 추출 (날짜 패턴 제외)."""
    # 품번 패턴: 영문+숫자 조합 or NO.숫자
    raw_codes = re.findall(
        r'\b(?:[A-Za-z]{1,4}[-_]?\d{3,7}|\d{3,6}[-_][A-Za-z]{1,4}|NO\.?\s?\d{2,6})\b',
        text
    )
    codes = [c for c in raw_codes if not is_date_like(c)]
    return ", ".join(dict.fromkeys(codes)) if codes else ""


def extract_price(text: str) -> str:
    prices = re.findall(r'\d{1,3}(?:,\d{3})*원', text)
    return ", ".join(dict.fromkeys(prices)) if prices else ""


def extract_subcategory(text: str) -> str:
    """
    secrets에 저장된 소분류 목록 중 텍스트에 등장하는 것만 반환.
    마음대로 추출하지 않음.
    """
    if not SUBCATEGORIES:
        return ""
    found = [sub for sub in SUBCATEGORIES if sub in text]
    return ", ".join(dict.fromkeys(found)) if found else ""


# ============================
# 엑셀 생성
# ============================
def create_excel(data: list, query: str, start_date: str, end_date: str) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "LENS 분석결과"

    headers = ["출처", "검색어", "소분류", "품번", "가격언급", "제목", "링크", "날짜", "감성", "확신도(%)"]
    ws.append(headers)

    # 헤더 스타일
    header_fill = openpyxl.styles.PatternFill(start_color="1A1A24", end_color="1A1A24", fill_type="solid")
    header_font = openpyxl.styles.Font(bold=True, color="C8A96E", name="Malgun Gothic")
    border_side = openpyxl.styles.Side(style="thin", color="2A2A35")
    border = openpyxl.styles.Border(
        bottom=openpyxl.styles.Side(style="thin", color="C8A96E")
    )
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = openpyxl.styles.Alignment(horizontal="center")

    color_map = {
        "호평":   "1E3D2F",
        "악평":   "3D1E1E",
        "중립":   "1E1E3D",
        "분석불가": "2A2A2A"
    }
    text_color_map = {
        "호평": "4A9E6E",
        "악평": "C05858",
        "중립": "7878A8",
        "분석불가": "6A6460"
    }

    for row_idx, row in enumerate(data, start=2):
        ws.append([
            row.get("출처", ""),
            row.get("검색어", ""),
            row.get("소분류", ""),
            row.get("품번", ""),
            row.get("가격언급", ""),
            row.get("title", ""),
            row.get("link", ""),
            row.get("날짜", ""),
            row.get("감성", ""),
            row.get("확신도", 0.0),
        ])
        sentiment = row.get("감성", "")
        fill_color = color_map.get(sentiment, "111116")
        txt_color  = text_color_map.get(sentiment, "E8E4DC")

        # 감성 셀 색상
        ws.cell(row=row_idx, column=9).fill = openpyxl.styles.PatternFill(
            start_color=fill_color, end_color=fill_color, fill_type="solid"
        )
        ws.cell(row=row_idx, column=9).font = openpyxl.styles.Font(
            color=txt_color, bold=True, name="Malgun Gothic"
        )

    # 컬럼 너비
    widths = [8, 20, 15, 15, 15, 45, 50, 12, 8, 10]
    col_letters = ["A","B","C","D","E","F","G","H","I","J"]
    for letter, width in zip(col_letters, widths):
        ws.column_dimensions[letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ============================
# 메인 UI
# ============================

# 헤더
st.markdown("""
<div class="main-header">
    <div class="main-logo">LENS</div>
    <div class="main-sub">Review Intelligence · Naver Sentiment Engine</div>
    <div class="main-desc">블로그·지식인 리뷰를 수집하고 앙상블 AI로 감성을 정밀 분석합니다</div>
</div>
""", unsafe_allow_html=True)

# ============================
# 사이드바
# ============================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding-bottom:1.5rem; border-bottom: 1px solid #2a2a35;">
        <div style="font-family:'Cormorant Garamond',serif; font-size:1.6rem; color:#c8a96e; letter-spacing:0.2em;">LENS</div>
        <div style="font-family:'DM Mono',monospace; font-size:0.58rem; color:#6a6460; letter-spacing:0.2em; text-transform:uppercase; margin-top:0.2rem;">설정 패널</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<span class="sidebar-label">🔎 검색어 (다중 입력)</span>', unsafe_allow_html=True)
    keywords_input = st.text_area(
        "",
        value="다이소 불만\n다이소 짜증\n다이소 별로",
        height=120,
        label_visibility="collapsed",
        help="한 줄에 하나씩 입력하세요. 각 키워드를 개별 검색합니다."
    )
    st.markdown('<span class="keyword-hint">↑ 줄바꿈으로 키워드 구분 (최대 10개)</span>', unsafe_allow_html=True)

    st.markdown('<span class="sidebar-label">📅 수집 기간</span>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.text_input("시작일", value="20250101", help="YYYYMMDD")
    with col2:
        end_date = st.text_input("종료일", value="20250315", help="YYYYMMDD")

    st.markdown('<span class="sidebar-label">📡 수집 채널</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        search_blog = st.checkbox("블로그", value=True)
    with c2:
        search_kin  = st.checkbox("지식인", value=True)

    st.markdown('<span class="sidebar-label">📊 수집 개수 (건/키워드)</span>', unsafe_allow_html=True)
    display_count = st.slider("", 10, 100, 50, step=10, label_visibility="collapsed")

    st.markdown('<span class="sidebar-label">🎯 감성 임계값 (%)</span>', unsafe_allow_html=True)
    threshold = st.slider("확신도 임계값", 0, 100, 55, step=5, label_visibility="collapsed",
                          help="이 수치 이상인 경우만 결과에 포함합니다")

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("◈ 분석 시작", use_container_width=True, type="primary")


# ============================
# 분석 실행
# ============================
if run_btn:
    # 키워드 파싱
    keywords = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()]
    keywords = keywords[:10]  # 최대 10개

    if not keywords:
        st.error("검색어를 최소 1개 입력해주세요.")
        st.stop()
    if not search_blog and not search_kin:
        st.error("블로그 또는 지식인 중 하나 이상 선택해주세요.")
        st.stop()

    # 모델 로드
    with st.spinner(""):
        st.markdown('<div class="glass-card"><span style="font-family:\'DM Mono\',monospace; font-size:0.72rem; color:#c8a96e; letter-spacing:0.15em;">◈ AI 모델 초기화 중...</span></div>', unsafe_allow_html=True)
        model_a = load_model()
        model_b = load_sentiment_model()

    # 수집
    all_items = []
    collect_status = st.empty()

    for kw in keywords:
        if search_blog:
            items = search_naver(kw, "blog", display_count)
            all_items.extend(items)
        if search_kin:
            items = search_naver(kw, "kin", display_count)
            all_items.extend(items)

    # 중복 제거 (링크 기준)
    seen_links = set()
    unique_items = []
    for item in all_items:
        link = item.get("link", "")
        if link not in seen_links:
            seen_links.add(link)
            unique_items.append(item)

    collect_status.markdown(f"""
    <div class="glass-card">
        <span style="font-family:'DM Mono',monospace; font-size:0.72rem; color:#c8a96e;">
            ◈ 수집 완료 — 총 <strong style="color:#e8c98e">{len(unique_items)}</strong>건
            (중복제거 후 / 키워드 {len(keywords)}개)
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 날짜 필터
    filtered = filter_by_date(unique_items, start_date, end_date)

    if not filtered:
        st.warning("해당 기간에 결과가 없습니다. 날짜 범위를 넓혀보세요.")
        st.stop()

    # 감성 분석
    results = []
    progress_bar = st.progress(0)
    status_text  = st.empty()

    for i, item in enumerate(filtered):
        title = clean_text(item.get("title", ""))
        desc  = clean_text(item.get("description", ""))
        full_text = title + " " + desc

        sentiment, score = ai_sentiment_ensemble(full_text, model_a, model_b)

        # 임계값 필터 (중립은 그냥 통과)
        # 확신도가 낮으면 중립 처리
        if score < threshold and sentiment != "중립":
            sentiment = "중립"

        dt       = parse_date(item)
        date_str = dt.strftime("%Y-%m-%d") if dt else ""

        results.append({
            "출처":    item.get("출처", ""),
            "검색어":  item.get("검색어", ""),
            "소분류":  extract_subcategory(full_text),
            "품번":    extract_product_code(full_text),
            "가격언급": extract_price(full_text),
            "title":  title,
            "link":   item.get("link", ""),
            "날짜":   date_str,
            "감성":   sentiment,
            "확신도": score,
        })

        pct = (i + 1) / len(filtered)
        progress_bar.progress(pct)
        status_text.markdown(
            f'<span style="font-family:\'DM Mono\',monospace; font-size:0.68rem; color:#6a6460;">'
            f'분석 중 {i+1} / {len(filtered)}</span>',
            unsafe_allow_html=True
        )

    progress_bar.empty()
    status_text.empty()

    # ============================
    # 결과 표시
    # ============================
    total = len(results)
    pos   = sum(1 for r in results if r["감성"] == "호평")
    neg   = sum(1 for r in results if r["감성"] == "악평")
    neu   = sum(1 for r in results if r["감성"] == "중립")

    st.markdown('<div class="section-title">분석 요약</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        (col1, "TOTAL",   str(total),  f"수집 기간 내 전체", "total", ""),
        (col2, "호평",    str(pos),    f"{round(pos/total*100) if total else 0}%",   "pos",   "😊"),
        (col3, "악평",    str(neg),    f"{round(neg/total*100) if total else 0}%",   "neg",   "😞"),
        (col4, "중립",    str(neu),    f"{round(neu/total*100) if total else 0}%",   "neu",   "😐"),
    ]
    for col, label, val, pct, cls, emoji in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card {cls}">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-pct">{pct} {emoji}</div>
            </div>
            """, unsafe_allow_html=True)

    # 감성 비율 바
    if total > 0:
        pos_pct = pos / total * 100
        neg_pct = neg / total * 100
        neu_pct = neu / total * 100
        st.markdown(f"""
        <div style="margin: 1.2rem 0 2rem; height: 4px; display: flex; border-radius: 0; overflow: hidden;">
            <div style="width:{pos_pct:.1f}%; background: #4a9e6e;"></div>
            <div style="width:{neu_pct:.1f}%; background: #7878a8;"></div>
            <div style="width:{neg_pct:.1f}%; background: #c05858;"></div>
        </div>
        """, unsafe_allow_html=True)

    # 많이 언급된 소분류
    all_subs = []
    for r in results:
        if r.get("소분류"):
            all_subs.extend([s.strip() for s in r["소분류"].split(",") if s.strip()])

    if all_subs:
        st.markdown('<div class="section-title">소분류 언급 TOP 5</div>', unsafe_allow_html=True)
        top_subs = Counter(all_subs).most_common(5)
        top_html = ""
        for rank, (name, count) in enumerate(top_subs, 1):
            top_html += f"""
            <div class="top-item">
                <div class="top-rank">{rank:02d}</div>
                <div class="top-name">{name}</div>
                <div class="top-count">{count}건</div>
            </div>
            """
        st.markdown(f'<div class="glass-card">{top_html}</div>', unsafe_allow_html=True)

    # 검색어별 감성 분포
    st.markdown('<div class="section-title">검색어별 감성 분포</div>', unsafe_allow_html=True)
    kw_stats = {}
    for r in results:
        kw = r.get("검색어", "")
        if kw not in kw_stats:
            kw_stats[kw] = {"호평": 0, "악평": 0, "중립": 0}
        kw_stats[kw][r["감성"]] = kw_stats[kw].get(r["감성"], 0) + 1

    kw_rows = []
    for kw, s in kw_stats.items():
        total_kw = s["호평"] + s["악평"] + s["중립"]
        kw_rows.append({
            "검색어": kw,
            "호평": s["호평"],
            "악평": s["악평"],
            "중립": s["중립"],
            "합계": total_kw,
            "악평률(%)": round(s["악평"] / total_kw * 100, 1) if total_kw else 0
        })
    kw_df = pd.DataFrame(kw_rows)
    st.dataframe(kw_df, use_container_width=True, hide_index=True)

    # 상세 결과
    st.markdown('<div class="section-title">상세 결과</div>', unsafe_allow_html=True)

    df = pd.DataFrame(results).rename(columns={
        "title": "제목", "link": "링크", "확신도": "확신도(%)"
    })

    def color_sentiment(val):
        m = {"호평": "background:#1E3D2F; color:#4a9e6e",
             "악평": "background:#3D1E1E; color:#c05858",
             "중립": "background:#1E1E3D; color:#7878a8"}
        return m.get(val, "")

    display_cols = ["출처", "검색어", "소분류", "품번", "가격언급", "제목", "날짜", "감성", "확신도(%)"]
    show_df = df[[c for c in display_cols if c in df.columns]]

    st.dataframe(
        show_df.style.applymap(color_sentiment, subset=["감성"]),
        use_container_width=True,
        height=420
    )

    # 다운로드
    st.markdown('<div class="section-title">결과 다운로드</div>', unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        excel_buffer = create_excel(results, ",".join(keywords[:3]), start_date, end_date)
        st.download_button(
            label="◈ EXCEL 다운로드",
            data=excel_buffer,
            file_name=f"LENS_{start_date}_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_dl2:
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="◈ CSV 다운로드",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"LENS_{start_date}_{end_date}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 하단 장식
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0 1rem; border-top: 1px solid #2a2a35; margin-top: 3rem;">
        <div style="font-family:'Cormorant Garamond',serif; font-size:1.1rem; color:#c8a96e; letter-spacing:0.25em;">LENS</div>
        <div style="font-family:'DM Mono',monospace; font-size:0.58rem; color:#3a3a45; letter-spacing:0.15em; margin-top:0.3rem; text-transform:uppercase;">Review Intelligence System</div>
    </div>
    """, unsafe_allow_html=True)
