# -*- coding: utf-8 -*-
"""
Streamlit 웹 화면: 매출 데이터 엑셀 업로드 -> "요약하기" -> 사원/매니저 요약 엑셀 다운로드

계산·렌더링 로직은 전혀 새로 만들지 않고, feature1~4의 기존 함수를 그대로 호출한다
(feature3/feature4가 outputs/employee-pages, outputs/manager-pages에 파일을 저장하는 동작도 그대로 유지 -
 이 화면은 그 파일들을 모아 zip으로 다운로드하도록 얹었을 뿐이다).
"""
import io
import os
import tempfile
import zipfile

import altair as alt
import pandas as pd
import streamlit as st

import feature1_engine as f1
import feature2_manager_view as f2
import feature3_employee_pages as f3
import feature4_manager_pages as f4

st.set_page_config(page_title="판촉사원 매출 요약", page_icon="🪻")

# 차트 색상 (dataviz 스킬 참조 팔레트 그대로 사용 - 별도 브랜드 색 대입 없음)
CHART_CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]
CHART_BLUE = CHART_CATEGORICAL[0]
CHART_INK_PRIMARY = "#0b0b0b"
CHART_INK_SECONDARY = "#52514e"
CHART_INK_MUTED = "#898781"
CHART_GRID = "#e1e0d9"
CHART_AXIS = "#c3c2b7"
CHART_SURFACE = "#fcfcfb"


def categorical_scale(values):
    """정해진 순서의 팔레트를 카테고리에 고정 배정 (8개 초과분은 순환하지 않고 마지막 색을 재사용)."""
    values = list(values)
    colors = [CHART_CATEGORICAL[i] if i < len(CHART_CATEGORICAL) else CHART_CATEGORICAL[-1] for i in range(len(values))]
    return alt.Scale(domain=values, range=colors)


def style_chart(chart):
    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(
            gridColor=CHART_GRID,
            domainColor=CHART_AXIS,
            tickColor=CHART_AXIS,
            labelColor=CHART_INK_SECONDARY,
            titleColor=CHART_INK_SECONDARY,
            labelLimit=260,
        )
        .configure_legend(labelColor=CHART_INK_SECONDARY, titleColor=CHART_INK_SECONDARY)
        .properties(background=CHART_SURFACE)
    )

CUSTOM_CSS = """
<style>
.badge-pill {
    display: inline-block;
    background-color: #DCEBFF;
    color: #2B4C7E;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}
h1 { color: #4B3A8E !important; }

.st-key-input-card, .st-key-employee-card, .st-key-manager-card {
    border-radius: 18px !important;
    padding: 0.4rem 0.4rem 0.9rem 0.4rem;
}
.st-key-input-card {
    background-color: #F7F3FF;
    border: 1px solid #E4D9FF !important;
}
.st-key-employee-card {
    background-color: #FDF3B0;
    border: none !important;
}
.st-key-manager-card {
    background-color: #FBD8E4;
    border: none !important;
}
.st-key-employee-card button, .st-key-manager-card button {
    background-color: #FFFFFF !important;
    color: #4B3A8E !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
div.stButton > button[kind="primary"] {
    background-color: #8B7FE8;
    border: none;
    border-radius: 10px;
}
.st-key-text-card {
    background-color: #DCEBFF;
    border: none !important;
    border-radius: 18px !important;
    padding: 0.4rem 0.4rem 0.9rem 0.4rem;
}
.st-key-text-card button {
    background-color: #FFFFFF !important;
    color: #2B4C7E !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
.guide-text {
    font-size: 0.9rem;
    color: #5B4E8C;
    margin-bottom: 0.5rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown('<span class="badge-pill">✨ 자동 요약 도구</span>', unsafe_allow_html=True)
st.title("판촉사원 매출 요약")

tab_sales_summary, tab_dashboard = st.tabs(["매출 요약", "매출 전광판"])

with tab_sales_summary:
    st.caption(
        "채널별 매출 데이터 엑셀 파일을 올리고 '요약하기'를 누르면, "
        "사원별·매니저별 요약 엑셀 파일을 zip으로 받을 수 있습니다."
    )

    with st.container(key="input-card", border=True):
        st.markdown(
            '<div class="guide-text">📌 채널별 매출 데이터 엑셀 파일(.xlsx)을 아래에 올려주세요. '
            "여러 팀 파일을 한 번에 선택할 수 있고, 다 올린 뒤 '요약하기'를 누르면 됩니다.</div>",
            unsafe_allow_html=True,
        )
        uploaded_files = st.file_uploader(
            "매출 데이터 엑셀 파일 업로드 (채널별로 여러 개 선택 가능)",
            type="xlsx",
            accept_multiple_files=True,
        )
        run_clicked = st.button("요약하기", type="primary", disabled=not uploaded_files)


def zip_files(paths):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            zf.write(path, arcname=os.path.basename(path))
    return buffer.getvalue()


if "employee_zip" not in st.session_state:
    st.session_state.employee_zip = None
    st.session_state.manager_zip = None
    st.session_state.summary_message = None
    st.session_state.dash_report = None
    st.session_state.dash_group_rankings = None
    st.session_state.dash_meta = None

with tab_sales_summary:
    if run_clicked:
        with tempfile.TemporaryDirectory() as tmp_dir:
            saved_paths = []
            for uploaded in uploaded_files:
                path = os.path.join(tmp_dir, uploaded.name)
                with open(path, "wb") as f:
                    f.write(uploaded.getbuffer())
                saved_paths.append(path)

            try:
                with st.spinner("매출 데이터를 계산하는 중..."):
                    result = f1.compute_all(saved_paths)
                    report = result["report"]

                    if not report:
                        st.session_state.employee_zip = None
                        st.session_state.manager_zip = None
                        st.session_state.summary_message = None
                        st.session_state.dash_report = None
                        st.session_state.dash_group_rankings = None
                        st.session_state.dash_meta = None
                        st.warning(
                            "결과에 포함된 행사자가 없습니다 "
                            "(유효한 매출 데이터가 없거나 모두 정제 과정에서 제외됨)."
                        )
                    else:
                        manager_views = f2.build_manager_views(report, result["group_rankings"])
                        employee_paths = f3.generate_pages(report)
                        manager_paths = f4.generate_pages(manager_views)

                        st.session_state.employee_zip = zip_files(employee_paths)
                        st.session_state.manager_zip = zip_files(manager_paths)
                        st.session_state.summary_message = (
                            f"완료: 행사자 {len(employee_paths)}명, 매니저 {len(manager_paths)}명 요약 생성"
                        )
                        st.session_state.dash_report = report
                        st.session_state.dash_group_rankings = result["group_rankings"]
                        st.session_state.dash_meta = result["meta"]
            except (FileNotFoundError, ValueError) as e:
                st.session_state.employee_zip = None
                st.session_state.manager_zip = None
                st.session_state.summary_message = None
                st.session_state.dash_report = None
                st.session_state.dash_group_rankings = None
                st.session_state.dash_meta = None
                st.error(f"실행을 멈췄습니다: {e}")

    if st.session_state.employee_zip and st.session_state.manager_zip:
        st.success(st.session_state.summary_message)
        col1, col2 = st.columns(2)
        with col1:
            with st.container(key="employee-card", border=True):
                st.markdown("**사원매출요약**")
                st.download_button(
                    "다운로드",
                    data=st.session_state.employee_zip,
                    file_name="사원매출요약.zip",
                    mime="application/zip",
                )
        with col2:
            with st.container(key="manager-card", border=True):
                st.markdown("**매니저요약**")
                st.download_button(
                    "다운로드",
                    data=st.session_state.manager_zip,
                    file_name="매니저요약.zip",
                    mime="application/zip",
                )

        with st.container(key="text-card", border=True):
            st.markdown("**결과 요약** — 행사자별 누적매출·달성률을 한눈에 볼 수 있어요.")

            df_result_emp = pd.DataFrame(
                [
                    {
                        "행사자이름": e["행사자이름"],
                        "매니저": e["매니저"],
                        "누적매출": e["누적매출"],
                        "달성률(%)": round(e["달성률"] * 100, 1),
                    }
                    for e in st.session_state.dash_report
                ]
            ).sort_values("누적매출", ascending=False)

            base = alt.Chart(df_result_emp).encode(
                y=alt.Y("행사자이름:N", sort="-x", title=None),
                x=alt.X("누적매출:Q", title="누적매출(원)"),
                tooltip=[
                    alt.Tooltip("행사자이름:N"),
                    alt.Tooltip("매니저:N"),
                    alt.Tooltip("누적매출:Q", format=",.0f", title="누적매출(원)"),
                    alt.Tooltip("달성률(%):Q", format=".1f"),
                ],
            )
            bars = base.mark_bar(cornerRadiusEnd=4, size=18, color=CHART_BLUE)
            labels = base.mark_text(align="left", dx=4, color=CHART_INK_PRIMARY).encode(
                text=alt.Text("누적매출:Q", format=",.0f")
            )
            st.altair_chart(style_chart((bars + labels).properties(height=alt.Step(24))), width="stretch")

            st.dataframe(df_result_emp, hide_index=True, width="stretch")

            with st.expander("거래처별 상세 보기"):
                df_result_stores = pd.DataFrame(
                    [
                        {
                            "행사자이름": e["행사자이름"],
                            "매니저": e["매니저"],
                            "거래처명": s["거래처명"],
                            "채널": s["채널"],
                            "품목군": f1.combo_label(s["품목군슬롯"]),
                            "전국순위": s["순위"],
                            "그룹인원수": s["그룹인원수"],
                            "근무일수": s["근무일수"],
                            "일평균매출": s["일평균매출"],
                            "누적매출": s["누적매출"],
                        }
                        for e in st.session_state.dash_report
                        for s in e["거래처목록"]
                    ]
                )
                st.dataframe(df_result_stores, hide_index=True, width="stretch")

with tab_dashboard:
    st.caption("'매출 요약' 탭에서 계산한 결과를, 채널·매니저·행사자 관점의 차트로 보여줍니다.")

    if not st.session_state.dash_report:
        st.info("먼저 '매출 요약' 탭에서 매출 데이터를 올리고 '요약하기'를 눌러주세요.")
    else:
        dash_report = st.session_state.dash_report
        dash_group_rankings = st.session_state.dash_group_rankings
        dash_meta = st.session_state.dash_meta

        df_stores = pd.DataFrame(
            [
                {
                    "행사자이름": e["행사자이름"],
                    "매니저": e["매니저"],
                    "채널": s["채널"],
                    "거래처명": s["거래처명"],
                    "누적매출": s["누적매출"],
                }
                for e in dash_report
                for s in e["거래처목록"]
            ]
        )
        df_emp = pd.DataFrame(
            [
                {
                    "행사자이름": e["행사자이름"],
                    "매니저": e["매니저"],
                    "누적매출": e["누적매출"],
                    "달성률": e["달성률"] * 100,
                }
                for e in dash_report
            ]
        )

        # 1) KPI 카드
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("기준일", str(dash_meta["최신마감일"]))
        kpi2.metric("전사 누적매출", f1.format_won(df_emp["누적매출"].sum()))
        kpi3, kpi4 = st.columns(2)
        kpi3.metric("참여 행사자", f"{len(df_emp)}명")
        kpi4.metric("평균 달성률", f"{df_emp['달성률'].mean():.1f}%")

        st.divider()

        # 2) 채널별 매출 비교
        st.markdown("**채널별 매출 비교**")
        channel_totals = (
            df_stores.groupby("채널", as_index=False)["누적매출"].sum().sort_values("누적매출", ascending=False)
        )
        base = alt.Chart(channel_totals).encode(
            y=alt.Y("채널:N", sort="-x", title=None),
            x=alt.X("누적매출:Q", title="누적매출(원)"),
            color=alt.Color("채널:N", scale=categorical_scale(channel_totals["채널"]), legend=None),
            tooltip=[alt.Tooltip("채널:N"), alt.Tooltip("누적매출:Q", format=",.0f", title="누적매출(원)")],
        )
        bars = base.mark_bar(cornerRadiusEnd=4, size=28)
        labels = base.mark_text(align="left", dx=4, color=CHART_INK_PRIMARY).encode(
            text=alt.Text("누적매출:Q", format=",.0f")
        )
        st.altair_chart(style_chart((bars + labels).properties(height=alt.Step(40))), width="stretch")
        with st.expander("표로 보기"):
            st.dataframe(channel_totals, hide_index=True, width="stretch")

        st.divider()

        # 3) 매니저별 팀 실적 (누적매출 합계 / 평균 달성률 - 척도가 달라 차트를 둘로 분리)
        st.markdown("**매니저별 팀 실적**")
        manager_sales = (
            df_emp.groupby("매니저", as_index=False)["누적매출"].sum().sort_values("누적매출", ascending=False)
        )
        manager_rate = (
            df_emp.groupby("매니저", as_index=False)["달성률"].mean().sort_values("달성률", ascending=False)
        )
        col_sales, col_rate = st.columns(2)
        with col_sales:
            st.caption("팀 누적매출 합계")
            base = alt.Chart(manager_sales).encode(
                y=alt.Y("매니저:N", sort="-x", title=None),
                x=alt.X("누적매출:Q", title="누적매출(원)"),
                color=alt.Color("매니저:N", scale=categorical_scale(manager_sales["매니저"]), legend=None),
                tooltip=[alt.Tooltip("매니저:N"), alt.Tooltip("누적매출:Q", format=",.0f", title="누적매출(원)")],
            )
            bars = base.mark_bar(cornerRadiusEnd=4, size=22)
            labels = base.mark_text(align="left", dx=4, color=CHART_INK_PRIMARY).encode(
                text=alt.Text("누적매출:Q", format=",.0f")
            )
            st.altair_chart(style_chart((bars + labels).properties(height=alt.Step(34))), width="stretch")
        with col_rate:
            st.caption("팀 평균 달성률")
            base = alt.Chart(manager_rate).encode(
                y=alt.Y("매니저:N", sort="-x", title=None),
                x=alt.X("달성률:Q", title="평균 달성률(%)"),
                color=alt.Color("매니저:N", scale=categorical_scale(manager_rate["매니저"]), legend=None),
                tooltip=[alt.Tooltip("매니저:N"), alt.Tooltip("달성률:Q", format=".1f", title="평균 달성률(%)")],
            )
            bars = base.mark_bar(cornerRadiusEnd=4, size=22)
            labels = base.mark_text(align="left", dx=4, color=CHART_INK_PRIMARY).encode(
                text=alt.Text("달성률:Q", format=".1f")
            )
            st.altair_chart(style_chart((bars + labels).properties(height=alt.Step(34))), width="stretch")
        with st.expander("표로 보기"):
            st.dataframe(
                manager_sales.merge(manager_rate, on="매니저").sort_values("누적매출", ascending=False),
                hide_index=True,
                width="stretch",
            )

        st.divider()

        # 4) 행사자 달성률 랭킹 (점선 = 목표 달성 기준선 100%)
        st.markdown("**행사자 달성률 랭킹**")
        df_rate_sorted = df_emp.sort_values("달성률", ascending=False)
        base = alt.Chart(df_rate_sorted).encode(
            y=alt.Y("행사자이름:N", sort="-x", title=None),
            x=alt.X("달성률:Q", title="누적일수 기준 달성률(%)"),
            tooltip=[
                alt.Tooltip("행사자이름:N"),
                alt.Tooltip("매니저:N"),
                alt.Tooltip("달성률:Q", format=".1f", title="달성률(%)"),
            ],
        )
        bars = base.mark_bar(cornerRadiusEnd=4, size=18, color=CHART_BLUE)
        labels = base.mark_text(align="left", dx=4, color=CHART_INK_PRIMARY).encode(
            text=alt.Text("달성률:Q", format=".1f")
        )
        rule = alt.Chart(pd.DataFrame({"x": [100]})).mark_rule(strokeDash=[4, 4], color=CHART_INK_MUTED).encode(
            x="x:Q"
        )
        st.altair_chart(
            style_chart((bars + labels + rule).properties(height=alt.Step(24))), width="stretch"
        )
        st.caption("점선 = 누적일수 기준 목표 달성선(100%)")
        with st.expander("표로 보기"):
            st.dataframe(
                df_rate_sorted[["행사자이름", "매니저", "누적매출", "달성률"]],
                hide_index=True,
                width="stretch",
            )

        st.divider()

        # 5) 품목군 그룹 리더보드 (그룹 선택 -> 전국 순위 Top N, 일평균매출 기준)
        st.markdown("**품목군 그룹 리더보드**")
        group_options = []
        for (channel, item_tuple), members in dash_group_rankings.items():
            label_source = members[0]["품목군슬롯"] if members else []
            group_label = f1.combo_label(label_source) or "+".join(item_tuple)
            headcount = len({m["행사자사번"] for m in members})
            group_options.append((f"{channel}채널 · {group_label} (전국 {headcount}명)", (channel, item_tuple)))
        group_options.sort(key=lambda x: x[0])

        if group_options:
            selected_label = st.selectbox("그룹 선택", [label for label, _ in group_options])
            selected_key = dict(group_options)[selected_label]
            members = dash_group_rankings[selected_key]
            top_n = min(10, len(members))
            df_group = pd.DataFrame(members[:top_n])[
                ["순위", "행사자이름", "거래처명", "근무일수", "일평균매출", "누적매출"]
            ]
            df_group["표시이름"] = df_group["행사자이름"] + " · " + df_group["거래처명"]

            base = alt.Chart(df_group).encode(
                y=alt.Y("표시이름:N", sort="-x", title=None),
                x=alt.X("일평균매출:Q", title="일평균매출(원)"),
                tooltip=[
                    alt.Tooltip("순위:Q"),
                    alt.Tooltip("행사자이름:N"),
                    alt.Tooltip("거래처명:N"),
                    alt.Tooltip("일평균매출:Q", format=",.0f", title="일평균매출(원)"),
                ],
            )
            bars = base.mark_bar(cornerRadiusEnd=4, size=20, color=CHART_BLUE)
            labels = base.mark_text(align="left", dx=4, color=CHART_INK_PRIMARY).encode(
                text=alt.Text("일평균매출:Q", format=",.0f")
            )
            st.altair_chart(
                style_chart((bars + labels).properties(height=alt.Step(28))), width="stretch"
            )
            with st.expander("표로 보기"):
                st.dataframe(
                    df_group[["순위", "행사자이름", "거래처명", "근무일수", "일평균매출", "누적매출"]],
                    hide_index=True,
                    width="stretch",
                )
        else:
            st.caption("표시할 그룹 데이터가 없습니다.")

        st.divider()

        # 6) 행사자 개별 조회
        st.markdown("**행사자 개별 조회**")
        emp_labels = [f"{e['행사자이름']} (매니저: {e['매니저']})" for e in dash_report]
        selected_emp_label = st.selectbox("행사자 선택", emp_labels)
        selected_emp = dash_report[emp_labels.index(selected_emp_label)]

        m1, m2, m3 = st.columns(3)
        m1.metric("누적매출", f1.format_won(selected_emp["누적매출"]))
        m2.metric("달성률", f"{selected_emp['달성률'] * 100:.1f}%")
        m3.metric("소속 거래처 수", f"{len(selected_emp['거래처목록'])}곳")

        df_emp_stores = pd.DataFrame(
            [
                {
                    "거래처명": s["거래처명"],
                    "채널": s["채널"],
                    "품목군": f1.combo_label(s["품목군슬롯"]),
                    "전국순위": s["순위"],
                    "그룹인원수": s["그룹인원수"],
                    "근무일수": s["근무일수"],
                    "일평균매출": s["일평균매출"],
                    "누적매출": s["누적매출"],
                }
                for s in selected_emp["거래처목록"]
            ]
        )
        st.dataframe(df_emp_stores, hide_index=True, width="stretch")
