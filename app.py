import streamlit as st
import requests
import openpyxl
import re
import io
from datetime import datetime
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
# CSS
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:       #0d1117;
    --bg2:      #161b22;
    --card:     #1c2230;
    --border:   #2a3347;
    --border2:  #3b4f6b;
    --text:     #e6edf3;
    --text2:    #8b9ab5;
    --text3:    #586073;
    --accent:   #3b82f6;
    --accent2:  #93c5fd;
    --pos:      #34d399;
    --neg:      #f87171;
    --neu:      #94a3b8;
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

.stApp {
    background: var(--bg);
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* 헤더 */
.page-header {
    display: flex;
    align-items: flex-end;
    gap: 1rem;
    padding: 1.6rem 0 1.2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.6rem;
}
.page-logo {
    font-family: 'DM Mono', monospace;
    font-size: 1.5rem;
    font-weight: 500;
    color: var(--text);
    letter-spacing: 0.08em;
}
.page-badge {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    background: rgba(59,130,246,0.12);
    color: var(--accent2);
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 6px;
    padding: 0.2rem 0.55rem;
    margin-bottom: 0.2rem;
    text-transform: uppercase;
}

/* KPI 카드 */
.kpi-wrap { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1.4rem; }
.kpi {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.1rem 0.9rem;
}
.kpi-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.6rem;
}
.kpi-val {
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    font-weight: 500;
    color: var(--text);
    line-height: 1;
}
.kpi-sub { font-size: 0.75rem; color: var(--text2); margin-top: 0.4rem; }
.kpi.pos { border-top: 2px solid var(--pos); }
.kpi.neg { border-top: 2px solid var(--neg); }
.kpi.neu { border-top: 2px solid var(--neu); }
.kpi.tot { border-top: 2px solid var(--accent); }

/* 진행바 */
.bar-wrap {
    height: 6px;
    display: flex;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(255,255,255,0.05);
    margin: 0 0 1.8rem;
}

/* 섹션 타이틀 */
.sec { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text3); margin: 1.4rem 0 0.7rem; }

/* TOP 목록 */
.top-list { background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.top-row {
    display: flex; align-items: center; gap: 0.8rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.top-row:last-child { border-bottom: none; }
.top-n {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem; color: var(--text3);
    width: 22px; text-align: right;
}
.top-name { flex: 1; font-size: 0.88rem; color: var(--text); }
.top-cnt { font-family: 'DM Mono', monospace; font-size: 0.8rem; color: var(--text2); }

/* 버튼 */
.stButton > button, .stDownloadButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.55rem 1rem !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: #2563eb !important;
}

/* 입력 */
.stTextInput > div > div > input,
.stTextArea textarea,
[data-baseweb="select"] > div {
    background: var(--bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
}
.stCheckbox > label { color: var(--text2) !important; font-size: 0.88rem !important; }

/* 프로그레스 */
.stProgress > div > div > div > div {
    background: var(--accent) !important;
    border-radius: 999px !important;
}
.stProgress > div > div > div {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 999px !important;
}

/* 알림 */
.stAlert { border-radius: 10px !important; background: #132033 !important; }

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* 사이드바 레이블 */
.slabel {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text3);
    margin: 1rem 0 0.35rem;
    display: block;
}
.hint { font-size: 0.68rem; color: var(--text3); margin-top: 0.25rem; display: block; }

/* 로그인 */
.login-box {
    max-width: 320px; margin: 7rem auto;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 2.2rem 2rem;
    text-align: center;
}
.login-title { font-family: 'DM Mono', monospace; font-size: 1.4rem; font-weight: 500; color: var(--text); margin-bottom: 0.3rem; }
.login-sub { font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text3); margin-bottom: 1.6rem; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #2a3347; border-radius: 999px; }
</style>
""", unsafe_allow_html=True)


# ============================
# 비밀번호
# ============================
def check_password():
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div class="login-box">
        <div class="login-title">DAISO LENS</div>
        <div class="login-sub">Sentiment Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        pw = st.text_input("", type="password", placeholder="비밀번호", label_visibility="collapsed")
        if st.button("입장", use_container_width=True):
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
# 소분류 로드
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
# 룰 기반 감성 분석 (강화판)
# ============================
NEGATIVE_KEYWORDS = [
    # 강한 부정
    "최악", "쓰레기", "형편없", "구려", "허접", "최하", "불합격",
    # 불만/실망
    "불만", "불편", "실망", "아쉬워", "아쉽", "짜증", "별로", "별루",
    # 품질 이슈
    "불량", "하자", "고장", "망가", "깨졌", "뜯겨", "터졌", "찢어",
    "냄새", "오염", "더럽", "불결", "지저분", "녹슬", "색빠짐",
    # A/S 관련
    "환불", "교환", "반품", "환급", "클레임", "AS", "수리",
    # 위험/주의
    "위험", "조심", "주의", "다쳤", "긁혔", "베었",
    # 가성비 부정
    "비싸", "과대포장", "사기", "낚임", "낚였",
    # 재구매 의사 없음
    "재구매 안", "비추", "사지마", "구매금지",
    # 평가
    "별점 1", "★1", "⭐1", "1점", "0점",
]

POSITIVE_KEYWORDS = [
    # 만족
    "만족", "좋아요", "좋았", "좋네", "괜찮", "나쁘지않",
    # 추천
    "추천", "강추", "적극추천", "강력추천",
    # 재구매
    "재구매", "또살", "또구매",
    # 품질 칭찬
    "최고", "훌륭", "완벽", "좋은품질", "튼튼", "내구성",
    # 편리
    "편리", "편해요", "편하네", "사용편리",
    # 가성비
    "가성비", "합리적", "저렴한데", "싸고좋",
    # 긍정 표현
    "대박", "꿀템", "득템", "찐템", "예뻐", "예쁘네", "깔끔",
    # 별점
    "별점 5", "★5", "⭐5", "5점", "만점",
]

# 부정어 (앞에 붙으면 반전)
NEGATION_WORDS = ["안", "못", "없", "아니", "전혀", "절대", "별로안", "그다지"]


def rule_sentiment(text: str) -> tuple[str, float]:
    """룰 기반 감성 분석 — (label, confidence_pct) 반환"""
    neg = 0
    pos = 0

    for kw in NEGATIVE_KEYWORDS:
        idx = text.find(kw)
        while idx != -1:
            # 앞 5글자에 부정어 있으면 무효
            prefix = text[max(0, idx-5):idx]
            if any(neg_w in prefix for neg_w in NEGATION_WORDS):
                pass
            else:
                neg += 1
            idx = text.find(kw, idx + 1)

    for kw in POSITIVE_KEYWORDS:
        idx = text.find(kw)
        while idx != -1:
            prefix = text[max(0, idx-5):idx]
            if any(neg_w in prefix for neg_w in NEGATION_WORDS):
                neg += 0.5  # 부정된 긍정은 약한 부정
            else:
                pos += 1
            idx = text.find(kw, idx + 1)

    if neg == 0 and pos == 0:
        return "중립", 50.0

    total = neg + pos
    if neg > pos:
        conf = min(55 + (neg / total) * 40, 97)
        return "악평", round(conf, 1)
    else:
        conf = min(55 + (pos / total) * 40, 97)
        return "호평", round(conf, 1)


# ============================
# 네이버 검색
# ============================
def search_naver(query: str, search_type: str = "blog", display: int = 100) -> list:
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": "date"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        items = r.json().get("items", [])
    except Exception:
        items = []

    label = {"blog": "블로그", "kin": "지식인"}.get(search_type, search_type)
    for item in items:
        item["출처"] = label
        item["검색어"] = query
    return items


# ============================
# 유틸
# ============================
def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    return text.strip()


def parse_date(item: dict):
    date_str = item.get("postdate") or item.get("pubDate", "")
    try:
        if len(date_str) == 8:
            return datetime.strptime(date_str, "%Y%m%d")
        return datetime.strptime(date_str[:16], "%a, %d %b %Y")
    except Exception:
        return None


def filter_by_date(items, start, end):
    s = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end, "%Y%m%d")
    return [i for i in items if parse_date(i) and s <= parse_date(i) <= e]


DATE_PATTERNS = [
    r'\b20\d{6}\b', r'\b\d{4}[-./]\d{2}[-./]\d{2}\b',
    r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b',
    r'\b\d{4}년\s*\d{1,2}월', r'\b\d{1,2}월\s*\d{1,2}일',
]

def is_date_like(token):
    for p in DATE_PATTERNS:
        if re.fullmatch(p, token.strip()):
            return True
    return bool(re.fullmatch(r'\d{6,8}', token.strip()))


def extract_product_code(text):
    raw = re.findall(
        r'\b(?:[A-Za-z]{1,4}[-_]?\d{3,7}|\d{3,6}[-_][A-Za-z]{1,4}|NO\.?\s?\d{2,6})\b', text
    )
    codes = [c for c in raw if not is_date_like(c)]
    return ", ".join(dict.fromkeys(codes)) if codes else ""


def extract_price(text):
    prices = re.findall(r'\d{1,3}(?:,\d{3})*원', text)
    return ", ".join(dict.fromkeys(prices)) if prices else ""


def extract_subcategory(text):
    if not SUBCATEGORIES:
        return ""
    found = [s for s in SUBCATEGORIES if s in text]
    return ", ".join(dict.fromkeys(found)) if found else ""


# ============================
# 엑셀 생성
# ============================
def create_excel(data, start_date, end_date):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "LENS"

    headers = ["출처", "검색어", "소분류", "품번", "가격언급", "제목", "링크", "날짜", "감성", "확신도(%)"]
    ws.append(headers)

    hfill = openpyxl.styles.PatternFill(start_color="161b22", end_color="161b22", fill_type="solid")
    hfont = openpyxl.styles.Font(bold=True, color="E6EDF3", name="Malgun Gothic")
    for col in range(1, len(headers) + 1):
        c = ws.cell(row=1, column=col)
        c.fill = hfill
        c.font = hfont
        c.alignment = openpyxl.styles.Alignment(horizontal="center")

    color_map = {"호평": ("EAF8F0", "166534"), "악평": ("FEE2E2", "991B1B"), "중립": ("EEF2F7", "475569")}
    for ri, row in enumerate(data, 2):
        ws.append([
            row.get("출처"), row.get("검색어"), row.get("소분류"), row.get("품번"),
            row.get("가격언급"), row.get("title"), row.get("link"),
            row.get("날짜"), row.get("감성"), row.get("확신도"),
        ])
        s = row.get("감성", "")
        if s in color_map:
            bg, fg = color_map[s]
            ws.cell(row=ri, column=9).fill = openpyxl.styles.PatternFill(start_color=bg, end_color=bg, fill_type="solid")
            ws.cell(row=ri, column=9).font = openpyxl.styles.Font(color=fg, bold=True, name="Malgun Gothic")

    for letter, width in zip("ABCDEFGHIJ", [8, 20, 15, 15, 15, 45, 50, 12, 8, 10]):
        ws.column_dimensions[letter].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ============================
# 메인 UI
# ============================
st.markdown("""
<div class="page-header">
    <div class="page-logo">DAISO LENS</div>
    <div class="page-badge">Sentiment Dashboard</div>
</div>
""", unsafe_allow_html=True)


# ============================
# 사이드바
# ============================
with st.sidebar:
    st.markdown("""
    <div style="padding:0.2rem 0 1rem; border-bottom:1px solid #2a3347; margin-bottom:0.6rem;">
        <div style="font-family:'DM Mono',monospace; font-size:1rem; font-weight:500; color:#e6edf3; letter-spacing:0.06em;">분석 설정</div>
        <div style="font-size:0.68rem; letter-spacing:0.1em; text-transform:uppercase; color:#586073; margin-top:0.2rem;">Keyword · Channel · Filter</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<span class="slabel">검색어 (줄바꿈으로 구분)</span>', unsafe_allow_html=True)
    keywords_input = st.text_area(
        "", value="다이소 불만\n다이소 짜증\n다이소 별로",
        height=110, label_visibility="collapsed"
    )
    st.markdown('<span class="hint">최대 10개</span>', unsafe_allow_html=True)

    st.markdown('<span class="slabel">수집 기간</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.text_input("시작", value="20250101", help="YYYYMMDD", label_visibility="visible")
    with c2:
        end_date = st.text_input("종료", value="20250315", help="YYYYMMDD", label_visibility="visible")

    st.markdown('<span class="slabel">수집 채널</span>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        search_blog = st.checkbox("블로그", value=True)
    with cc2:
        search_kin = st.checkbox("지식인", value=True)

    st.markdown('<span class="slabel">수집 개수 (건/키워드)</span>', unsafe_allow_html=True)
    display_count = st.slider("", 10, 100, 50, step=10, label_visibility="collapsed")

    st.markdown('<span class="slabel">확신도 임계값 (%)</span>', unsafe_allow_html=True)
    threshold = st.slider("threshold", 0, 100, 50, step=5, label_visibility="collapsed")

    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("분석 시작", use_container_width=True)


# ============================
# 분석 실행
# ============================
if run_btn:
    keywords = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()][:10]

    if not keywords:
        st.error("검색어를 최소 1개 입력해주세요.")
        st.stop()
    if not search_blog and not search_kin:
        st.error("블로그 또는 지식인 중 하나 이상 선택해주세요.")
        st.stop()

    # 수집
    all_items = []
    with st.spinner("데이터 수집 중..."):
        for kw in keywords:
            if search_blog:
                all_items.extend(search_naver(kw, "blog", display_count))
            if search_kin:
                all_items.extend(search_naver(kw, "kin", display_count))

    # 중복 제거
    seen, unique = set(), []
    for item in all_items:
        link = item.get("link", "")
        if link not in seen:
            seen.add(link)
            unique.append(item)

    st.info(f"수집 완료 — {len(unique)}건 (중복 제거 후, 키워드 {len(keywords)}개)")

    filtered = filter_by_date(unique, start_date, end_date)
    if not filtered:
        st.warning("해당 기간에 결과가 없습니다. 날짜 범위를 넓혀보세요.")
        st.stop()

    # 분석
    results = []
    bar = st.progress(0)
    status = st.empty()

    for i, item in enumerate(filtered):
        title = clean_text(item.get("title", ""))
        desc  = clean_text(item.get("description", ""))
        full  = title + " " + desc

        label, score = rule_sentiment(full)

        # 임계값 미달 → 중립
        if score < threshold and label != "중립":
            label = "중립"

        dt = parse_date(item)
        results.append({
            "출처":   item.get("출처", ""),
            "검색어": item.get("검색어", ""),
            "소분류": extract_subcategory(full),
            "품번":   extract_product_code(full),
            "가격언급": extract_price(full),
            "title":  title,
            "link":   item.get("link", ""),
            "날짜":   dt.strftime("%Y-%m-%d") if dt else "",
            "감성":   label,
            "확신도": score,
        })

        pct = (i + 1) / len(filtered)
        bar.progress(pct)
        status.markdown(
            f"<span style='font-size:0.8rem;color:#8b9ab5;'>분석 중 {i+1} / {len(filtered)}</span>",
            unsafe_allow_html=True
        )

    bar.empty()
    status.empty()

    # ============================
    # 결과
    # ============================
    total = len(results)
    pos   = sum(1 for r in results if r["감성"] == "호평")
    neg   = sum(1 for r in results if r["감성"] == "악평")
    neu   = sum(1 for r in results if r["감성"] == "중립")

    # KPI
    st.markdown('<div class="sec">요약</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, cls, label, val, sub in [
        (c1, "tot", "TOTAL",    total, "수집 기간 전체"),
        (c2, "pos", "POSITIVE", pos,   f"{round(pos/total*100) if total else 0}%"),
        (c3, "neg", "NEGATIVE", neg,   f"{round(neg/total*100) if total else 0}%"),
        (c4, "neu", "NEUTRAL",  neu,   f"{round(neu/total*100) if total else 0}%"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi {cls}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-val">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    if total:
        pp = pos/total*100
        np_ = neu/total*100
        negp = neg/total*100
        st.markdown(f"""
        <div class="bar-wrap">
            <div style="width:{pp:.1f}%;background:#34d399;"></div>
            <div style="width:{np_:.1f}%;background:#94a3b8;"></div>
            <div style="width:{negp:.1f}%;background:#f87171;"></div>
        </div>""", unsafe_allow_html=True)

    # 소분류 TOP 5
    all_subs = []
    for r in results:
        if r.get("소분류"):
            all_subs.extend([s.strip() for s in r["소분류"].split(",") if s.strip()])

    if all_subs:
        st.markdown('<div class="sec">소분류 언급 TOP 5</div>', unsafe_allow_html=True)
        top5 = Counter(all_subs).most_common(5)
        rows_html = "".join(
            f'<div class="top-row"><div class="top-n">{i+1}</div>'
            f'<div class="top-name">{name}</div>'
            f'<div class="top-cnt">{cnt}건</div></div>'
            for i, (name, cnt) in enumerate(top5)
        )
        st.markdown(f'<div class="top-list">{rows_html}</div>', unsafe_allow_html=True)

    # 검색어별 분포
    st.markdown('<div class="sec">검색어별 감성 분포</div>', unsafe_allow_html=True)
    kw_stats = {}
    for r in results:
        kw = r.get("검색어", "")
        kw_stats.setdefault(kw, {"호평": 0, "악평": 0, "중립": 0})
        kw_stats[kw][r["감성"]] = kw_stats[kw].get(r["감성"], 0) + 1

    kw_rows = []
    for kw, s in kw_stats.items():
        t = s["호평"] + s["악평"] + s["중립"]
        kw_rows.append({
            "검색어": kw, "호평": s["호평"], "악평": s["악평"],
            "중립": s["중립"], "합계": t,
            "악평률(%)": round(s["악평"] / t * 100, 1) if t else 0
        })
    st.dataframe(pd.DataFrame(kw_rows), use_container_width=True, hide_index=True)

    # 상세 결과
    st.markdown('<div class="sec">상세 결과</div>', unsafe_allow_html=True)

    df = pd.DataFrame(results).rename(columns={"title": "제목", "link": "링크", "확신도": "확신도(%)"})

    def color_sentiment(val):
        return {
            "호평": "background:#dcfce7;color:#166534",
            "악평": "background:#fee2e2;color:#991b1b",
            "중립": "background:#e2e8f0;color:#475569",
        }.get(val, "")

    display_cols = ["출처", "검색어", "소분류", "품번", "가격언급", "제목", "날짜", "감성", "확신도(%)"]
    show_df = df[[c for c in display_cols if c in df.columns]]

    st.dataframe(
        show_df.style.map(color_sentiment, subset=["감성"]),
        use_container_width=True,
        height=400
    )

    # 다운로드
    st.markdown('<div class="sec">다운로드</div>', unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        excel_buf = create_excel(results, start_date, end_date)
        st.download_button(
            "EXCEL 다운로드", data=excel_buf,
            file_name=f"LENS_{start_date}_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with dl2:
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "CSV 다운로드", data=csv_data.encode("utf-8-sig"),
            file_name=f"LENS_{start_date}_{end_date}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("""
    <div style="text-align:center;padding:2rem 0 0.5rem;font-size:0.7rem;color:#3b4f6b;letter-spacing:0.1em;text-transform:uppercase;">
        DAISO LENS · Rule-Based Sentiment · v2
    </div>
    """, unsafe_allow_html=True)
