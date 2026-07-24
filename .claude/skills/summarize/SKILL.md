---
name: summarize
description: Use when the user asks to run "summarize", or asks for "한 줄 요약", "결과 요약해줘" — runs summarize_one_line.py to produce a single-sentence summary of a result file, shown together with the original result.
version: 1.0.0
---

# Summarize

결과를 한 줄 요약과 함께 보여주기(summarize_one_line.py)를 실행하는 스킬.

## 무엇을

결과/요약 문서를 정확히 한 문장으로 요약하고, 그 한 줄 요약과 원본 결과 전문을 함께 보여준다.

## 입력

- 결과 마크다운 파일 경로 (생략하면 기본 샘플 `outputs/weekly-report-2.md` 사용)

## 순서

1. 사용자가 파일 경로를 주면 그 값으로, 안 주면 기본값으로 `python summarize_one_line.py [파일경로]`를 실행한다.
2. 한 줄 요약과 원본 결과 전문을 함께 사용자에게 보여준다.

## 출력

- 한 줄 요약 + 원본 결과 전문
