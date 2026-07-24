---
name: cross-review
description: Use when the user asks to run "cross-review", or asks for "교차검증", "GPT랑 같이 검증", "이중 검증", "GPT랑 크로스체크" — runs gpt_review.py to get an independent GPT API review of a given file, then has Claude independently review the same file (without reading the GPT result first) against the same criteria, and finally compares both reviews into a 공통/한쪽만/엇갈림 table.
version: 1.0.0
---

# Cross Review

한 문서를 GPT API와 Claude가 각각 독립적으로 검증한 뒤, 두 결과를 비교해서 보여주는 스킬.

## 무엇을

사용자가 지정한 파일을 두 번 따로 검증한다 — 한 번은 OpenAI GPT API로, 한 번은 Claude가 직접. 순서를 지켜서 서로의 결과를 못 보게 해야 진짜 독립적인 두 번째 의견이 나온다.

## 입력

- 검증할 파일 경로 (생략하면 기본값 `specs/기획서.md` 사용)
- 점검 기준은 항상 4가지로 고정: **사실 · 논리 · 누락 · 톤/형식**

## 순서

1. **GPT 검증**: `python gpt_review.py [파일경로]`를 실행한다. GPT API가 파일을 4가지 기준으로 검증하고, 결과가 `outputs/{파일명}-gpt-review.md`로 저장된다.
2. **Claude 독립 검증**: 1번에서 저장된 결과 파일은 **아직 열어보지 않는다.** Claude가 원본 파일을 직접 읽고, 같은 4가지 기준(사실·논리·누락·톤/형식)으로 문제점만 짚는다. 각 지적은 "어느 문장인지 + 왜 문제인지"를 짧게 적는다. 이 순서를 반드시 지킨다 — GPT 결과를 먼저 보면 독립적인 두 번째 의견이 나올 수 없다.
3. **비교**: 이제 1번 결과 파일을 열어서, 2번(Claude 검증)과 다음 세 가지로 나눠 표로 정리한다:
   - 공통으로 지적한 것 (→ 확실히 고칠 후보)
   - 한쪽만 지적한 것 (→ 확인해볼 것)
   - 서로 엇갈리는 것 (→ 각각의 근거를 함께 적음)

   GPT 쪽 지적이 실제로는 틀렸다고 판단되면(예: 모델이 오늘 날짜를 착각하는 등), 표에서 빼지 말고 남기되 왜 신뢰하기 어려운지 같이 적는다.

## 출력

- `outputs/{파일명}-gpt-review.md` (GPT 검증 결과 파일)
- 대화창에 Claude의 독립 검증 결과 (항목별, 원본 열어보기 전에 작성한 것)
- 공통/한쪽만/엇갈림 비교 표
