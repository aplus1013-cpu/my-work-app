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

import streamlit as st

import feature1_engine as f1
import feature2_manager_view as f2
import feature3_employee_pages as f3
import feature4_manager_pages as f4

st.set_page_config(page_title="판촉사원 매출 요약", page_icon="🪻")

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

(tab_sales_summary,) = st.tabs(["매출 요약"])

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


def build_report_text(report, meta):
    """콘솔용 print_report()와 같은 서식으로, 복사/다운로드용 텍스트를 만든다."""
    lines = [
        f"[매출 요약] 기준일: {meta['최신마감일']} "
        f"(누적일수 {meta['누적일수']}일 / 해당월 전체일수 {meta['해당월전체일수']}일)"
    ]
    for e in report:
        lines.append("")
        lines.append(
            f"{e['행사자이름']} 님 (매니저: {e['매니저']}), 이번 달 누적 매출 {f1.format_won(e['누적매출'])} "
            f"(누적일수 기준 목표 대비 {e['달성률'] * 100:.1f}% 달성)"
        )
        for s in e["거래처목록"]:
            label = f1.combo_label(s["품목군슬롯"])
            lines.append(
                f"  - {s['거래처명']}: {s['채널']}채널 · {label} 그룹 "
                f"전국 {s['그룹인원수']}명 중 {s['순위']}위 "
                f"(근무 {s['근무일수']}일 · 일평균 {f1.format_won(s['일평균매출'])} · "
                f"누적 {f1.format_won(s['누적매출'])})"
            )
    return "\n".join(lines)


if "employee_zip" not in st.session_state:
    st.session_state.employee_zip = None
    st.session_state.manager_zip = None
    st.session_state.summary_message = None
    st.session_state.report_text = None

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
                        st.session_state.report_text = None
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
                        st.session_state.report_text = build_report_text(report, result["meta"])
            except (FileNotFoundError, ValueError) as e:
                st.session_state.employee_zip = None
                st.session_state.manager_zip = None
                st.session_state.summary_message = None
                st.session_state.report_text = None
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
            st.markdown("**결과 요약 텍스트** — 오른쪽 위 아이콘으로 복사하거나, 아래 버튼으로 내려받을 수 있어요.")
            st.code(st.session_state.report_text, language=None)
            st.download_button(
                "텍스트로 다운로드",
                data=st.session_state.report_text,
                file_name="매출요약.txt",
                mime="text/plain",
            )
