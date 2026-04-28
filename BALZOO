import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import re
from PIL import Image
import requests
from io import BytesIO

# ─── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="발주관리표",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 13px;
  }

  /* 전체 배경 */
  .stApp { background: #f0f2f5; }

  /* 헤더 */
  .page-header {
    background: linear-gradient(135deg, #1a3a5c 0%, #2d6a9f 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 10px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  .page-header h1 { font-size: 1.3rem; font-weight: 700; margin: 0; }

  /* 필터 카드 */
  .filter-card {
    background: white;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #e8ecf0;
  }
  .filter-card h3 {
    font-size: 0.78rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 10px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #e8f0fe;
  }

  /* selectbox / multiselect */
  .stSelectbox > div > div,
  .stMultiSelect > div > div {
    border-radius: 7px !important;
    border-color: #d1d5db !important;
    font-size: 13px !important;
  }

  /* 조회 버튼 */
  div.stButton > button {
    background: linear-gradient(135deg, #1a3a5c, #2d6a9f);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.8rem;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    box-shadow: 0 3px 8px rgba(26,58,92,0.3);
    transition: all 0.2s;
  }
  div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(26,58,92,0.4);
  }

  /* 결과 카드 */
  .result-card {
    background: white;
    border-radius: 10px;
    padding: 16px;
    margin-top: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #e8ecf0;
  }
  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  .result-count {
    background: #e8f0fe;
    color: #1a3a5c;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
  }

  /* 상품 행 */
  .product-block {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-bottom: 14px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  }

  /* 상품 기본정보 헤더 */
  .product-info-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    flex-wrap: wrap;
  }
  .seq-badge {
    background: #1a3a5c;
    color: white;
    border-radius: 50%;
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
  }
  .status-badge {
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
  }
  .status-신상품 { background: #dcfce7; color: #166534; }
  .status-단종대기 { background: #fee2e2; color: #991b1b; }
  .status-정상 { background: #e0f2fe; color: #075985; }
  .status-기타 { background: #f3f4f6; color: #374151; }

  .prod-code { font-family: monospace; font-size: 12px; color: #6b7280; }
  .prod-name { font-weight: 600; color: #1e293b; font-size: 13px; }
  .prod-meta { font-size: 11px; color: #94a3b8; }
  .prod-price { font-weight: 700; color: #1a3a5c; font-size: 13px; }

  /* 월별 데이터 테이블 */
  .monthly-table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  table.monthly-tbl {
    border-collapse: collapse;
    width: 100%;
    font-size: 11.5px;
  }
  table.monthly-tbl th {
    background: #1a3a5c;
    color: white;
    padding: 5px 8px;
    text-align: center;
    white-space: nowrap;
    font-weight: 500;
    position: sticky;
    top: 0;
    z-index: 1;
  }
  table.monthly-tbl th.row-label-col {
    background: #2d3748;
    min-width: 70px;
  }
  table.monthly-tbl td {
    padding: 4px 7px;
    text-align: right;
    border: 1px solid #e2e8f0;
    white-space: nowrap;
  }
  table.monthly-tbl td.row-label {
    text-align: left;
    font-weight: 600;
    background: #f8fafc;
    color: #374151;
    font-size: 11px;
    border-right: 2px solid #cbd5e1;
  }
  table.monthly-tbl tr.row-pos td { background: #fff1f2; }
  table.monthly-tbl tr.row-pos td.row-label { background: #ffe4e6; color: #be123c; }
  table.monthly-tbl tr:hover td { filter: brightness(0.97); }
  table.monthly-tbl td.zero { color: #cbd5e1; }
  table.monthly-tbl td.positive { color: #1e40af; font-weight: 500; }

  /* 상품 이미지 */
  .prod-img {
    width: 52px;
    height: 52px;
    object-fit: contain;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
    background: white;
    flex-shrink: 0;
  }
  .prod-img-placeholder {
    width: 52px;
    height: 52px;
    background: #f1f5f9;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
  }

  /* 아이패드 최적화 */
  @media (max-width: 1024px) {
    html, body, [class*="css"] { font-size: 12px; }
    .product-info-bar { gap: 8px; }
    table.monthly-tbl th, table.monthly-tbl td { padding: 4px 5px; font-size: 10.5px; }
  }

  /* 로딩 스피너 숨김 */
  div[data-testid="stStatusWidget"] { display: none; }

  /* 구분선 */
  hr { border: none; border-top: 1px solid #e2e8f0; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)


# ─── Google Sheets 연결 ──────────────────────────────────────────
SHEET_ID = "1MZrzRkcbA7tcF8GiP5iQGOAWRtwfxyL3-_4h2-2k76o"

@st.cache_resource(ttl=300)
def get_gsheet_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_data():
    try:
        client = get_gsheet_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.get_worksheet(0)
        data = ws.get_all_values()
        if not data or len(data) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Google Sheets 연결 오류: {e}")
        return pd.DataFrame()


# ─── 월 컬럼 목록 생성 (24/11 ~ 26/04) ─────────────────────────
def gen_month_labels():
    months = []
    for y in range(24, 27):
        for m in range(1, 13):
            lbl = f"{y:02d}/{m:02d}"
            months.append(lbl)
            if y == 26 and m == 4:
                return months
    return months

ALL_MONTHS = gen_month_labels()

ROW_TYPES = ["발주", "입고", "출고", "POS판매", "물류재고", "매장재고", "보유매장", "미입고"]

INFO_COLS = ["발주주체", "발주구분", "품번", "품번2", "품명", "대분류", "중분류", "소분류",
             "담당", "관계사팀", "중포", "카톤", "등급", "상태", "업체명", "산지",
             "구입가", "판매가", "정상재고", "일출고량", "미입고", "입고예정",
             "사진주소", "S/N단가_통화", "S/N단가_금액", "S/N단가_재고일"]


def get_col(df, name):
    """컬럼명이 약간 다를 수 있어서 유사 매칭"""
    if name in df.columns:
        return name
    for c in df.columns:
        if name in c or c in name:
            return c
    return None


def get_monthly_val(row, row_type, month):
    col = f"{row_type}_{month}"
    if col in row.index:
        v = row[col]
        try:
            return int(float(str(v).replace(",", ""))) if v not in ("", None) else 0
        except:
            return 0
    return 0


# ─── 헤더 ───────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <span style="font-size:1.5rem">📦</span>
  <h1>발주관리표</h1>
</div>
""", unsafe_allow_html=True)

# ─── 데이터 로드 ─────────────────────────────────────────────────
with st.spinner("데이터 불러오는 중..."):
    df_raw = load_data()

if df_raw.empty:
    st.warning("데이터가 없습니다. Google Sheets 연결 및 데이터를 확인해주세요.")
    st.stop()

# ─── 컬럼명 파악 ─────────────────────────────────────────────────
col_담당 = get_col(df_raw, "담당")
col_대분류 = get_col(df_raw, "대분류")
col_중분류 = get_col(df_raw, "중분류")
col_소분류 = get_col(df_raw, "소분류")
col_품명 = get_col(df_raw, "품명")
col_품번 = get_col(df_raw, "품번")
col_상태 = get_col(df_raw, "상태")
col_발주주체 = get_col(df_raw, "발주주체")
col_발주구분 = get_col(df_raw, "발주구분")
col_판매가 = get_col(df_raw, "판매가")
col_구입가 = get_col(df_raw, "구입가")
col_사진주소 = get_col(df_raw, "사진주소")
col_업체명 = get_col(df_raw, "업체명")

# ─── 필터 UI ────────────────────────────────────────────────────
st.markdown('<div class="filter-card"><h3>🔍 조회 조건</h3>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])

with c1:
    담당_options = ["전체"]
    if col_담당:
        vals = sorted(df_raw[col_담당].dropna().unique().tolist())
        담당_options += [v for v in vals if v.strip()]
    sel_담당 = st.selectbox("담당자", 담당_options)

with c2:
    대분류_options = ["전체"]
    if col_대분류:
        vals = sorted(df_raw[col_대분류].dropna().unique().tolist())
        대분류_options += [v for v in vals if v.strip()]
    sel_대분류 = st.selectbox("대분류", 대분류_options)

with c3:
    중분류_options = ["전체"]
    if col_중분류:
        df_f = df_raw if sel_대분류 == "전체" else df_raw[df_raw[col_대분류] == sel_대분류]
        vals = sorted(df_f[col_중분류].dropna().unique().tolist())
        중분류_options += [v for v in vals if v.strip()]
    sel_중분류 = st.selectbox("중분류", 중분류_options)

with c4:
    소분류_options = ["전체"]
    if col_소분류:
        df_f2 = df_raw.copy()
        if sel_대분류 != "전체" and col_대분류:
            df_f2 = df_f2[df_f2[col_대분류] == sel_대분류]
        if sel_중분류 != "전체" and col_중분류:
            df_f2 = df_f2[df_f2[col_중분류] == sel_중분류]
        vals = sorted(df_f2[col_소분류].dropna().unique().tolist())
        소분류_options += [v for v in vals if v.strip()]
    sel_소분류 = st.selectbox("소분류", 소분류_options)

st.markdown('</div>', unsafe_allow_html=True)

_, btn_col, _ = st.columns([3, 1, 3])
with btn_col:
    search_btn = st.button("🔍 조회", use_container_width=True)

# ─── 필터 적용 ──────────────────────────────────────────────────
df = df_raw.copy()
if sel_담당 != "전체" and col_담당:
    df = df[df[col_담당] == sel_담당]
if sel_대분류 != "전체" and col_대분류:
    df = df[df[col_대분류] == sel_대분류]
if sel_중분류 != "전체" and col_중분류:
    df = df[df[col_중분류] == sel_중분류]
if sel_소분류 != "전체" and col_소분류:
    df = df[df[col_소분류] == sel_소분류]
df = df.reset_index(drop=True)

# ─── 결과 표시 ───────────────────────────────────────────────────
st.markdown(f"""
<div class="result-card">
  <div class="result-header">
    <span style="font-weight:700;color:#1a3a5c;font-size:14px">📋 조회 결과</span>
    <span class="result-count">총 {len(df)}개 상품</span>
  </div>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.info("조회 결과가 없습니다.")
    st.stop()

# ─── 월 범위 선택 ────────────────────────────────────────────────
with st.expander("📅 조회 월 범위 선택", expanded=False):
    mc1, mc2 = st.columns(2)
    with mc1:
        start_month = st.selectbox("시작 월", ALL_MONTHS, index=max(0, len(ALL_MONTHS)-6))
    with mc2:
        end_month = st.selectbox("종료 월", ALL_MONTHS, index=len(ALL_MONTHS)-1)

si = ALL_MONTHS.index(start_month) if start_month in ALL_MONTHS else 0
ei = ALL_MONTHS.index(end_month) if end_month in ALL_MONTHS else len(ALL_MONTHS)-1
if si > ei:
    si, ei = ei, si
sel_months = ALL_MONTHS[si:ei+1]


# ─── 월별 테이블 HTML 생성 ──────────────────────────────────────
def make_monthly_table(row, months):
    th_style = ""
    # 헤더 행
    ths = '<th class="row-label-col">구분</th>'
    for m in months:
        ths += f'<th>{m}</th>'

    rows_html = ""
    for rt in ROW_TYPES:
        is_pos = rt == "POS판매"
        tr_class = ' class="row-pos"' if is_pos else ''
        cells = f'<td class="row-label">{rt}</td>'
        for m in months:
            v = get_monthly_val(row, rt, m)
            td_class = "zero" if v == 0 else "positive"
            display = str(v) if v != 0 else "0"
            cells += f'<td class="{td_class}">{display}</td>'
        rows_html += f'<tr{tr_class}>{cells}</tr>'

    return f"""
    <div class="monthly-table-wrap">
      <table class="monthly-tbl">
        <thead><tr>{ths}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """


# ─── 각 상품 렌더링 ─────────────────────────────────────────────
for idx, row in df.iterrows():
    품명 = row[col_품명] if col_품명 else ""
    품번 = row[col_품번] if col_품번 else ""
    상태 = row[col_상태] if col_상태 else ""
    발주주체 = row[col_발주주체] if col_발주주체 else ""
    발주구분 = row[col_발주구분] if col_발주구분 else ""
    판매가 = row[col_판매가] if col_판매가 else ""
    구입가 = row[col_구입가] if col_구입가 else ""
    업체명 = row[col_업체명] if col_업체명 else ""
    사진주소 = row[col_사진주소] if col_사진주소 else ""
    대분류_val = row[col_대분류] if col_대분류 else ""
    중분류_val = row[col_중분류] if col_중분류 else ""
    소분류_val = row[col_소분류] if col_소분류 else ""
    담당_val = row[col_담당] if col_담당 else ""

    status_cls = {
        "신상품": "status-신상품",
        "단종대기": "status-단종대기",
        "정상": "status-정상",
    }.get(상태, "status-기타")

    # 이미지
    img_html = ""
    if 사진주소 and str(사진주소).startswith("http"):
        img_html = f'<img class="prod-img" src="{사진주소}" onerror="this.style.display=\'none\'" />'
    else:
        img_html = '<div class="prod-img-placeholder">📦</div>'

    table_html = make_monthly_table(row, sel_months)

    block_html = f"""
    <div class="product-block">
      <div class="product-info-bar">
        <div class="seq-badge">{idx+1}</div>
        {img_html}
        <div style="display:flex;flex-direction:column;gap:3px;flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span class="prod-code">{품번}</span>
            <span class="status-badge {status_cls}">{상태}</span>
            <span class="prod-meta">{발주주체} · {발주구분}</span>
          </div>
          <div class="prod-name" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{품명}</div>
          <div class="prod-meta">{대분류_val} &gt; {중분류_val} &gt; {소분류_val} &nbsp;|&nbsp; 담당: {담당_val} &nbsp;|&nbsp; {업체명}</div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <div class="prod-price">판매가: {판매가}</div>
          <div class="prod-meta">구입가: {구입가}</div>
        </div>
      </div>
      {table_html}
    </div>
    """
    st.markdown(block_html, unsafe_allow_html=True)

# 하단 여백
st.markdown("<br><br>", unsafe_allow_html=True)
