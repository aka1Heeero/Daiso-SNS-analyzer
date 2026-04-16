import streamlit as st
import requests
import openpyxl
import re
import io
from datetime import datetime
from transformers import pipeline
from collections import Counter
import pandas as pd

# ============================
# 페이지 설정
# ============================
st.set_page_config(
    page_title="DAISO LENS · 리뷰 감성분석",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# 데이터 대시보드형 CSS
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg: #0b1220;
    --bg2: #121a2b;
    --bg3: #182235;
    --card: #1b263b;
    --card2: #22314b;
    --border: #2b3a55;
    --border2: #3b4f73;
    --text: #eef4ff;
    --text2: #b7c5dd;
    --text3: #7f92b0;

    --accent: #3b82f6;
    --accent2: #60a5fa;

    --pos: #22c55e;
    --neg: #ef4444;
    --neu: #94a3b8;

    --pos-bg: rgba(34,197,94,0.12);
    --neg-bg: rgba(239,68,68,0.12);
    --neu-bg: rgba(148,163,184,0.12);
}

/* 전체 */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(59,130,246,0.16), transparent 30%),
        linear-gradient(180deg, #09111d 0%, #0b1220 100%);
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1728 0%, #121a2b 100%) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 1.2rem !important;
}
[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* 메인 헤더 */
.main-header {
    background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(15,23,42,0.2));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2rem 2rem 1.6rem 2rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 12px 28px rgba(0,0,0,0.18);
}
.main-logo {
    font-size: 2.1rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: 0.04em;
    margin-bottom: 0.35rem;
}
.main-sub {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--accent2);
    margin-bottom: 0.4rem;
}
.main-desc {
    font-size: 0.92rem;
    color: var(--text2);
    line-height: 1.55;
}

/* 섹션 타이틀 */
.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    margin: 1.4rem 0 0.8rem 0;
    padding-left: 0.2rem;
}

/* 공통 카드 */
.glass-card {
    background: linear-gradient(180deg, var(--card) 0%, #172235 100%) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1rem 1.1rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.18);
}

/* KPI 카드 */
.metric-card {
    background: linear-gradient(180deg, #1c2740 0%, #182235 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1rem 0.9rem 1rem;
    min-height: 128px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}
.metric-card:hover {
    border-color: var(--border2);
}
.metric-label {
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--text3);
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.metric-value {
    font-size: 2.1rem;
    font-weight: 800;
    line-height: 1;
    color: var(--text);
}
.metric-pct {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text2);
    margin-top: 0.5rem;
}
.metric-card.total { border-bottom: 3px solid var(--accent); }
.metric-card.pos   { border-bottom: 3px solid var(--pos); }
.metric-card.neg   { border-bottom: 3px solid var(--neg); }
.metric-card.neu   { border-bottom: 3px solid var(--neu); }

/* 사이드바 */
.sidebar-panel-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--text);
}
.sidebar-panel-sub {
    font-size: 0.75rem;
    color: var(--accent2);
    font-weight: 600;
    margin-top: 0.15rem;
}
.sidebar-label {
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--text2);
    margin-bottom: 0.35rem;
    margin-top: 1rem;
    display: block;
}
.keyword-hint {
    font-size: 0.7rem;
    color: var(--text3);
    margin-top: 0.35rem;
    display: block;
}

/* 로그인 */
.login-wrap {
    max-width: 360px;
    margin: 6rem auto;
    background: linear-gradient(180deg, #121a2b 0%, #172235 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2.6rem 2.2rem;
    text-align: center;
    box-shadow: 0 16px 30px rgba(0,0,0,0.22);
}
.login-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.4rem;
}
.login-sub {
    font-size: 0.78rem;
    color: var(--accent2);
    margin-bottom: 1.6rem;
    font-weight: 600;
}

/* 버튼 */
.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(180deg, var(--accent) 0%, #2563eb 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.62rem 1rem !important;
    box-shadow: 0 8px 18px rgba(37,99,235,0.28);
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    background: linear-gradient(180deg, var(--accent2) 0%, var(--accent) 100%) !important;
}

/* 입력 */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div,
[data-baseweb="select"] > div {
    background: #0f1728 !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

/* 체크박스 */
.stCheckbox > label {
    color: var(--text2) !important;
}

/* 슬라이더 */
.stSlider > div[data-baseweb="slider"] > div > div {
    color: var(--accent) !important;
}

/* 프로그레스 */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
    border-radius: 999px !important;
}
.stProgress > div > div > div {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 999px !important;
}

/* 알림 */
.stAlert {
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
    background: #132033 !important;
}

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
}

/* TOP 5 */
.top-item {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.85rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.top-item:last-child {
    border-bottom: none;
}
.top-rank {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: rgba(59,130,246,0.14);
    color: var(--accent2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 800;
}
.top-name {
    color: var(--text);
    font-size: 0.92rem;
    flex: 1;
    font-weight: 600;
}
.top-count {
    color: var(--text2);
    font-size: 0.82rem;
    font-weight: 700;
}

/* 스크롤바 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f1728; }
::-webkit-scrollbar-thumb { background: #31425f; border-radius: 999px; }
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
        <div class="login-title">DAISO LENS</div>
        <div class="login-sub">Review Sentiment Dashboard</div>
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
    model_name = "snunlp/KR-FinBert-SC"
    try:
        clf = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            truncation=True,
            max_length=512,
            top_k=None,
            device=-1
        )
        return clf
    except Exception as e:
        st.warning(f"모델 로드 실패: {e}")
        return None


@st.cache_resource
def load_sentiment_model():
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
    except Exception:
        return None


# ============================
# 네이버 검색
# ============================
def search_naver(query: str, search_type: str = "blog", display: int = 100) -> list:
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
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
    end_dt   = datetime.strptime(end, "%Y%m%d")
    return [
        item for item in items
        if parse_date(item) and start_dt <= parse_date(item) <= end_dt
    ]


# ============================
# 앙상블 감성 분석
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
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)

    if neg_count > pos_count:
        return "악평", min(0.6 + neg_count * 0.08, 0.95)
    elif pos_count > neg_count:
        return "호평", min(0.55 + pos_count * 0.08, 0.95)
    return "중립", 0.5


def ai_sentiment_ensemble(text: str, model_a, model_b=None) -> tuple:
    label_map = {
        "positive": "호평", "pos": "호평", "LABEL_2": "호평", "호평": "호평",
        "negative": "악평", "neg": "악평", "LABEL_0": "악평", "악평": "악평",
        "neutral":  "중립", "neu": "중립", "LABEL_1": "중립", "중립": "중립",
    }

    votes = {"호평": 0.0, "악평": 0.0, "중립": 0.0}

    if model_a:
        try:
            result_a = model_a(text[:512])[0]
            for item in result_a:
                lbl = label_map.get(item["label"], None)
                if lbl:
                    votes[lbl] += item["score"] * 1.5
        except Exception:
            pass

    if model_b:
        try:
            result_b = model_b(text[:512])[0]
            for item in result_b:
                lbl = label_map.get(item["label"], None)
                if lbl:
                    votes[lbl] += item["score"] * 1.0
        except Exception:
            pass

    rule_lbl, rule_score = rule_based_sentiment(text)
    votes[rule_lbl] += rule_score * 0.6

    total = sum(votes.values())
    if total == 0:
        return "중립", 50.0

    best_label = max(votes, key=votes.get)
    best_score = round(votes[best_label] / total * 100, 1)

    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    if neg_count >= 3 and best_label != "악평":
        best_label = "악평"
        best_score = max(best_score, 72.0)

    return best_label, best_score


# ============================
# 품번 추출 (날짜 패턴 제외)
# ============================
DATE_PATTERNS = [
    r'\b20\d{6}\b',
    r'\b\d{4}[-./]\d{2}[-./]\d{2}\b',
    r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b',
    r'\b\d{4}년\s*\d{1,2}월',
    r'\b\d{1,2}월\s*\d{1,2}일',
]


def is_date_like(token: str) -> bool:
    for pat in DATE_PATTERNS:
        if re.fullmatch(pat, token.strip()):
            return True
    if re.fullmatch(r'\d{6,8}', token.strip()):
        return True
    return False


def extract_product_code(text: str) -> str:
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

    header_fill = openpyxl.styles.PatternFill(start_color="1B263B", end_color="1B263B", fill_type="solid")
    header_font = openpyxl.styles.Font(bold=True, color="EAF2FF", name="Malgun Gothic")
    border = openpyxl.styles.Border(
        bottom=openpyxl.styles.Side(style="thin", color="60A5FA")
    )

    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = openpyxl.styles.Alignment(horizontal="center")

    color_map = {
        "호평": "EAF8F0",
        "악평": "FDECEC",
        "중립": "EEF2F7",
        "분석불가": "F3F4F6"
    }
    text_color_map = {
        "호평": "15803D",
        "악평": "DC2626",
        "중립": "64748B",
        "분석불가": "6B7280"
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
        fill_color = color_map.get(sentiment, "FFFFFF")
        txt_color = text_color_map.get(sentiment, "111827")

        ws.cell(row=row_idx, column=9).fill = openpyxl.styles.PatternFill(
            start_color=fill_color, end_color=fill_color, fill_type="solid"
        )
        ws.cell(row=row_idx, column=9).font = openpyxl.styles.Font(
            color=txt_color, bold=True, name="Malgun Gothic"
        )

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
    <div class="main-logo">DAISO LENS</div>
    <div class="main-sub">Sentiment Analysis Dashboard</div>
    <div class="main-desc">
        블로그·지식인 리뷰를 수집하고, 앙상블 AI 모델로 감성 분류 결과를 대시보드 형태로 제공합니다.
    </div>
</div>
""", unsafe_allow_html=True)


# ============================
# 사이드바
# ============================
with st.sidebar:
    st.markdown("""
    <div style="padding-bottom:1rem; border-bottom:1px solid #2b3a55; margin-bottom:0.4rem;">
        <div class="sidebar-panel-title">분석 설정</div>
        <div class="sidebar-panel-sub">Keyword · Channel · Threshold</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<span class="sidebar-label">검색어 (다중 입력)</span>', unsafe_allow_html=True)
    keywords_input = st.text_area(
        "",
        value="다이소 불만\n다이소 짜증\n다이소 별로",
        height=120,
        label_visibility="collapsed",
        help="한 줄에 하나씩 입력하세요. 각 키워드를 개별 검색합니다."
    )
    st.markdown('<span class="keyword-hint">줄바꿈 기준으로 키워드 분리 / 최대 10개</span>', unsafe_allow_html=True)

    st.markdown('<span class="sidebar-label">수집 기간</span>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.text_input("시작일", value="20250101", help="YYYYMMDD")
    with col2:
        end_date = st.text_input("종료일", value="20250315", help="YYYYMMDD")

    st.markdown('<span class="sidebar-label">수집 채널</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        search_blog = st.checkbox("블로그", value=True)
    with c2:
        search_kin = st.checkbox("지식인", value=True)

    st.markdown('<span class="sidebar-label">수집 개수 (건/키워드)</span>', unsafe_allow_html=True)
    display_count = st.slider("", 10, 100, 50, step=10, label_visibility="collapsed")

    st.markdown('<span class="sidebar-label">감성 임계값 (%)</span>', unsafe_allow_html=True)
    threshold = st.slider(
        "확신도 임계값", 0, 100, 55, step=5,
        label_visibility="collapsed",
        help="이 수치 이상인 경우만 결과에 포함합니다"
    )

    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("분석 시작", use_container_width=True, type="primary")


# ============================
# 분석 실행
# ============================
if run_btn:
    keywords = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()]
    keywords = keywords[:10]

    if not keywords:
        st.error("검색어를 최소 1개 입력해주세요.")
        st.stop()

    if not search_blog and not search_kin:
        st.error("블로그 또는 지식인 중 하나 이상 선택해주세요.")
        st.stop()

    with st.spinner(""):
        st.markdown(
            '<div class="glass-card"><strong style="color:#60a5fa;">모델 초기화 중...</strong></div>',
            unsafe_allow_html=True
        )
        model_a = load_model()
        model_b = load_sentiment_model()

    all_items = []
    collect_status = st.empty()

    for kw in keywords:
        if search_blog:
            items = search_naver(kw, "blog", display_count)
            all_items.extend(items)
        if search_kin:
            items = search_naver(kw, "kin", display_count)
            all_items.extend(items)

    seen_links = set()
    unique_items = []
    for item in all_items:
        link = item.get("link", "")
        if link not in seen_links:
            seen_links.add(link)
            unique_items.append(item)

    collect_status.markdown(f"""
    <div class="glass-card">
        수집 완료 — 총 <strong style="color:#60a5fa;">{len(unique_items)}</strong>건
        (중복 제거 후 / 키워드 {len(keywords)}개)
    </div>
    """, unsafe_allow_html=True)

    filtered = filter_by_date(unique_items, start_date, end_date)

    if not filtered:
        st.warning("해당 기간에 결과가 없습니다. 날짜 범위를 넓혀보세요.")
        st.stop()

    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, item in enumerate(filtered):
        title = clean_text(item.get("title", ""))
        desc = clean_text(item.get("description", ""))
        full_text = title + " " + desc

        sentiment, score = ai_sentiment_ensemble(full_text, model_a, model_b)

        if score < threshold and sentiment != "중립":
            sentiment = "중립"

        dt = parse_date(item)
        date_str = dt.strftime("%Y-%m-%d") if dt else ""

        results.append({
            "출처": item.get("출처", ""),
            "검색어": item.get("검색어", ""),
            "소분류": extract_subcategory(full_text),
            "품번": extract_product_code(full_text),
            "가격언급": extract_price(full_text),
            "title": title,
            "link": item.get("link", ""),
            "날짜": date_str,
            "감성": sentiment,
            "확신도": score,
        })

        pct = (i + 1) / len(filtered)
        progress_bar.progress(pct)
        status_text.markdown(
            f"<div style='color:#b7c5dd; font-size:0.82rem; margin-top:0.4rem;'>분석 중 {i+1} / {len(filtered)}</div>",
            unsafe_allow_html=True
        )

    progress_bar.empty()
    status_text.empty()

    # ============================
    # 결과 표시
    # ============================
    total = len(results)
    pos = sum(1 for r in results if r["감성"] == "호평")
    neg = sum(1 for r in results if r["감성"] == "악평")
    neu = sum(1 for r in results if r["감성"] == "중립")

    st.markdown('<div class="section-title">분석 요약</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        (col1, "Total Reviews", str(total), "수집 기간 전체", "total"),
        (col2, "Positive", str(pos), f"{round(pos/total*100) if total else 0}%", "pos"),
        (col3, "Negative", str(neg), f"{round(neg/total*100) if total else 0}%", "neg"),
        (col4, "Neutral", str(neu), f"{round(neu/total*100) if total else 0}%", "neu"),
    ]

    for col, label, val, pct_text, cls in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card {cls}">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-pct">{pct_text}</div>
            </div>
            """, unsafe_allow_html=True)

    if total > 0:
        pos_pct = pos / total * 100
        neg_pct = neg / total * 100
        neu_pct = neu / total * 100
        st.markdown(f"""
        <div style="margin: 1rem 0 2rem; height: 8px; display: flex; border-radius: 999px; overflow: hidden; background: rgba(255,255,255,0.06);">
            <div style="width:{pos_pct:.1f}%; background: #22c55e;"></div>
            <div style="width:{neu_pct:.1f}%; background: #94a3b8;"></div>
            <div style="width:{neg_pct:.1f}%; background: #ef4444;"></div>
        </div>
        """, unsafe_allow_html=True)

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
                <div class="top-rank">{rank}</div>
                <div class="top-name">{name}</div>
                <div class="top-count">{count}건</div>
            </div>
            """
        st.markdown(f'<div class="glass-card">{top_html}</div>', unsafe_allow_html=True)

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

    st.markdown('<div class="section-title">상세 결과</div>', unsafe_allow_html=True)

    df = pd.DataFrame(results).rename(columns={
        "title": "제목",
        "link": "링크",
        "확신도": "확신도(%)"
    })

    def color_sentiment(val):
        m = {
            "호평": "background:#DCFCE7; color:#166534",
            "악평": "background:#FEE2E2; color:#991B1B",
            "중립": "background:#E2E8F0; color:#475569"
        }
        return m.get(val, "")

    display_cols = ["출처", "검색어", "소분류", "품번", "가격언급", "제목", "날짜", "감성", "확신도(%)"]
    show_df = df[[c for c in display_cols if c in df.columns]]

    st.dataframe(
        show_df.style.applymap(color_sentiment, subset=["감성"]),
        use_container_width=True,
        height=420
    )

    st.markdown('<div class="section-title">결과 다운로드</div>', unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        excel_buffer = create_excel(results, ",".join(keywords[:3]), start_date, end_date)
        st.download_button(
            label="EXCEL 다운로드",
            data=excel_buffer,
            file_name=f"LENS_{start_date}_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_dl2:
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="CSV 다운로드",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"LENS_{start_date}_{end_date}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("""
    <div style="text-align:center; padding:2.4rem 0 0.6rem; color:#7f92b0; font-size:0.78rem;">
        DAISO LENS · Sentiment Analysis Dashboard
    </div>
    """, unsafe_allow_html=True)
