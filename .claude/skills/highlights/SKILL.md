---
name: highlights
description: Use when the user asks to run "highlights", or asks for "핵심 항목", "핵심만 뽑아줘", "결과 핵심 요약" — runs extract_highlights.py to pull just the key topic names out of a summary/result file via the OpenAI chat API.
version: 1.0.0
---

# Highlights

요약 결과에서 핵심 항목만 추출(extract_highlights.py)을 실행하는 스킬.

## 무엇을

요약/결과 문서에서 세부 수치나 실행 방법은 빼고, 무엇에 대한 이야기인지 핵심 항목명만 짧게 뽑아 보여준다.

## 입력

- 요약 마크다운 파일 경로 (생략하면 기본 샘플 `outputs/weekly-report-2.md` 사용)

## 순서

1. 사용자가 파일 경로를 주면 그 값으로, 안 주면 기본값으로 `python extract_highlights.py [파일경로]`를 실행한다.
2. 추출된 핵심 항목을 번호 목록으로 사용자에게 보여준다.

## 출력

- "핵심 항목" 번호 목록
