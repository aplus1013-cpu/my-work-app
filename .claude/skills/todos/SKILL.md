---
name: todos
description: Use when the user asks to run "todos", or asks for "할 일 뽑기", "오늘 할 일", "액션 아이템" — runs extract_todos.py to pull only actionable to-do items out of a summary/result file via the OpenAI chat API.
version: 1.0.0
---

# Todos

요약 결과에서 할 일만 추출(extract_todos.py)을 실행하는 스킬.

## 무엇을

요약/결과 문서에서 매출·방문자 같은 상태 설명은 빼고, 실행 가능한 할 일(액션 아이템)만 뽑아 보여준다.

## 입력

- 요약 마크다운 파일 경로 (생략하면 기본 샘플 `outputs/weekly-report-2.md` 사용)

## 순서

1. 사용자가 파일 경로를 주면 그 값으로, 안 주면 기본값으로 `python extract_todos.py [파일경로]`를 실행한다.
2. 추출된 할 일 목록을 하나도 빠짐없이 번호 목록으로 사용자에게 보여준다.

## 출력

- "오늘 할 일" 번호 목록 (전부)
