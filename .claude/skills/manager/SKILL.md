---
name: manager
description: Use when the user asks to run "manager", or asks for "매니저 화면", "매니저 코칭", "매니저 순위" — runs feature2_manager_view.py, showing each manager the full national ranking for every group their employees belong to, with their own employees marked.
version: 1.0.0
---

# Manager

매니저별 코칭용 데이터 구성(feature2_manager_view.py)을 실행하는 스킬.

## 무엇을

매니저가 자기 소속 행사자와 관련된 (채널·품목군 조합) 그룹의 전국 전체 순위를 보고, 그 안에서 자기 소속 행사자의 위치를 바로 짚어낼 수 있게 보여준다.

## 입력

- 없음 (feature1_engine.py의 계산 결과를 내부에서 다시 계산해서 사용)

## 순서

1. `python feature2_manager_view.py`를 실행한다.
2. 매니저별로 관련 그룹의 전국 전체 순위와 "내 소속" 표시를 콘솔에 그대로 보여준다.

## 출력

- 매니저별: 관련 (채널·품목군 조합) 그룹마다 전국 전체 순위표(행사자이름/소속매니저/거래처/누적매출/일평균매출/내 소속 여부)
