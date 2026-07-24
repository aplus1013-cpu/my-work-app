# -*- coding: utf-8 -*-
"""
Feature 2: 매니저별 코칭용 데이터 구성
명세: specs/feature-2-spec.md

입력 : feature1_engine.py의 계산 결과 — 행사자별 결과(report) + 그룹별 전국 전체 순위 명단(group_rankings)
동작 : 매니저 소속 행사자가 걸쳐 있는 (채널·품목군 조합) 그룹들을 찾아, 그 그룹의 전국 전체 순위를
       그대로 보여주고 "내 소속(같은 매니저)" 여부를 표시
출력 : 매니저별로, 관련 그룹의 전국 전체 순위표(내 소속 표시 포함)를 콘솔에 출력
       (웹페이지·저장·승인·카카오톡 발송은 이 기능 범위 밖 - feature-2-spec.md '지금은 뺄 것')
"""
import feature1_engine as f1


def build_manager_views(report, group_rankings):
    """매니저별로, 자신이 속한 그룹들의 전국 전체 순위 리스트(내 소속 표시 포함)를 구성한다."""
    # 매니저별 소속 행사자사번 집합
    managers = {}
    for e in report:
        managers.setdefault(e["매니저"], set()).add(e["행사자사번"])

    manager_views = {}
    for manager_name, emp_nos in managers.items():
        related_groups = []
        for group_key, group_list in group_rankings.items():
            if not any(row["행사자사번"] in emp_nos for row in group_list):
                continue  # 이 매니저 소속 행사자가 하나도 없는 그룹은 건너뜀
            marked_rows = [
                {**row, "내소속": row["행사자사번"] in emp_nos}
                for row in group_list
            ]
            related_groups.append({
                "채널": group_key[0],
                "품목군조합": group_key[1],
                "순위목록": marked_rows,
            })
        related_groups.sort(key=lambda g: (g["채널"], g["품목군조합"]))
        manager_views[manager_name] = related_groups

    return manager_views


def print_summary(manager_views):
    """전체 처리 규모를 한눈에 보여주는 요약 (상세는 아래 매니저별 섹션에서 확인)."""
    group_count = sum(len(groups) for groups in manager_views.values())
    row_count = sum(len(g["순위목록"]) for groups in manager_views.values() for g in groups)

    print("=" * 70)
    print("[처리 요약]")
    print(f"매니저 {len(manager_views)}명, 관련 그룹 {group_count}개, 표시된 순위 행 {row_count}건")


def print_manager_views(manager_views):
    print("=" * 70)
    print("[매니저별 코칭용 데이터] - 그룹 전국 전체 순위 + 내 소속 표시")
    print("=" * 70)
    if not manager_views:
        print("\n표시할 매니저가 없습니다 (유효한 매출 데이터가 없거나 모두 정제 과정에서 제외됨).")
        return
    for manager_name in sorted(manager_views):
        print(f"\n■ 매니저: {manager_name}")
        for group in manager_views[manager_name]:
            label = f1.combo_label(group["순위목록"][0]["품목군슬롯"])
            print(f"  [{group['채널']} · {label}] 그룹 전국 순위 (총 {len(group['순위목록'])}건)")
            for row in group["순위목록"]:
                mark = "  ◀ 내 소속" if row["내소속"] else ""
                print(
                    f"    {row['순위']}위 {row['행사자이름']}({row['매니저']}) - "
                    f"{row['거래처명']} - 누적 {f1.format_won(row['누적매출'])} - "
                    f"일평균 {f1.format_won(row['일평균매출'])}{mark}"
                )


def print_intro():
    print("=" * 70)
    print("[매니저별 코칭 화면]")
    print("feature1_engine.py의 매출 계산 결과를 바탕으로, 매니저별 소속 행사자가 속한")
    print('그룹(채널·품목군 조합)의 전국 전체 순위를 보여주고 "내 소속" 여부를 표시합니다.')
    print("(입력 파일은 feature1과 동일하게 inputs/sales 폴더를 읽습니다)")


def run(paths=None):
    print_intro()

    result = f1.compute_all(paths)
    manager_views = build_manager_views(result["report"], result["group_rankings"])
    print_summary(manager_views)
    print_manager_views(manager_views)
    return manager_views


if __name__ == "__main__":
    try:
        run()
    except (FileNotFoundError, ValueError) as e:
        print("=" * 70)
        print("[오류] 실행을 멈췄습니다.")
        print(str(e))
