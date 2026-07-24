# -*- coding: utf-8 -*-
"""
결과를 한 줄 요약과 함께 보여주는 기능 (OpenAI GPT API)

입력 : 결과/요약 마크다운 파일 (기본값: outputs/weekly-report-2.md 샘플)
동작 : 내용을 OpenAI Chat API에 보내 정확히 한 문장으로 요약하게 함
출력 : "한 줄 요약" + 원본 결과 전체를 콘솔에 함께 출력

API 키는 다른 GPT 기능들과 동일하게 .env 파일 또는 OPENAI_API_KEY 환경변수를 사용합니다.

사용법:
    python summarize_one_line.py                      (기본 샘플 파일로 실행)
    python summarize_one_line.py "경로/다른_결과.md"    (다른 파일 지정)
"""
import os
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(FOLDER, ".env")
DEFAULT_RESULT_FILE = os.path.join(FOLDER, "outputs", "weekly-report-2.md")


def load_env_file():
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


def summarize_one_line(text):
    from openai import OpenAI

    client = OpenAI(api_key=get_api_key())
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                "다음 내용을 정확히 한 문장으로 요약해주세요. "
                "다른 설명이나 따옴표 없이 한 문장만 출력하세요.\n\n"
                f"내용:\n{text}"
            ),
        }],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def run(result_path=None):
    result_path = result_path or DEFAULT_RESULT_FILE
    if not os.path.exists(result_path):
        print(f"결과 파일을 찾을 수 없습니다: {result_path}")
        return None

    with open(result_path, "r", encoding="utf-8") as f:
        result_text = f.read()

    one_liner = summarize_one_line(result_text)

    print("=" * 70)
    print(f"[한 줄 요약] {one_liner}")
    print("=" * 70)
    print(f"[원본 결과] ({os.path.basename(result_path)})")
    print("-" * 70)
    print(result_text)

    return one_liner


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    run(path)
