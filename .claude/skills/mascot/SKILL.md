---
name: mascot
description: Use when the user asks to run "mascot", or asks for "이미지 생성", "마스코트 만들어줘", "AI 이미지" — runs generate_image.py with a short description to create 2 AI images via the OpenAI image API and save them under outputs/images/.
version: 1.0.0
---

# Mascot

AI 이미지 생성(generate_image.py)을 실행하는 스킬.

## 무엇을

짧은 설명을 받아 OpenAI 이미지 생성 API로 이미지를 만들어 저장한다.

## 입력

- 사용자가 주는 짧은 이미지 설명 문장 (예: "내 서비스 마스코트 - 물방울 모양 귀여운 캐릭터")

## 순서

1. 사용자가 준 설명을 인자로 `python generate_image.py "설명"`을 실행한다. (설명이 없으면 사용자에게 물어본다.)
2. 한 번에 2장이 생성되며, `outputs/images/`에 저장된 파일 경로를 그대로 사용자에게 보여준다.

## 출력

- `outputs/images/` 폴더에 저장된 PNG 파일 2개 (파일명에 날짜·설명·순번 포함)
