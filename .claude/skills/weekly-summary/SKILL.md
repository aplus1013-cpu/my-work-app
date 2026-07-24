---
name: weekly-summary
description: Use when the user asks to run "weekly-summary", or asks for a "주간 요약", "주간 정리", "주간 데이터 정리" — reads the weekly data files provided for this run (current period + previous period), drafts a summary, and saves it as a file.
version: 1.0.0
---

# Weekly Summary

주간 데이터를 읽어 정리 초안을 만드는 스킬.

## 입력

- 그때그때 사용자가 제공하는 주간 데이터 파일 (이번 회차, 지난 회차)

## 순서

1. 사용자가 준 데이터 파일들을 읽는다.
2. 핵심을 세 줄로 요약하고, 지난 회차 대비 달라진 점을 한 줄 덧붙인다.
3. 챙겨야 할 이슈를 목록으로 정리한다.
4. 결과를 파일로 저장한다.

## 출력

- 요약(3줄) + 지난 회차 대비 달라진 점(1줄) + 이슈 목록이 담긴 정리 파일 하나

## 조건

- 제공된 자료에 없는 내용은 지어내지 않는다. 자료에서 확인할 수 없는 부분은 추측하지 말고 "자료에서 확인 불가"로 명시한다.
