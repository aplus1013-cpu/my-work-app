---
name: categorize
description: Use when the user asks to run "categorize", or asks for "메모 분류", "메모 카테고리", "메모 정리" — runs categorize_memos.py to classify every memo under inputs/memos/ into a category using the OpenAI chat API.
version: 1.0.0
---

# Categorize

메모 카테고리 자동 분류(categorize_memos.py)를 실행하는 스킬.

## 무엇을

`inputs/memos/` 안의 메모들을 읽어, 정해진 카테고리(회의/아이디어/할 일/자료조사/피드백/공지/기타) 중 어울리는 것을 OpenAI로 골라준다.

## 입력

- `inputs/memos/*.md`, `*.txt` (별도 인자 없이 폴더 안 메모 전부 사용)

## 순서

1. `python categorize_memos.py`를 실행한다.
2. 메모별로 분류된 카테고리와 선택 이유를 콘솔에 그대로 보여준다.

## 출력

- 파일명 - 카테고리 - 선택 이유 목록
