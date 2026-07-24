# -*- coding: utf-8 -*-
"""
Feature 3: 메모 카테고리 자동 분류 (OpenAI GPT API)

입력 : 이 폴더의 memos/ 안에 있는 메모 파일들(.md, .txt)
동작 : 각 메모 내용을 OpenAI Chat API에 보내, 정해진 카테고리 중 어울리는 것 하나를 고르게 함
출력 : 파일명 - 카테고리 - 선택 이유를 콘솔에 정리해서 보여줌

API 키는 generate_image.py와 동일하게 .env 파일 또는 OPENAI_API_KEY 환경변수를 사용합니다.
"""
import glob
import json
import os
import re

FOLDER = os.path.dirname(os.path.abspath(__file__))
MEMOS_DIR = os.path.join(FOLDER, "inputs", "memos")
ENV_FILE = os.path.join(FOLDER, ".env")

CATEGORIES = ["회의", "아이디어", "할 일", "자료조사", "피드백", "공지", "기타"]


def load_env_file():
    """.env 파일이 있으면 KEY=VALUE 줄들을 읽어 환경변수로 보충한다 (파일 없으면 무시)."""
    if not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_api_key():
    load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY가 설정되어 있지 않습니다.\n"
            '  1) PowerShell: $env:OPENAI_API_KEY = "sk-..." 로 설정하거나\n'
            f"  2) 이 파일을 만들어 한 줄만 넣어주세요: {ENV_FILE}\n"
            "     OPENAI_API_KEY=sk-..."
        )
    return api_key


def load_memos():
    paths = sorted(
        glob.glob(os.path.join(MEMOS_DIR, "*.md")) + glob.glob(os.path.join(MEMOS_DIR, "*.txt"))
    )
    memos = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            memos.append({"파일명": os.path.basename(path), "내용": f.read()})
    return memos


def categorize_memo(memo_text):
    from openai import OpenAI

    client = OpenAI(api_key=get_api_key())
    prompt = (
        "다음은 사내 메모입니다. 아래 카테고리 중 가장 어울리는 것 하나만 고르세요.\n"
        f"카테고리: {', '.join(CATEGORIES)}\n\n"
        "반드시 아래 JSON 형식으로만 답하세요 (다른 설명 붙이지 말 것):\n"
        '{"category": "카테고리명", "reason": "한 줄 이유"}\n\n'
        f"메모 내용:\n{memo_text}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(raw)
        category = str(parsed.get("category", "")).strip()
        reason = str(parsed.get("reason", "")).strip()
    except json.JSONDecodeError:
        category, reason = raw, ""

    if category not in CATEGORIES:
        reason = f"(모델 응답 '{category}'이(가) 목록에 없어 기타로 처리) {reason}".strip()
        category = "기타"

    return category, reason


def run():
    memos = load_memos()
    if not memos:
        print(f"메모 파일을 찾을 수 없습니다: {MEMOS_DIR}")
        return []

    print("=" * 70)
    print(f"[메모 카테고리 분류 결과] 총 {len(memos)}건 (카테고리 후보: {', '.join(CATEGORIES)})")
    print("=" * 70)

    results = []
    for memo in memos:
        category, reason = categorize_memo(memo["내용"])
        results.append({**memo, "카테고리": category, "이유": reason})
        line = f"- {memo['파일명']} -> [{category}]"
        if reason:
            line += f" ({reason})"
        print(line)

    return results


if __name__ == "__main__":
    run()
