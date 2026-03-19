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

# ============================
# API 키
# ============================
NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

# ============================
# 상품 사전 (secrets에서 추가 가능)
# ============================
_raw = st.secrets.get("DAISO_PRODUCTS", "")
_custom = [p.strip() for p in _raw.split(",") if p.strip()]
_default = [
    "발목양말","압축봉","텀블러","마스크팩","수세미","칫솔","면봉",
    "화장솜","지퍼백","행거","클립","바구니","파우치","보냉백","우산",
    "슬리퍼","도마","접시","그릇","컵","머그컵","물병","케이스","파일",
    "메모지","스티커","테이프","가위","자","풀","빗","거울","족집게",
    "면도기","손톱깎이","헤어핀","머리끈","수건","욕실화","칫솔걸이",
    "비누통","샴푸통","휴지통","집게","옷걸이","선반","훅","고리",
    "매트","방석","쿠션","양초","방향제","모기향","살충제","세제","장갑",
    "충전기","케이블","이어폰","건전지","보조배터리","압축팩","세탁망",
    "빨래집게","행주","앞치마","냄비받침","주방장갑","국자","주걱",
    "병따개","캔따개","채반","소쿠리","식판","도시락","물통","빨대",
    "청소포","밀대","빗자루","쓰레받기","위생봉투","쓰레기봉투"
]
PRODUCT_DICT = sorted(set(_custom + _default), key=len, reverse=True)

# ============================
# 동의어 사전
# ============================
SYNONYM_DICT = {
    "양말":     ["발목양말","쿠션양말","스포츠양말","덧신"],
    "텀블러":   ["보온병","보냉병","스텐컵"],
    "수세미":   ["설거지솔","수세미볼","철수세미"],
    "마스크팩": ["팩","마스크시트","시트팩"],
    "바구니":   ["바스켓","정리함","수납함","트레이"],
    "행거":     ["스탠드행거","빨래걸이"],
    "압축봉":   ["욕실봉","샤워커튼봉","수납봉"],
    "매트":     ["발매트","욕실매트","미끄럼방지매트"],
    "충전기":   ["어댑터","충전어댑터","멀티충전기"],
    "케이블":   ["충전선","USB선","C타입선","라이트닝"],
    "집게":     ["빨래집게","클립집게","자석집게"],
    "지퍼백":   ["비닐백","보관백","냉동백"],
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

def is_complaint(text, brand):
    return (brand.lower() in text.lower()
            and any(kw in text for kw in PRODUCT_KEYWORDS)
            and any(kw in text for kw in COMPLAINT_KEYWORDS))

# ============================
# 검색어 적정성 검사
# ============================
def check_query(query):
    warnings, suggestions = [], []
    brand = query.split()[0]
    if len(brand) < 2:
        warnings.append("브랜드명이 너무 짧아요")
    if not any(h in query for h in ["불만","불량","후기","리뷰","문제","이상"]):
        suggestions.append(f'💡 추천: **"{brand} 불만"** 또는 **"{brand} 불량 후기"**')
    if len(query.strip()) > 20:
        warnings.append("검색어가 너무 길면 결과가 적을 수 있어요")
    return warnings, suggestions

# ============================
# 2차: AI 감성 분석
# ============================
@st.cache_resource
def load_model():
    return pipeline("sentiment-analysis", model="snunlp/KR-ELECTRA-SC",
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
    "품질불량": ["불량","파손","깨짐","터짐","찢어짐","벗겨짐","고장","녹","곰팡이","변형","휘어짐","부러짐","갈라짐","오염","불량품"],
    "안전성":   ["유해","위험","냄새","악취","화학","독성","알레르기","피부트러블","가려움","발진","환경호르몬","납","중금속"],
    "스펙불일치":["작다","크다","짧다","길다","무겁다","가볍다","두껍다","얇다","생각보다","예상보다","사진과 다름","실물과 다름","색이 다름","크기가 다름"],
    "내구성":   ["약하다","금방","며칠만에","하루만에","한달도","바로","얼마안가","금방망가","쉽게망가","오래못감","질이나쁨"],
    "구매경험": ["환불","반품","교환","불친절","응대","서비스","AS","품절","재고없음","구하기힘듦","단종","배송"],
    "가성비":   ["비싸다","가격대비","돈낭비","아깝다","손해","바가지","가성비나쁨","비쌈","돈이아깝"]
}

def classify_type(text):
    matched = [t for t, kws in COMPLAINT_TYPES.items() if any(kw in text for kw in kws)]
    return ", ".join(matched[:2]) if matched else "기타불만"

# ============================
# 3차: 상품명 추출
# ============================
STOPWORDS = {
    "다이소","구매","후기","리뷰","사용","제품","상품","추천","가격","할인",
    "불만","불량","고장","파손","이거","저거","이것","저것","그것","여기","거기",
    "해당","관련","같은","어떤","이런","저런","그런","모든","일부","전체","보면","대한",
    "한국","일본","중국","온라인","오프라인","매장","블로그","지식인"
}

def extract_product(text, brand="다이소"):
    for p in PRODUCT_DICT:
        if p in text: return p
    for key, synonyms in SYNONYM_DICT.items():
        for s in synonyms:
            if s in text: return key
    m = re.search(rf'{brand}\s+([가-힣]{{2,8}})(?=\s|$|[이을를의은는가])', text)
    if m and m.group(1) not in STOPWORDS: return m.group(1)
    m = re.search(r'([가-힣]{2,8})\s+(?:후기|리뷰|불량|파손|고장|불만)(?:\s|$|[이을를])', text)
    if m and m.group(1) not in STOPWORDS: return m.group(1)
    return ""

def extract_info(text):
    codes  = re.findall(r'(?<![0-9,원])\b\d{5,10}\b(?!\d)(?![\d,]*원)', text)
    prices = re.findall(r'\d{1,3}(?:,\d{3})*원', text)
    return {"품번": ", ".join(list(dict.fromkeys(codes))[:3]), "가격": ", ".join(set(prices))}

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
            for item in batch: item["출처"] = "블로그" if type_ == "blog" else "지식인"
            items += batch
        except Exception as e:
            st.warning(f"수집 오류: {e}"); break
        start += fetch
    return items

# ============================
# 날짜 파싱
# ============================
def parse_date(item):
    d = item.get("postdate") or item.get("pubDate", "")
    if not d: return None
    try:
        if len(d) == 8: return datetime.strptime(d, "%Y%m%d")
        elif "," in d: return datetime.strptime(d[:22].strip(), "%a, %d %b %Y")
        elif len(d) >= 10: return datetime.strptime(d[:10], "%Y-%m-%d")
    except:
        try:
            p = d.split()
            if len(p) >= 4: return datetime.strptime(f"{p[1]} {p[2]} {p[3]}", "%d %b %Y")
        except: pass
    return None

def filter_by_date(items, start, end):
    s, e = datetime.strptime(start, "%Y%m%d"), datetime.strptime(end, "%Y%m%d")
    result = []
    for item in items:
        dt = parse_date(item)
        if dt is None or s <= dt <= e: result.append(item)
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
                ["빈칸","확인 안 함 (미사용)",""],[],["목표","1+0 합쳐서 200개 이상 → 파인튜닝 가능"]]:
        ws2.append(row)
    ws2.column_dimensions["A"].width = 15
    ws2.column_dimensions["B"].width = 35
    ws2.column_dimensions["C"].width = 40
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
st.caption("🤖 KR-ELECTRA-SC  |  1차 불만필터 → 2차 감성분석 → 3차 상품명+유형분류")
st.divider()

with st.sidebar:
    st.header("[분석 조건 설정]")

    st.markdown("**🔎 검색어**")
    st.caption("검색어를 입력하세요")
    query = st.text_input("검색어 입력", value="다이소 불만", label_visibility="collapsed")

    if query:
        warnings, suggestions = check_query(query)
        for w in warnings: st.warning(f"⚠️ {w}")
        for s in suggestions: st.info(s)
        if not warnings and not suggestions: st.success("✅ 검색 가능")

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
            b = search_naver(query, "blog", display_count); all_items += b; st.info(f"블로그 {len(b)}개")
        if do_kin:
            k = search_naver(query, "kin", display_count); all_items += k; st.info(f"지식인 {len(k)}개")

    filtered = filter_by_date(all_items, start_date, end_date)
    st.write(f"📅 날짜 필터 후: **{len(filtered)}개**")
    if not filtered: st.warning("해당 기간에 결과가 없습니다."); st.stop()

    brand, results, skipped = query.split()[0], [], 0
    prog = st.progress(0, text="분석 중...")

    for i, item in enumerate(filtered):
        text = re.sub(r'<[^>]+>', '', item.get("title","") + " " + item.get("description","")).strip()

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
            "출처": item["출처"], "품명": product,
            "title": re.sub(r'<[^>]+>', '', item.get("title","")),
            "link": item.get("link",""),
            "날짜": dt.strftime("%Y-%m-%d") if dt else "",
            "감성": senti, "확신도": score, "불만유형": ctype, **info
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
