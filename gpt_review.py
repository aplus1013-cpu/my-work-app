# -*- coding: utf-8 -*-
"""
GPT API로 문서를 검증해 리뷰 결과를 저장하는 기능 (cross-review 스킬의 1단계)

입력 : 검증할 마크다운 파일 경로 (기본값: specs/기획서.md)
동작 : 파일 내용을 OpenAI Chat API에 보내, "사실/논리/누락/톤·형식" 4가지 기준으로
       문서를 고쳐 쓰지 않고 문제점만 짚게 함
출력 : outputs/{원본파일명}-gpt-review.md 로 저장, 콘솔에도 그대로 출력

API 키는 generate_image.py / categorize_memos.py와 동일하게 .env 파일 또는
OPENAI_API_KEY 환경변수를 사용합니다.

사용법:
    python gpt_review.py                      (기본 대상: specs/기획서.md)
    python gpt_review.py "경로/다른_문서.md"    (다른 파일 지정)
"""
import json
import os
import re
import sys

FOLDER = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(FOLDER, ".env")
DEFAULT_TARGET_FILE = os.path.join(FOLDER, "specs", "기획서.md")
OUTPUT_DIR = os.path.join(FOLDER, "outputs")

CATEGORIES = ["사실", "논리", "누락", "톤·형식"]


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


def review_document(text):
    from openai import OpenAI

    client = OpenAI(api_key=get_api_key())
    prompt = f"""당신은 까다로운 사내 검토자입니다. 아래는 검토 대상 문서(마크다운)입니다.
이 문서를 다시 쓰지 말고, 문제점만 항목별로 짚어주세요.

점검 기준 4가지:
1. 사실: 숫자·이름·날짜·인용 중 근거 없이 지어낸 것으로 의심되는 부분, 또는 문서 내 다른 부분과 수치가 어긋나는 부분
2. 논리: 주장과 근거가 맞지 않는 부분, 섹션 제목과 실제 내용이 어긋나는 부분, 앞뒤 단계 순서나 인과관계가 이상한 부분
3. 누락: 이 문서가 다루는 프로세스라면 당연히 있어야 하는데 빠진 내용 (예: 실패/예외 상황일 때 어떻게 하는지, 승인이 거부되면 어떻게 되는지, 담당자가 자리를 비우면 어떻게 되는지 등 운영 관점의 빈틈)
4. 톤·형식: 실무 담당자가 읽었을 때 어색하거나, 항목마다 표현 방식(문체·구조)이 들쭉날쭉하거나, 헤딩과 본문 내용이 안 맞는 부분

문서를 문장 단위로 실제로 꼼꼼히 훑어보고 판단하세요. 대충 훑고 "문제없음"으로 넘어가지 마세요.
근거 없이 트집을 잡으라는 뜻은 아닙니다 — 정말 검토해봤는데도 그 기준에서 지적할 게 전혀 없다면 해당 배열은 비워도 됩니다.
각 지적은 반드시 "어느 문장/항목을 가리키는지"와 "왜 문제인지"를 포함해야 합니다.

반드시 아래 JSON 형식으로만 답하세요 (다른 설명이나 마크다운 코드블록 표시 없이):
{{
  "사실": [{{"location": "인용하거나 가리키는 문장/항목", "issue": "왜 문제인지 한두 문장"}}],
  "논리": [{{"location": "...", "issue": "..."}}],
  "누락": [{{"location": "...", "issue": "..."}}],
  "톤·형식": [{{"location": "...", "issue": "..."}}]
}}

검토 대상 문서 전문:
---
{text}
---
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def build_markdown(result, source_path):
    lines = [
        f"# GPT 검토 결과: {os.path.basename(source_path)}",
        "",
        f"검토 대상: `{os.path.relpath(source_path, FOLDER)}`",
        "검토 도구: OpenAI GPT API (gpt-4o) — 문서를 다시 쓰지 않고 문제점만 짚음",
        "",
        "---",
        "",
    ]
    for cat in CATEGORIES:
        items = result.get(cat, [])
        lines.append(f"## {cat}")
        lines.append("")
        if not items:
            lines.append("- 특이사항 없음")
        else:
            for item in items:
                location = str(item.get("location", "")).strip()
                issue = str(item.get("issue", "")).strip()
                lines.append(f"- **{location}** — {issue}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run(target_path=None):
    target_path = target_path or DEFAULT_TARGET_FILE
    if not os.path.exists(target_path):
        print(f"검토할 파일을 찾을 수 없습니다: {target_path}")
        return None

    with open(target_path, "r", encoding="utf-8") as f:
        text = f.read()

    result = review_document(text)
    markdown = build_markdown(result, target_path)

    stem = os.path.splitext(os.path.basename(target_path))[0]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{stem}-gpt-review.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print("=" * 70)
    print(f"[GPT 검토 완료] {os.path.basename(target_path)} -> {output_path}")
    print("=" * 70)
    print(markdown)

    return output_path


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    run(path)
