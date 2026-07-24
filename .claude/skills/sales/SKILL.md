---
name: sales
description: Use when the user asks to run "sales", or asks for "매출 요약", "행사자 매출 계산", "판촉사원 매출" — runs feature1_engine.py against the sample sales excel files and shows each promo-staff employee's cumulative sales, achievement rate, and national store ranking.
version: 1.0.0
---

# Sales

행사자별 매출 요약 계산 엔진(feature1_engine.py)을 실행하는 스킬.

## 무엇을

채널별 매출 엑셀을 검증·정제한 뒤, 행사자별 누적매출·목표대비 달성률과 거래처별 전국순위를 계산해서 보여준다.

## 입력

- `inputs/sales/*유인행사매출*.xlsx` (별도 인자 없이 폴더 안 파일을 전부 사용)

## 순서

1. `python feature1_engine.py`를 실행한다.
2. 콘솔에 출력되는 데이터 정제 로그, 완전히 제외된 행사자, 행사자별 결과를 그대로 사용자에게 보여준다.

## 출력

- 행사자별 이름/누적매출/달성률과, 거래처별 채널·품목군 조합 전국순위·근무일수·일평균매출
