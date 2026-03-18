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
    page_title="네이버 리뷰 AI 감성분석기",
    page_icon="🔍",
    layout="wide"
)

# ============================
# 비밀번호 체크 (가장 먼저!)
# ============================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("## 🔐 로그인")
    pw = st.text_input("비밀번호를 입력하세요", type="password")

    if st.button("입력"):
        if pw == st.secrets["PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")
    return False

if not check_password():
    st.stop()  # 비밀번호 맞은 사람만 아래 내용을 볼 수 있음


# ============================
# API 키 (코드에 노출 없이 secrets에서 읽기)
# ============================
NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]


# ============================
# AI 모델 로드 (처음 한 번만)
# ============================
@st.cache_resource
def load_model():
    return pipeline(
        "sentiment-analysis",
        model="snunlp/KR-FinBert-SC"
    )


# ============================
# 네이버 검색
# ============================
def search_naver(query, search_type="blog", display=100):
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": display, "sort": "date"}
    response = requests.get(url, headers=headers, params=params)
    items = response.json().get("items", [])
    for item in items:
        item["출처"] = "블로그" if search_type == "blog" else "지식인"
    return items


# ============================
# 텍스트 정제
# ============================
def clean_text(text):
    return re.sub(r'<[^>]+>', '', text).strip()


# ============================
# 날짜 파싱 & 필터링
# ============================
def parse_date(item):
    date_str = item.get("postdate") or item.get("pubDate", "")
    try:
        if len(date_str) == 8:
            return datetime.strptime(date_str, "%Y%m%d")
        else:
            return datetime.strptime(date_str[:16], "%a, %d %b %Y")
    except:
        return None


def filter_by_date(items, start, end):
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")
    return [
        item for item in items
        if parse_date(item) and start_dt <= parse_date(item) <= end_dt
    ]


# ============================
# AI 감성 분석
# ============================
def ai_sentiment(text, model):
    text = text[:512]
    try:
        result = model(text)[0]
        label = result["label"]
        score = round(result["score"] * 100, 1)
        if label == "positive":
            return "호평", score
        elif label == "negative":
            return "악평", score
        else:
            return "중립", score
    except:
        return "분석불가", 0.0


# ============================
# 품번 / 품명 / 가격 추출
# ============================
def extract_product_info(text, query_brand="다이소"):
    code_pattern = r'[A-Za-z]{1,3}[-_]?\d{3,6}|NO\.?\d{2,5}'
    codes = re.findall(code_pattern, text)

    price_pattern = r'\d{1,3}(?:,\d{3})*원'
    prices = re.findall(price_pattern, text)

    name_pattern = rf'{query_brand}\s+([가-힣\s]{{2,12}})'
    names = re.findall(name_pattern, text)

    review_pattern = r'([가-힣]{2,8})\s*(?:구매|후기|리뷰|사용)'
    review_names = re.findall(review_pattern, text)

    all_names = list(dict.fromkeys(names + review_names))[:3]

    return {
        "품번": ", ".join(set(codes)) if codes else "",
        "가격언급": ", ".join(set(prices)) if prices else "",
        "품명추출": ", ".join(all_names) if all_names else ""
    }


# ============================
# 엑셀 생성 (파일로 저장 아닌 메모리로)
# ============================
def create_excel(data, query, start_date, end_date):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AI 리뷰 분석"

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

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 40
    ws.column_dimensions["F"].width = 50
    ws.column_dimensions["G"].width = 12
    ws.column_dimensions["H"].width = 10
    ws.column_dimensions["I"].width = 12

    # 메모리에 저장 후 반환
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ============================
# 메인 UI
# ============================
st.title("🔍 네이버 리뷰 AI 감성분석기")
st.markdown("블로그·지식인 리뷰를 수집하고 AI로 감성을 자동 분석합니다.")
st.divider()

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 분석 설정")
    query = st.text_input("🔎 검색어", value="다이소 상품 리뷰")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.text_input("시작일", value="20250101", help="YYYYMMDD 형식")
    with col2:
        end_date = st.text_input("종료일", value="20250317", help="YYYYMMDD 형식")

    search_blog = st.checkbox("블로그 수집", value=True)
    search_kin = st.checkbox("지식인 수집", value=True)
    display_count = st.slider("수집 개수 (최대)", 10, 100, 100, step=10)

    run_btn = st.button("🚀 분석 시작", use_container_width=True, type="primary")

# 분석 실행
if run_btn:
    if not query:
        st.error("검색어를 입력해주세요!")
        st.stop()

    if not search_blog and not search_kin:
        st.error("블로그 또는 지식인 중 하나는 선택해주세요!")
        st.stop()

    with st.spinner("🤖 AI 모델 로딩 중... (처음 실행 시 약 1~2분 소요)"):
        sentiment_model = load_model()

    # 수집
    all_items = []
    with st.spinner("📡 데이터 수집 중..."):
        if search_blog:
            blog_items = search_naver(query, "blog", display_count)
            all_items += blog_items
            st.info(f"블로그 {len(blog_items)}개 수집 완료")

        if search_kin:
            kin_items = search_naver(query, "kin", display_count)
            all_items += kin_items
            st.info(f"지식인 {len(kin_items)}개 수집 완료")

    # 날짜 필터
    filtered = filter_by_date(all_items, start_date, end_date)
    st.write(f"📅 날짜 필터 후: **{len(filtered)}개**")

    if not filtered:
        st.warning("⚠️ 해당 기간에 결과가 없어요. 날짜 범위를 넓혀보세요!")
        st.stop()

    # 분석
    brand = query.split()[0]
    results = []
    progress = st.progress(0, text="분석 중...")

    for i, item in enumerate(filtered):
        title = clean_text(item.get("title", ""))
        desc = clean_text(item.get("description", ""))
        full_text = title + " " + desc

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
    st.success(f"✅ 분석 완료! 총 {len(results)}개")
    st.divider()

    # 요약 지표
    total = len(results)
    pos = sum(1 for r in results if r["감성"] == "호평")
    neg = sum(1 for r in results if r["감성"] == "악평")
    neu = sum(1 for r in results if r["감성"] == "중립")

    st.subheader("📊 분석 요약")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체", f"{total}개")
    c2.metric("호평 😊", f"{pos}개", f"{round(pos/total*100)}%")
    c3.metric("악평 😞", f"{neg}개", f"{round(neg/total*100)}%")
    c4.metric("중립 😐", f"{neu}개", f"{round(neu/total*100)}%")

    # 많이 언급된 품명
    all_names = []
    for r in results:
        if r["품명추출"]:
            all_names.extend(r["품명추출"].split(", "))

    if all_names:
        st.subheader("🏷️ 많이 언급된 품명 TOP 5")
        top_names = Counter(all_names).most_common(5)
        for name, count in top_names:
            st.write(f"  **{name}**: {count}회")

    # 결과 테이블
    st.subheader("📋 상세 결과")
    import pandas as pd
    df = pd.DataFrame(results)
    df = df.rename(columns={
        "출처": "출처", "title": "제목", "link": "링크",
        "날짜": "날짜", "감성": "감성", "확신도": "확신도(%)",
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

    # 엑셀 다운로드
    st.subheader("💾 결과 다운로드")
    excel_buffer = create_excel(results, query, start_date, end_date)
    st.download_button(
        label="📥 엑셀 파일 다운로드",
        data=excel_buffer,
        file_name=f"AI리뷰분석_{query[:5]}_{start_date}_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
