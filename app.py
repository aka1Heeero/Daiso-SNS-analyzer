import streamlit as st
import requests
import openpyxl
import re
import io
from datetime import datetime
from transformers import pipeline
from collections import Counter
import pandas as pd

st.set_page_config(page_title="🤬 다이소 고객불만 AI분석 by PC", page_icon="🔍", layout="wide")

# ============================
# 비밀번호
# ============================
def check_password():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if st.session_state.auth:
        return True
    st.markdown("## LOG IN")
    pw = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("입력"):
        if pw == st.secrets["PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ 비밀번호 오류")
    return False

if not check_password():
    st.stop()

NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

# ============================
# 상품 사전
# ============================
_raw = st.secrets.get("DAISO_PRODUCTS", "")
_custom = [p.strip() for p in _raw.split(",") if p.strip()]
_default = []
PRODUCT_DICT = sorted(set(_custom + _default), key=len, reverse=True)

SYNONYM_DICT = {
    "텀블러":   ["보온병","보냉병","스텐컵"],
    "수세미":   ["설거지솔","수세미볼","철수세미"],
    "마스크팩": ["시트팩","마스크시트"],
    "바구니":   ["바스켓","정리함","수납함","트레이"],
    "행거":     ["스탠드행거","빨래걸이"],
    "매트":     ["발매트","욕실매트","미끄럼방지매트"],
    "충전기":   ["어댑터","충전어댑터","멀티충전기"],
    "케이블":   ["충전선","USB선","C타입선","라이트닝"],
    "마우스":   ["무선마우스","유선마우스","블루투스마우스"],
    "키보드":   ["무선키보드","유선키보드","블루투스키보드"],
    "지퍼백":   ["비닐백","보관백","냉동백"],
    "가습기":   ["초음파가습기","미니가습기","가열식가습기"],
    "젤램프":   ["젤네일램프","UV램프","LED램프","네일램프"],
    "전구":     ["LED전구","형광등","야간등"],
}

# ============================
# 1차: 불만 필터
# ============================
COMPLAINT_KEYWORDS = [
    "불만","불편","별로","실망","최악","나쁨","후회","환불",
    "불량","파손","고장","터짐","깨짐","냄새","이상","문제",
    "아쉽","싸구려","저품질","불량품","반품","교환","비추",
    "불편하다","위험","유해","녹","곰팡이","찢어짐","벗겨짐",
    "짧다","작다","크다","무겁다","약하다","얇다","두껍다"
]
PRODUCT_KEYWORDS = [
    "샀","구매","구입","제품","상품","사용","써봤","써보니",
    "개봉","사봤","가격","원짜리","원에","원인데","후기","리뷰"
]

POSITIVE_CONTEXT = [
    "저렴해","싸다","착하다","알뜰","합리적","가성비좋","가성비최고",
    "저렴하네","싸네","가격이좋","저가","가격착해","가격이착해",
    "강추","득템","꿀템","완전좋","최고야","대박이","좋네","좋다",
    "만족해","만족스러","훌륭해","뛰어나","퀄리티좋","품질좋",
    "잘만들","튼튼해","오래써","오래가","내구성좋",
    "추천해","추천함","알게됐","발견했","득템했","찾았다","찾았어",
    "이거사세요","사세요","사봐","써봐","써보세요",
    "뮤지엄","박물관","미술관","해외","면세","백화점","마트보다",
    "편의점보다","온라인보다","다른곳보다","훨씬싸","비교불가",
    "대박","화악뛰","가격이화악","놀랍","신기해","이게이가격",
    "이가격에","이런퀄리티","가격대비좋","믿기지않","믿기지않아"
    
]

def is_complaint(text, brand):
    if "다이소" not in text:
        return False
    # 명백한 칭찬/비교 글은 제외
    if any(kw in text for kw in POSITIVE_CONTEXT):
        return False
    return (any(kw in text for kw in PRODUCT_KEYWORDS)
            and any(kw in text for kw in COMPLAINT_KEYWORDS))

# ============================
# 검색어 적정성 검사
# ============================
def check_query(query):
    warnings, suggestions = [], []
    if not any(h in query for h in ["불만","불량","후기","리뷰","문제","이상"]):
        suggestions.append('💡 추천: **"다이소 불만"** 또는 **"다이소 불량 후기"**')
    if len(query.strip()) > 20:
        warnings.append("검색어가 너무 길면 결과가 적을 수 있어요")
    return warnings, suggestions

# ============================
# 2차: AI 감성 분석
# ============================
@st.cache_resource
def load_model():
    return pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC",
                    truncation=True, max_length=512)

DEFAULT_POSITIVE = [
    "꿀이었","강추","최고","완벽","대박","굿","좋았","만족",
    "추천","좋아요","훌륭","짱","최애","득템","필수템","꿀템"
]
DEFAULT_NEGATIVE = [
    "최악","환불","불량품","쓰레기","망했","최저","형편없",
    "절대비추","비추","후회","실망","돈낭비","진짜별로"
]

def ai_sentiment(text, model):
    if any(kw in text for kw in DEFAULT_POSITIVE): return "호평", 95.0
    if any(kw in text for kw in DEFAULT_NEGATIVE): return "악평", 95.0
    try:
        r = model(text[:512])[0]
        label = r["label"].lower()
        score = round(r["score"] * 100, 1)
        if "pos" in label or label == "1": return "호평", score
        elif "neg" in label or label == "0": return "악평", score
        return "중립", score
    except:
        return "분석불가", 0.0

# ============================
# 3차: 불만 유형 분류
# ============================
COMPLAINT_TYPES = {
    "품질불량": ["불량","파손","깨짐","터짐","찢어짐","벗겨짐","고장","녹","곰팡이","변형","부러짐","갈라짐","오염","불량품"],
    "안전성":   ["유해","위험","냄새","악취","독성","알레르기","피부트러블","가려움","발진","환경호르몬","납","중금속"],
    "스펙불일치":["작다","크다","짧다","길다","무겁다","가볍다","두껍다","얇다","생각보다","예상보다","사진과 다름","실물과 다름","색이 다름"],
    "내구성":   ["약하다","금방","며칠만에","하루만에","바로","얼마안가","쉽게망가","오래못감"],
    "구매경험": ["환불","반품","교환","불친절","응대","AS","품절","재고없음","단종","배송"],
    "가성비":   ["비싸다","가격대비","돈낭비","아깝다","손해","바가지","가성비나쁨"]
}

def classify_type(text):
    matched = [t for t, kws in COMPLAINT_TYPES.items() if any(kw in text for kw in kws)]
    return ", ".join(matched[:2]) if matched else "기타불만"

# ============================
# 3차: 상품명 추출
# ============================
STOPWORDS = {
    "다이소","네이버","블로그","지식인","카카오","쿠팡","이마트","온라인","오프라인",
    "자","은","는","이","가","을","를","의","에","도","만","로","으로","에서","에게",
    "이것","저것","그것","이거","저거","그거","여기","저기","거기","이곳","저곳",
    "구매","후기","리뷰","사용","제품","상품","추천","가격","할인","불만","불량",
    "고장","파손","해당","관련","같은","어떤","이런","저런","그런","모든","일부","전체",
    "보면","대한","위한","통해","따라","방법","질문","문의","안내","설명","확인",
    "손님","진상","거기에","영양제","신문","기사","쿠폰","소송","대응","피고","원고",
    "회복","민생","소비자","발명가","기업","브랜드","매장","지점",
    "자체","빠지는데","등에서","접촉","슈얼리","물건","교환","환불",
    "무선","유선","감도","속도","성능","기능","구조","방식","형태","종류","색상",
    "크기","사이즈","용량","무게","두께","길이","너비","높이",
}

def extract_product(text, brand="다이소"):
    for p in PRODUCT_DICT:
        if p in text: return p
    for key, synonyms in SYNONYM_DICT.items():
        for s in synonyms:
            if s in text: return key
    m = re.search(r'다이소\s+([가-힣]{2,8})(?=[^가-힣]|$)', text)
    if m:
        candidate = m.group(1)
        if candidate not in STOPWORDS and len(candidate) >= 2:
            return candidate
    m = re.search(r'([가-힣]{2,8})\s+(?:불량|파손|고장|후기|리뷰)(?:\s|$)', text)
    if m:
        candidate = m.group(1)
        if candidate not in STOPWORDS and len(candidate) >= 2:
            return candidate
    return ""

# ============================
# 품번 / 가격 추출
# ============================
def extract_info(text):
    prices = re.findall(r'[1-9]\d{0,2}(?:,\d{3})*원', text)
    codes = re.findall(r'(?<![0-9,])\b[1-9]\d{4,9}\b(?![0-9])', text)
    price_nums = [re.sub(r'[,원]', '', p) for p in prices]
    codes = [c for c in codes if c not in price_nums]
    return {
        "품번": ", ".join(list(dict.fromkeys(codes))[:3]),
        "가격": ", ".join(set(prices))
    }

# ============================
# 텍스트 정제
# ============================
def clean_text(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ============================
# 네이버 검색
# ============================
def search_naver(query, type_, display=100):
    url = f"https://openapi.naver.com/v1/search/{type_}.json"
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    items, start = [], 1
    while start <= display:
        fetch = min(100, display - start + 1)
        try:
            res = requests.get(url, headers=headers,
                params={"query": query, "display": fetch, "start": start, "sort": "date"},
                timeout=10)
            batch = res.json().get("items", [])
            if not batch: break
            for item in batch:
                item["출처"] = "블로그" if type_ == "blog" else "지식인"
            items += batch
        except Exception as e:
            st.warning(f"수집 오류: {e}"); break
        start += fetch
    return items

# ============================
# 날짜 파싱
# ============================
MONTH_MAP = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
             "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

def parse_date(item):
    # 블로그: postdate = "20250317"
    d = item.get("postdate", "").strip()
    if re.match(r'^\d{8}$', d):
        try:
            return datetime.strptime(d, "%Y%m%d")
        except:
            pass

    # 지식인: pubDate = "Mon, 17 Mar 2025 00:00:00 +0900"
    d = item.get("pubDate", "").strip()
    if "," in d:
        try:
            parts = d.split()
            day   = int(parts[1])
            month = MONTH_MAP.get(parts[2], 0)
            year  = int(parts[3])
            if month > 0:
                return datetime(year, month, day)
        except:
            pass

    return None

def filter_by_date(items, start, end):
    s, e = datetime.strptime(start, "%Y%m%d"), datetime.strptime(end, "%Y%m%d")
    result = []
    for item in items:
        dt = parse_date(item)
        if dt is None or s <= dt <= e:
            result.append(item)
    return result

# ============================
# 엑셀 생성
# ============================
def create_excel(data, query, start_date, end_date):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AI 불만 분석"
    headers = ["출처","품명","품번","가격","제목","링크","날짜","감성","확신도(%)","불만유형","불만여부(태깅)"]
    ws.append(headers)
    for col in range(1, len(headers)+1):
        ws.cell(1, col).font = openpyxl.styles.Font(bold=True)
        ws.cell(1, col).fill = openpyxl.styles.PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    ws.cell(1, 11).fill = openpyxl.styles.PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
    s_colors = {"호평":"C6EFCE","악평":"FFC7CE","중립":"FFEB9C","분석불가":"D9D9D9"}
    t_colors = {"품질불량":"FCE4D6","안전성":"FFE0E0","스펙불일치":"EAF0FB","내구성":"FFF2CC","구매경험":"E2EFDA","가성비":"F0E6FF","기타불만":"F2F2F2"}
    for ri, r in enumerate(data, 2):
        ws.append([r["출처"],r["품명"],r["품번"],r["가격"],r["title"],r["link"],r["날짜"],r["감성"],r["확신도"],r["불만유형"],""])
        ws.cell(ri,8).fill = openpyxl.styles.PatternFill(start_color=s_colors.get(r["감성"],"FFFFFF"), end_color=s_colors.get(r["감성"],"FFFFFF"), fill_type="solid")
        first_type = r["불만유형"].split(",")[0].strip()
        ws.cell(ri,10).fill = openpyxl.styles.PatternFill(start_color=t_colors.get(first_type,"F2F2F2"), end_color=t_colors.get(first_type,"F2F2F2"), fill_type="solid")
        ws.cell(ri,11).fill = openpyxl.styles.PatternFill(start_color="FFFDE7", end_color="FFFDE7", fill_type="solid")
    ws2 = wb.create_sheet("📌 태깅 안내")
    ws2["A1"] = "태깅 방법 안내"
    ws2["A1"].font = openpyxl.styles.Font(bold=True, size=14)
    for row in [[],["목적","AI 파인튜닝용 학습 데이터 수집"],[],["입력값","의미","예시"],
                ["1","실제 불만글","텀블러 뚜껑 깨짐 환불요청"],["0","불만 아닌 글","다이소 어디서 파나요?"],
                ["빈칸","확인 안 함",""],[],["목표","200개 이상 → 파인튜닝 가능"]]:
        ws2.append(row)
    for col, w in zip("ABCDEFGHIJK",[10,18,14,14,40,48,12,10,10,20,16]):
        ws.column_dimensions[col].width = w
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

# ============================
# 메인 UI
# ============================
st.title("🤬 네이버 고객불만 AI 분석기 by PC")
st.markdown("블로그·지식인 **불만 후기만** 수집 → AI 감성분석 → 불만유형 자동분류")
st.caption("🤖 KR-FinBert-SC  |  1차 불만필터 → 2차 감성분석 → 3차 상품명+유형분류")
st.divider()

with st.sidebar:
    st.header("⚙️ 분석 설정")
    st.markdown("**🔎 검색어**")
    st.caption("브랜드 + 상품명 + 불만키워드 조합")
    query = st.text_input("검색어 입력", value="다이소 불만", label_visibility="collapsed")

    if query:
        warnings, suggestions = check_query(query)
        for w in warnings: st.warning(f"⚠️ {w}")
        for s in suggestions: st.info(s)
        if not warnings and not suggestions: st.success("✅ 검색어 적절")

    c1, c2 = st.columns(2)
    with c1: start_date = st.text_input("시작일", "20250101", help="YYYYMMDD")
    with c2: end_date   = st.text_input("종료일",  "20260101", help="YYYYMMDD")

    st.markdown("**수집 채널**")
    do_blog = st.checkbox("블로그", value=True)
    do_kin  = st.checkbox("지식인", value=True)
    st.checkbox("🚧 Youtube (추가중)", value=False, disabled=True)
    display_count = st.slider("최대 수집 수", 100, 1000, 100, step=100)
    st.divider()
    run = st.button("🐎 분석 시작", use_container_width=True, type="primary")

if run:
    if not query: st.error("검색어를 입력하세요"); st.stop()
    if not do_blog and not do_kin: st.error("채널을 하나 이상 선택하세요"); st.stop()

    with st.spinner("🤖 AI 모델 로딩 중..."): model = load_model()

    all_items = []
    with st.spinner("📡 수집 중..."):
        if do_blog:
            b = search_naver(query, "blog", display_count)
            all_items += b
            st.info(f"블로그 {len(b)}개")
        if do_kin:
            k = search_naver(query, "kin", display_count)
            all_items += k
            st.info(f"지식인 {len(k)}개")
        if k:
        for item in k[:3]:
            st.code(f"pubDate: [{item.get('pubDate', '없음')}]")

    filtered = filter_by_date(all_items, start_date, end_date)

    # 날짜 디버깅 — 결과 0개일 때 원인 확인
    if len(filtered) == 0 and all_items:
        st.warning("🔍 날짜 디버깅: 첫 5개 확인")
        for item in all_items[:5]:
            pd_val = item.get("postdate", "없음")
            pub_val = item.get("pubDate", "없음")
            dt = parse_date(item)
            st.code(f"출처:{item.get('출처')} | postdate:[{pd_val}] | pubDate:[{pub_val}] | 파싱결과:{dt}")

    st.write(f"📅 날짜 필터 후: **{len(filtered)}개**")
    if not filtered: st.warning("해당 기간에 결과가 없습니다."); st.stop()

    brand, results, skipped = query.split()[0], [], 0
    prog = st.progress(0, text="분석 중...")

    for i, item in enumerate(filtered):
        title = clean_text(item.get("title", ""))
        desc  = clean_text(item.get("description", ""))
        text  = title + " " + desc

        if not is_complaint(text, brand):
            skipped += 1
            prog.progress((i+1)/len(filtered), text=f"1차 필터 중... ({i+1}/{len(filtered)})")
            continue

        senti, score = ai_sentiment(text, model)
        product = extract_product(text, brand)
        ctype   = classify_type(text)
        info    = extract_info(text)
        dt      = parse_date(item)

        results.append({
            "출처":  item["출처"],
            "품명":  product,
            "title": title,
            "link":  item.get("link",""),
            "날짜":  dt.strftime("%Y-%m-%d") if dt else "",
            "감성":  senti,
            "확신도": score,
            "불만유형": ctype,
            **info
        })
        prog.progress((i+1)/len(filtered), text=f"분석 중... ({i+1}/{len(filtered)})")

    prog.empty()
    st.success(f"✅ 완료! 불만 {len(results)}개 / 일반글 {skipped}개 제외")
    st.divider()

    if not results: st.warning("불만 관련 글이 없습니다. 검색어를 바꿔보세요!"); st.stop()

    total = len(results)
    pos = sum(1 for r in results if r["감성"]=="호평")
    neg = sum(1 for r in results if r["감성"]=="악평")
    neu = sum(1 for r in results if r["감성"]=="중립")

    st.subheader("📊 감성 요약")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("전체",f"{total}개")
    m2.metric("호평 😊",f"{pos}개",f"{round(pos/total*100)}%")
    m3.metric("악평 😞",f"{neg}개",f"{round(neg/total*100)}%")
    m4.metric("중립 😐",f"{neu}개",f"{round(neu/total*100)}%")

    st.subheader("🗂️ 불만 유형 분포")
    all_types = []
    for r in results: all_types.extend([t.strip() for t in r["불만유형"].split(",")])
    t_counts = Counter(all_types).most_common()
    tc1, tc2 = st.columns(2)
    for idx, (t, c) in enumerate(t_counts[:6]):
        col = tc1 if idx < 3 else tc2
        col.write(f"**{t}**: {c}건 ({round(c/total*100)}%)")

    name_list = [r["품명"] for r in results if r["품명"]]
    if name_list:
        st.subheader("🏷️ 불만 품명 TOP 5")
        for name, cnt in Counter(name_list).most_common(5):
            st.write(f"**{name}**: {cnt}건")

    st.subheader("📋 상세 결과")
    s_col = {"호평":"#C6EFCE","악평":"#FFC7CE","중립":"#FFEB9C"}
    t_col = {"품질불량":"#FCE4D6","안전성":"#FFE0E0","스펙불일치":"#EAF0FB","내구성":"#FFF2CC","구매경험":"#E2EFDA","가성비":"#F0E6FF","기타불만":"#F2F2F2"}
    rows_html = ""
    for r in results:
        s_bg = s_col.get(r["감성"],"#FFF")
        t_bg = t_col.get(r["불만유형"].split(",")[0].strip(),"#F2F2F2")
        link = f'<a href="{r["link"]}" target="_blank">🔗</a>' if r["link"] else ""
        rows_html += f"""<tr>
            <td>{r["출처"]}</td><td>{r["품명"]}</td><td>{r["품번"]}</td>
            <td>{r["가격"]}</td><td>{r["title"]}</td><td>{link}</td>
            <td>{r["날짜"]}</td>
            <td style="background:{s_bg};font-weight:bold">{r["감성"]}</td>
            <td>{r["확신도"]}</td>
            <td style="background:{t_bg}">{r["불만유형"]}</td>
        </tr>"""

    st.markdown(f"""
    <style>
      .rt{{width:100%;border-collapse:collapse;font-size:12px}}
      .rt th{{background:#D9D9D9;padding:7px 8px;border:1px solid #ccc;text-align:left}}
      .rt td{{padding:6px 8px;border:1px solid #eee;vertical-align:middle}}
      .rt tr:hover td{{background:#f9f9f9}}
      .rt a{{color:#1a73e8;text-decoration:none;font-size:14px}}
    </style>
    <div style="max-height:500px;overflow-y:auto">
    <table class="rt"><thead><tr>
      <th>출처</th><th>품명</th><th>품번</th><th>가격</th>
      <th>제목</th><th>링크</th><th>날짜</th><th>감성</th><th>확신도</th><th>불만유형</th>
    </tr></thead><tbody>{rows_html}</tbody></table></div>
    """, unsafe_allow_html=True)

    st.subheader("💾 결과 다운로드")
    st.info("📌 **'불만여부(태깅)'** 컬럼에 불만글=**1**, 일반글=**0** → 200개 모이면 AI 파인튜닝 가능")
    excel_buf = create_excel(results, query, start_date, end_date)
    st.download_button(
        "📥 엑셀 다운로드", data=excel_buf,
        file_name=f"불만분석_{query[:5]}_{start_date}_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
