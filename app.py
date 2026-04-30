# ============================================================
# DAISO SNS Issue Finder — 패치 모음
# 아래 4개 섹션을 기존 코드에서 찾아서 교체하세요
# ============================================================


# ============================================================
# [PATCH 1] 품번/품명 — load_product_db + 품명 기반 매칭
# 기존 load_product_db(), extract_product_code(), match_product_name() 전체 교체
# ============================================================

@st.cache_data(ttl=3600)
def load_product_db():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        df = pd.DataFrame(sh.sheet1.get_all_records())
        df.columns = [c.strip() for c in df.columns]

        # 품번: 숫자/문자 모두 str로 통일
        if "품번" in df.columns:
            df["품번"] = df["품번"].astype(str).str.strip()

        # 품명 토큰 미리 계산 (매칭 속도 향상)
        if "품명" in df.columns:
            df["_tokens"] = df["품명"].apply(
                lambda n: set(re.findall(r'[가-힣]{2,}|[A-Za-z]{3,}', str(n)))
            )
        return df
    except Exception as e:
        st.warning(f"⚠ 품명 DB 로드 실패: {e}")
        return pd.DataFrame(columns=["품번", "품명", "소분류", "_tokens"])


PRODUCT_DB = load_product_db()
VALID_PRODUCT_CODES = set()
if not PRODUCT_DB.empty and "품번" in PRODUCT_DB.columns:
    VALID_PRODUCT_CODES = set(PRODUCT_DB["품번"].dropna().astype(str).str.strip().tolist())


def load_subcategories():
    if not PRODUCT_DB.empty and "소분류" in PRODUCT_DB.columns:
        return list(PRODUCT_DB["소분류"].dropna().unique())
    return []


SUBCATEGORIES = load_subcategories()


def extract_product_code(text: str) -> str:
    """
    1순위: 품명 키워드 매칭 (SNS 글에 품번 직접 언급 드뭄)
    2순위: 숫자 품번 직접 매칭 (1~7자리 모두 허용)
    """
    if PRODUCT_DB.empty:
        return ""

    found_codes = []

    # ── 1순위: 품명 토큰 매칭 ──────────────────────────────
    if "_tokens" in PRODUCT_DB.columns:
        for _, row in PRODUCT_DB.iterrows():
            tokens = row.get("_tokens", set())
            if not tokens:
                continue
            # 핵심 토큰(3글자 이상) 중 하나라도 본문에 있으면 매칭
            key_tokens = [t for t in tokens if len(t) >= 3]
            if key_tokens and any(t in text for t in key_tokens):
                code = str(row.get("품번", "")).strip()
                if code and code not in found_codes:
                    found_codes.append(code)

    # ── 2순위: 숫자 품번 직접 매칭 (1~7자리 허용, 날짜 제외) ──
    if not found_codes and VALID_PRODUCT_CODES:
        raw_nums = re.findall(r'\b(\d{4,9})\b', text)
        for c in raw_nums:
            if is_date_like(c):
                continue
            if c in VALID_PRODUCT_CODES and c not in found_codes:
                found_codes.append(c)

    return ", ".join(found_codes[:3]) if found_codes else ""  # 최대 3개


def match_product_name(code: str) -> str:
    """품번으로 품명 조회 (쉼표 구분 복수 품번 지원)"""
    if PRODUCT_DB.empty or not code:
        return ""
    names = []
    for c in [c.strip() for c in code.split(",")][:3]:
        row = PRODUCT_DB[PRODUCT_DB["품번"].astype(str).str.strip() == c]
        if not row.empty:
            name = row.iloc[0].get("품명", "")
            if name and name not in names:
                names.append(str(name))
    return ", ".join(names)


def match_subcategory_from_code(code: str) -> str:
    """품번으로 소분류 직접 조회"""
    if PRODUCT_DB.empty or not code:
        return ""
    for c in [c.strip() for c in code.split(",")][:3]:
        row = PRODUCT_DB[PRODUCT_DB["품번"].astype(str).str.strip() == c]
        if not row.empty and "소분류" in row.columns:
            val = row.iloc[0].get("소분류", "")
            if val:
                return str(val)
    return ""


# ── 분석 루프에서 소분류 추출 순서 변경 ──
# 기존: extract_subcategory(full) 만 사용
# 변경: 품번 매칭 성공 시 소분류도 DB에서 직접 가져옴
# 아래 코드를 분석 루프의 prod_code 추출 이후에 적용하세요:
#
#   prod_code = extract_product_code(full)
#   prod_name = match_product_name(prod_code)
#   # 소분류: 품번 매칭 성공 시 DB에서, 실패 시 텍스트 추출
#   subcate = match_subcategory_from_code(prod_code) or extract_subcategory(full)


# ============================================================
# [PATCH 2] 골드셋 Google Sheets 저장/로드
# 기존 load_excluded_urls_from_sheet() 아래에 추가
# ============================================================

def load_goldset_from_sheet():
    """앱 시작 시 Google Sheets에서 골드셋 로드"""
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "goldset", [
            "link", "title", "AI판정", "확신도", "정답레이블",
            "출처", "날짜", "레이블일시"
        ])
        records = ws.get_all_records()
        if records:
            st.session_state["gold_labels"] = records
    except Exception as e:
        st.warning(f"⚠ 골드셋 로드 실패: {e}")


def save_goldset_to_sheet(entry: dict):
    """골드셋 1건을 Google Sheets에 추가"""
    try:
        gc = get_gsheet_client_rw()
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        ws = _get_or_create_worksheet(sh, "goldset", [
            "link", "title", "AI판정", "확신도", "정답레이블",
            "출처", "날짜", "레이블일시"
        ])
        ws.append_row([
            entry.get("link", ""),
            entry.get("title", ""),
            entry.get("AI판정", ""),
            entry.get("확신도", ""),
            entry.get("정답레이블", ""),
            entry.get("출처", ""),
            entry.get("날짜", ""),
            entry.get("레이블일시", ""),
        ])
    except Exception as e:
        st.warning(f"⚠ 골드셋 저장 실패: {e}")


# ── 세션 초기화 _defaults에 추가 ──
# "gold_labels": [],
# "gold_suggested_kw": [],   # 자동 추출된 키워드 후보
# "gold_threshold_rec": None, # 추천 threshold


# ── _sheets_loaded 블록에 추가 ──
# load_goldset_from_sheet()


# ============================================================
# [PATCH 3] 골드셋 기반 자가학습 분석 함수
# 파일 어디든 추가 (관리자 패널 위에 두면 좋음)
# ============================================================

def analyze_goldset(gold: list, current_threshold: int = 55):
    """
    골드셋을 분석해서:
    1. Recall / Precision 계산
    2. threshold 추천값
    3. 오판 글에서 키워드 후보 자동 추출
    반환: dict
    """
    if not gold:
        return None

    result = {
        "total": len(gold),
        "accuracy": 0,
        "recall": {},
        "precision": {},
        "threshold_rec": current_threshold,
        "suggested_kw": [],
        "confusion": {},
    }

    labels = ["부정", "긍정", "중립"]

    # 정확도
    match = sum(1 for g in gold if g.get("AI판정") == g.get("정답레이블"))
    result["accuracy"] = round(match / len(gold) * 100, 1)

    # Recall / Precision
    for lbl in labels:
        true_pos  = sum(1 for g in gold if g.get("정답레이블") == lbl and g.get("AI판정") == lbl)
        actual    = sum(1 for g in gold if g.get("정답레이블") == lbl)
        predicted = sum(1 for g in gold if g.get("AI판정") == lbl)
        result["recall"][lbl]    = round(true_pos / actual * 100, 1)    if actual    else 0
        result["precision"][lbl] = round(true_pos / predicted * 100, 1) if predicted else 0

    # 혼동 패턴
    from collections import Counter
    confusion_list = [
        f"{g['AI판정']}→{g['정답레이블']}"
        for g in gold if g.get("AI판정") != g.get("정답레이블")
    ]
    result["confusion"] = dict(Counter(confusion_list).most_common(6))

    # threshold 추천
    neg_recall = result["recall"].get("부정", 0)
    neg_prec   = result["precision"].get("부정", 0)
    if neg_recall < 55:
        result["threshold_rec"] = max(current_threshold - 5, 40)
        result["threshold_msg"] = f"부정 재현율 {neg_recall}% 낮음 → threshold {result['threshold_rec']}%로 낮추기 권장"
    elif neg_prec < 55:
        result["threshold_rec"] = min(current_threshold + 5, 75)
        result["threshold_msg"] = f"부정 정밀도 {neg_prec}% 낮음 → threshold {result['threshold_rec']}%로 높이기 권장"
    else:
        result["threshold_rec"] = current_threshold
        result["threshold_msg"] = f"현재 threshold {current_threshold}% 적정"

    # 오판 글에서 키워드 후보 자동 추출
    # AI가 "중립"으로 판정했지만 정답이 "부정"인 글 → 놓친 부정 표현 추출
    missed_neg = [
        g for g in gold
        if g.get("정답레이블") == "부정" and g.get("AI판정") != "부정"
    ]
    kw_candidates = []
    for g in missed_neg:
        title = g.get("title", "")
        # 2글자 이상 한글 명사/형용사 추출
        tokens = re.findall(r'[가-힣]{2,6}', title)
        # 이미 등록된 키워드 제외
        existing = set(st.session_state.get("neg_kw_list", []))
        for t in tokens:
            if t not in existing and t not in kw_candidates:
                # 불용어 제외
                stopwords = {"다이소","구매","상품","제품","사용","이에요","이야","입니다","에서","했어","했는","이네"}
                if t not in stopwords:
                    kw_candidates.append(t)

    # 빈도순 상위 10개
    freq = Counter(kw_candidates)
    result["suggested_kw"] = [kw for kw, _ in freq.most_common(10)]

    return result


# ============================================================
# [PATCH 4] 관리자 탭 — 5번째 탭 "🏷 골드셋 관리" 전체
# 기존 adm_tab1~4 선언을 아래로 교체하고 adm_tab5 내용 추가
# ============================================================

# ── 탭 선언 교체 ──
# adm_tab1, adm_tab2, adm_tab3, adm_tab4, adm_tab5 = st.tabs(
#     ["➕ 키워드 추가", "🗑 키워드 삭제", "📋 현재 키워드 목록", "📜 재학습 로그", "🏷 골드셋 관리"])

# ── adm_tab5 전체 내용 ──  (with adm_tab5: 블록으로 추가)
ADMIN_TAB5_CODE = '''
with adm_tab5:
    gold = st.session_state.get("gold_labels", [])

    st.markdown('<div class="admin-section">골드셋 현황 — AI 판정 정확도 실시간 측정</div>',
                unsafe_allow_html=True)

    if len(gold) < 10:
        st.info(f"현재 {len(gold)}건 레이블링됨. 10건 이상부터 정확도 분석이 활성화됩니다.")
    else:
        # ── 분석 실행 ──────────────────────────────────────────
        analysis = analyze_goldset(gold, current_threshold=threshold)

        # 정확도 + threshold 추천
        acc_color = "#16A34A" if analysis["accuracy"] >= 70 else "#CA8A04" if analysis["accuracy"] >= 50 else "#DC2626"
        st.markdown(f"""
        <div style="background:#F0F7FF;border:1.5px solid #B3D1F5;border-radius:10px;
                    padding:1rem 1.25rem;margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">
                <div>
                    <div style="font-size:0.72rem;color:#718096;font-weight:600;">AI 정확도</div>
                    <div style="font-size:2rem;font-weight:700;color:{acc_color};font-family:Inter;">
                        {analysis["accuracy"]}%
                    </div>
                    <div style="font-size:0.72rem;color:#718096;">{analysis["total"]}건 기준</div>
                </div>
                <div style="flex:1;min-width:200px;">
                    <div style="font-size:0.72rem;color:#718096;font-weight:600;margin-bottom:0.3rem;">
                        🎯 Threshold 추천
                    </div>
                    <div style="font-size:0.85rem;color:#0066CC;font-weight:600;">
                        {analysis["threshold_msg"]}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recall / Precision 표
        st.markdown("**감성별 Recall / Precision**")
        perf_data = []
        for lbl in ["부정", "긍정", "중립"]:
            rec  = analysis["recall"].get(lbl, 0)
            prec = analysis["precision"].get(lbl, 0)
            perf_data.append({
                "감성": lbl,
                "재현율 Recall (%)": rec,
                "정밀도 Precision (%)": prec,
                "판단": "✅ 양호" if rec >= 65 and prec >= 65 else "⚠ 개선 필요"
            })
        st.dataframe(pd.DataFrame(perf_data), use_container_width=True,
                     hide_index=True, height=140)

        # 오판 패턴
        if analysis["confusion"]:
            st.markdown("**AI 오판 패턴**")
            conf_html = ""
            for pattern, cnt in analysis["confusion"].items():
                ai_lbl, real_lbl = pattern.split("→")
                conf_html += f"""
                <div style="display:flex;align-items:center;gap:0.5rem;
                            padding:0.4rem 0.75rem;background:#FEF2F2;
                            border:1px solid #FCA5A5;border-radius:6px;margin-bottom:0.3rem;">
                    <span style="color:#DC2626;font-weight:600;">{ai_lbl}</span>
                    <span style="color:#718096;">→ 실제</span>
                    <span style="color:#16A34A;font-weight:600;">{real_lbl}</span>
                    <span style="margin-left:auto;background:#FEE2E2;color:#DC2626;
                                 padding:1px 8px;border-radius:10px;font-size:0.75rem;">
                        {cnt}건
                    </span>
                </div>"""
            st.markdown(conf_html, unsafe_allow_html=True)

        # 키워드 자동 추출 추천
        suggested = analysis.get("suggested_kw", [])
        if suggested:
            st.markdown('<div class="admin-section" style="margin-top:1rem;">키워드 자동 추출 — AI가 놓친 부정 글에서 추출</div>',
                        unsafe_allow_html=True)
            st.markdown(
                '<span style="font-size:0.78rem;color:#718096;">'
                'AI가 중립으로 잘못 판정한 부정 글에서 자주 나온 표현입니다. '
                '승인할 키워드를 선택 후 추가하세요.</span>',
                unsafe_allow_html=True)

            selected_kws = []
            kw_cols = st.columns(5)
            for i, kw in enumerate(suggested):
                with kw_cols[i % 5]:
                    if st.checkbox(kw, key=f"suggest_kw_{i}"):
                        selected_kws.append(kw)

            if selected_kws and st.button("✅ 선택 키워드 부정 목록에 추가",
                                           key="add_suggested_kw",
                                           use_container_width=True):
                added = []
                for kw in selected_kws:
                    ok, msg = admin_apply_keyword("neg", kw, "add")
                    if ok:
                        added.append(kw)
                if added:
                    st.success(f"✅ {len(added)}개 키워드 추가 완료: {', '.join(added)}")
                    st.rerun()

        st.markdown("---")

    # ── 골드셋 데이터 ──────────────────────────────────────────
    st.markdown('<div class="admin-section">레이블링 데이터 관리</div>', unsafe_allow_html=True)

    if gold:
        gold_df = pd.DataFrame(gold)

        # 분포 표시
        from collections import Counter
        dist = Counter(g.get("정답레이블","") for g in gold)
        gc1, gc2, gc3 = st.columns(3)
        for col, lbl, color in [
            (gc1, "부정", "#DC2626"),
            (gc2, "긍정", "#16A34A"),
            (gc3, "중립", "#CA8A04")
        ]:
            with col:
                st.markdown(f"""
                <div class="admin-stat-box">
                    <div class="admin-stat-num" style="color:{color};">{dist.get(lbl,0)}</div>
                    <div class="admin-stat-label">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.dataframe(
            gold_df[["title","AI판정","확신도","정답레이블","출처","날짜","레이블일시"]].tail(50),
            use_container_width=True, hide_index=True, height=250)

        g_dl1, g_dl2 = st.columns(2)
        with g_dl1:
            st.download_button(
                "📥 골드셋 CSV 다운로드",
                gold_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                f"goldset_{date.today()}.csv", "text/csv",
                use_container_width=True)
        with g_dl2:
            if st.button("🗑 골드셋 전체 초기화", key="gold_reset",
                         use_container_width=True):
                st.session_state["gold_labels"] = []
                st.success("초기화 완료")
                st.rerun()
    else:
        st.info("아직 레이블링 데이터가 없습니다. 분석 후 각 글 카드에서 정답을 표기해주세요.")
'''


# ============================================================
# [PATCH 5] 분석 결과 카드 — 레이블링 버튼 추가
# 대시보드(tab_dash)와 render_detail_tab() 양쪽에 적용
# result-card 렌더링 st.markdown() 직후에 삽입
# ============================================================

LABEL_BUTTON_CODE = '''
# ── 관리자 레이블링 버튼 ─────────────────────────────────────
if st.session_state["admin_mode"]:
    item_link = r.get("link", str(idx))

    # 이미 레이블링됐는지 확인
    already = next(
        (g for g in st.session_state.get("gold_labels", [])
         if g.get("link") == item_link), None)

    if already:
        label_color = {
            "부정": "#DC2626", "긍정": "#16A34A", "중립": "#CA8A04"
        }.get(already["정답레이블"], "#718096")
        st.markdown(f"""
        <div style="background:#F8F9FB;border:1px solid #E2E8F0;border-radius:6px;
                    padding:0.35rem 0.75rem;font-size:0.73rem;color:#718096;
                    margin-bottom:0.4rem;">
            ✅ 정답 레이블: 
            <strong style="color:{label_color};">{already["정답레이블"]}</strong>
        </div>""", unsafe_allow_html=True)
    else:
        lb0, lb1, lb2, lb3 = st.columns([2.5, 1, 1, 1])
        with lb0:
            st.markdown(
                '<div style="font-size:0.72rem;color:#7C3AED;font-weight:600;'
                'padding-top:0.45rem;">🏷 정답 레이블 표기:</div>',
                unsafe_allow_html=True)

        def _save_label(label):
            entry = {
                "link":      r.get("link", ""),
                "title":     r.get("title", "")[:80],
                "AI판정":    r["감성"],
                "확신도":    r["확신도"],
                "정답레이블": label,
                "출처":      r.get("출처", ""),
                "날짜":      r.get("날짜", ""),
                "레이블일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state["gold_labels"].append(entry)
            save_goldset_to_sheet(entry)   # Google Sheets 즉시 저장

        with lb1:
            if st.button("🔴 부정", key=f"lb_neg_{idx}", use_container_width=True):
                _save_label("부정"); st.rerun()
        with lb2:
            if st.button("🟢 긍정", key=f"lb_pos_{idx}", use_container_width=True):
                _save_label("긍정"); st.rerun()
        with lb3:
            if st.button("⚪ 중립", key=f"lb_neu_{idx}", use_container_width=True):
                _save_label("중립"); st.rerun()
'''
