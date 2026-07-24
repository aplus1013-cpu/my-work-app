# -*- coding: utf-8 -*-
"""
요약 결과에서 '오늘 할 일'만 뽑아 보여주는 기능 (OpenAI GPT API)

입력 : 요약 결과 마크다운 파일 (기본값: outputs/weekly-report-2.md 샘플)
동작 : 요약 내용을 OpenAI Chat API에 보내, 실행 가능한 액션 아이템(할 일)만 골라내게 함
출력 : "오늘 할 일" 목록을 콘솔에 출력

API 키는 generate_image.py / categorize_memos.py와 동일하게 .env 파일 또는
OPENAI_API_KEY 환경변수를 사용합니다.

사용법:
    python extract_todos.py                      (기본 샘플 요약 파일로 실행)
    python extract_todos.py "경로/다른_요약.md"    (다른 요약 파일 지정)
"""
import json
import os
import re
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(FOLDER, ".env")
DEFAULT_SUMMARY_FILE = os.path.join(FOLDER, "outputs", "weekly-report-2.md")


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


def extract_todos(summary_text):
    from openai import OpenAI

    client = OpenAI(api_key=get_api_key())
    prompt = (
        "다음은 업무 요약 결과입니다. 이 안에서 '오늘 할 일'로 볼 수 있는, "
        "실행 가능한 액션 아이템만 뽑아주세요. 매출·방문자 수치 같은 상태 설명이나 "
        "이미 끝난 일은 제외하고, 앞으로 해야 할 일(검토·확인·보강·채용 등)만 골라주세요.\n\n"
        "반드시 아래 JSON 형식으로만 답하세요 (다른 설명 금지):\n"
        '{"todos": ["할 일 1", "할 일 2"]}\n\n'
        f"요약 내용:\n{summary_text}"
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
        todos = parsed.get("todos", [])
    except json.JSONDecodeError:
        todos = [raw]

    return todos


def run(summary_path=None):
    summary_path = summary_path or DEFAULT_SUMMARY_FILE
    if not os.path.exists(summary_path):
        print(f"요약 파일을 찾을 수 없습니다: {summary_path}")
        return []

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_text = f.read()

    todos = extract_todos(summary_text)

    print("=" * 70)
    print(f"[오늘 할 일] ({os.path.basename(summary_path)} 기준)")
    print("=" * 70)
    if not todos:
        print("(뽑아낼 할 일이 없습니다)")
    for i, todo in enumerate(todos, start=1):
        print(f"{i}. {todo}")

    return todos


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    run(path)
