import streamlit as st
import requests
import openpyxl
import re
import io
from datetime import datetime
from transformers import pipeline
from collections import Counter

# ============================
# 페이지 설정
# ============================
st.set_page_config(
    page_title="🤬네이버 고객품질불만 AI분석기 by PC",
    page_icon="🔍",
    layout="wide"
)

# ============================
# 비밀번호 체크
# ============================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.markdown("## LOG IN")
    pw = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("입력"):
        if pw == st.secrets["PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")
    return False

if not check_password():
    st.stop()

# ============================
# API 키
# ============================
NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

# ============================
# 불만 필터 키워드
# ============================
COMPLAINT_KEYWORDS = [
    "불만", "불편", "별로", "실망", "최악", "나쁨", "후회", "환불",
    "불량", "파손", "고장", "터짐", "깨짐", "냄새", "이상", "문제",
    "아쉽", "싸구려", "저품질", "흠", "짧다", "작다", "크다",
    "무겁다", "약하다", "얇다", "두껍다", "불량품", "반품", "교환",
    "불편하다", "위험", "유해", "녹", "곰팡이", "찢어짐", "벗겨짐", "비추"
]

PRODUCT_KEYWORDS = [
    "샀", "구매", "구입", "제품", "상품", "사용", "써봤", "써보니",
    "개봉", "사봤", "가격", "원짜리", "원에", "원인데", "후기", "리뷰"
]

# ============================
# 관련성 필터
# ============================
def is_relevant(text, brand):
    has_brand = brand.lower() in text.lower()
    has_product = any(kw in text for kw in PRODUCT_KEYWORDS)
    has_complaint = any(kw in text for kw in COMPLAINT_KEYWORDS)
    return has_brand and has_product and has_complaint

# ============================
# AI 모델 로드 — KR-ELECTRA (업그레이드)
# ============================
@st.cache_resource
def load_model():
    # KR-ELECTRA 기반 한국어 감성분석 모델
    return pipeline(
        "sentiment-analysis",
        model="monologg/koelectra-base-finetuned-sentiment",
        truncation=True,
        max_length=512
    )

# ============================
# 네이버 검색 (페이징 최대 1000건)
# ============================
def search_naver(query, search_type="blog", display=100):
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    all_items = []
    start = 1
    while start <= display:
        fetch = min(100, display - start + 1)
        params = {"query": query, "display": fetch, "start": start, "sort": "date"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            items = response.json().get("items", [])
            if not items:
                break
            for item in items:
                item["출처"] = "블로그" if search_type == "blog" else "지식인"
            all_items += items
        except Exception as e:
            st.warning(f"수집 오류 (start={start}): {e}")
            break
        start += fetch
    return all_items

# ============================
# 텍스트 정제
# ============================
def clean_text(text):
    return re.sub(r'<[^>]+>', '', text).strip()

# ============================
# 날짜 파싱
# ============================
def parse_date(item):
    date_str = item.get("postdate") or item.get("pubDate", "")
    if not date_str:
        return None
    try:
        if len(date_str) == 8:
            return datetime.strptime(date_str, "%Y%m%d")
        elif "," in date_str:
            return datetime.strptime(date_str[:16], "%a, %d %b %Y")
        elif len(date_str) >= 10:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except:
        return None

# ============================
# 날짜 필터링
# ============================
def filter_by_date(items, start, end):
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")
    result = []
    for item in items:
        dt = parse_date(item)
        if dt is None:
            result.append(item)
        elif start_dt <= dt <= end_dt:
            result.append(item)
    return result

# ============================
# AI 감성 분석 (ELECTRA 라벨 매핑)
# ============================
def ai_sentiment(text, model):
    try:
        result = model(text[:512])[0]
        label = result["label"].lower()
        score = round(result["score"] * 100, 1)

        # koelectra-base-finetuned-sentiment 라벨: 0=부정, 1=긍정
        if label in ["positive", "1", "pos"]:
            return "호평", score
        elif label in ["negative", "0", "neg"]:
            return "악평", score
        else:
            return "중립", score
    except:
        return "분석불가", 0.0

# ============================
# 품번 / 품명 / 가격 추출
# ============================
def extract_product_info(text, query_brand="다이소"):
    # 품번: 5~10자리 연속 숫자 (가격 숫자 제외)
    code_pattern = r'(?<!\d)\d{5,10}(?!\d)(?!원)'
    codes = [c for c in re.findall(code_pattern, text)
             if not text[text.find(c):text.find(c)+len(c)+1].endswith("원")]

    # 가격 패턴
    price_pattern = r'\d{1,3}(?:,\d{3})*원'
    prices = re.findall(price_pattern, text)

    # 품명: 불만/후기/리뷰/사용 앞에 오는 한글 명사
    name_pattern = r'([가-힣]{2,10})\s*(?:불만|불량|파손|고장|후기|리뷰|사용기|사용|제품|상품)'
    names = re.findall(name_pattern, text)

    # 브랜드명 뒤에 오는 품명
    brand_pattern = rf'{query_brand}\s+([가-힣]{{2,10}})'
    brand_names = re.findall(brand_pattern, text)

    stopwords = {
        query_brand, "다이소", "구매", "후기", "리뷰", "사용", "제품",
        "상품", "추천", "가격", "할인", "불만", "불량", "고장", "파손"
    }
    all_names = [n for n in list(dict.fromkeys(brand_names + names))
                 if n not in stopwords][:3]

    return {
        "품번": ", ".join(list(dict.fromkeys(codes))[:3]) if codes else "",
        "가격언급": ", ".join(set(prices)) if prices else "",
        "품명추출": ", ".join(all_names) if all_names else ""
    }

# ============================
# 엑셀 생성
# ============================
def create_excel(data, query, start_date, end_date):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AI 불만 분석"

    headers = ["출처", "품명추출", "품번", "가격언급", "제목", "링크", "날짜", "감성", "확신도(%)"]
    ws.append(headers)

    for col in range(1, len(headers) + 1):
        ws.cell(row=1, column=col).font = openpyxl.styles.Font(bold=True)
        ws.cell(row=1, column=col).fill = openpyxl.styles.PatternFill(
            start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"
        )

    color_map = {
        "호평": "C6EFCE",
        "악평": "FFC7CE",
        "중립": "FFEB9C",
        "분석불가": "D9D9D9"
    }

    for row_idx, row in enumerate(data, start=2):
        ws.append([
            row["출처"], row["품명추출"], row["품번"], row["가격언급"],
            row["title"], row["link"], row["날짜"], row["감성"], row["확신도"]
        ])
        fill_color = color_map.get(row["감성"], "FFFFFF")
        ws.cell(row=row_idx, column=8).fill = openpyxl.styles.PatternFill(
            start_color=fill_color, end_color=fill_color, fill_type="solid"
        )

    for col, width in zip("ABCDEFGHI", [10, 20, 15, 15, 40, 50, 12, 10, 12]):
        ws.column_dimensions[col].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

# ============================
# 메인 UI
# ============================
st.title("🤬 네이버 고객품질불만 AI분석기 by PC")
st.markdown("블로그·지식인에서 **불만 후기만** 수집하고 AI로 감성을 자동 분석합니다.")
st.caption("🤖 AI 모델: koelectra-base-finetuned-sentiment")
st.divider()

with st.sidebar:
    st.header("⚙️ 분석 설정")
    query = st.text_input("🔎 검색어 (브랜드명 포함)", value="다이소 상품 불만")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.text_input("시작일", value="20250101", help="YYYYMMDD 형식")
    with col2:
        end_date = st.text_input("종료일", value="20260101", help="YYYYMMDD 형식")

    search_blog = st.checkbox("블로그 수집", value=True)
    search_kin = st.checkbox("지식인 수집", value=True)
    display_count = st.slider("수집 개수 (최대)", 100, 1000, 100, step=100)

    run_btn = st.button("🐎 분석 시작", use_container_width=True, type="primary")

if run_btn:
    if not query:
        st.error("검색어를 입력하세요")
        st.stop()
    if not search_blog and not search_kin:
        st.error("블로그 또는 지식인 중 하나는 선택해주세요!")
        st.stop()

    with st.spinner("🤖 AI 모델 로딩 중... (처음 실행 시 1~2분 소요)"):
        sentiment_model = load_model()

    all_items = []
    with st.spinner("📡 데이터 수집 중..."):
        if search_blog:
            blog_items = search_naver(query, "blog", display_count)
            all_items += blog_items
            st.info(f"블로그 {len(blog_items)}개 수집")
        if search_kin:
            kin_items = search_naver(query, "kin", display_count)
            all_items += kin_items
            st.info(f"지식인 {len(kin_items)}개 수집")

    filtered = filter_by_date(all_items, start_date, end_date)
    st.write(f"📅 날짜 필터 후: **{len(filtered)}개**")

    if not filtered:
        st.warning("⚠️ 해당 기간에 결과가 없습니다.")
        st.stop()

    brand = query.split()[0]
    results = []
    skipped = 0
    progress = st.progress(0, text="분석 중...")

    for i, item in enumerate(filtered):
        title = clean_text(item.get("title", ""))
        desc = clean_text(item.get("description", ""))
        full_text = title + " " + desc

        if not is_relevant(full_text, brand):
            skipped += 1
            progress.progress((i + 1) / len(filtered), text=f"필터링 중... ({i+1}/{len(filtered)})")
            continue

        sentiment, score = ai_sentiment(full_text, sentiment_model)
        product_info = extract_product_info(full_text, query_brand=brand)
        dt = parse_date(item)
        date_str = dt.strftime("%Y-%m-%d") if dt else ""

        results.append({
            "출처": item["출처"],
            "title": title,
            "link": item.get("link", ""),
            "날짜": date_str,
            "감성": sentiment,
            "확신도": score,
            **product_info
        })

        progress.progress((i + 1) / len(filtered), text=f"분석 중... ({i+1}/{len(filtered)})")

    progress.empty()
    st.success(f"✅ 분석 완료! 불만 관련 {len(results)}개 (무관련 {skipped}개 제외)")
    st.divider()

    if not results:
        st.warning("불만 관련 글이 없습니다. 검색어를 바꿔보세요!")
        st.stop()

    total = len(results)
    pos = sum(1 for r in results if r["감성"] == "호평")
    neg = sum(1 for r in results if r["감성"] == "악평")
    neu = sum(1 for r in results if r["감성"] == "중립")

    st.subheader("📊 분석 요약")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("불만 관련 전체", f"{total}개")
    c2.metric("호평 😊", f"{pos}개", f"{round(pos/total*100)}%")
    c3.metric("악평 😞", f"{neg}개", f"{round(neg/total*100)}%")
    c4.metric("중립 😐", f"{neu}개", f"{round(neu/total*100)}%")

    all_names = []
    for r in results:
        if r["품명추출"]:
            all_names.extend(r["품명추출"].split(", "))
    if all_names:
        st.subheader("🏷️ 많이 언급된 품명 TOP 5")
        for name, count in Counter(all_names).most_common(5):
            st.write(f"**{name}**: {count}회")

    st.subheader("📋 상세 결과")
    import pandas as pd
    df = pd.DataFrame(results)
    df = df.rename(columns={
        "title": "제목", "link": "링크", "날짜": "날짜",
        "감성": "감성", "확신도": "확신도(%)",
        "품명추출": "품명", "품번": "품번", "가격언급": "가격"
    })

    def highlight_sentiment(val):
        color_map = {"호평": "#C6EFCE", "악평": "#FFC7CE", "중립": "#FFEB9C"}
        return f"background-color: {color_map.get(val, '')}"

    st.dataframe(
        df[["출처", "품명", "품번", "가격", "제목", "날짜", "감성", "확신도(%)"]].style.applymap(
            highlight_sentiment, subset=["감성"]
        ),
        use_container_width=True,
        height=400
    )

    st.subheader("💾 결과 다운로드")
    excel_buffer = create_excel(results, query, start_date, end_date)
    st.download_button(
        label="📥 엑셀 파일 다운로드",
        data=excel_buffer,
        file_name=f"불만분석_{query[:5]}_{start_date}_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
