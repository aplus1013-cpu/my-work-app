# -*- coding: utf-8 -*-
"""
Feature 2: AI 이미지 생성 도구 (OpenAI 이미지 생성 API)

입력 : 짧은 이미지 설명 문장 (커맨드라인 인자 또는 실행 시 직접 입력)
동작 : OpenAI Images API(gpt-image-1)로 설명에 맞는 이미지를 한 번에 2장 생성
출력 : 이 폴더의 images/ 폴더에 PNG 파일로 저장 (파일명에 날짜·설명·순번 포함)

사용법:
    python generate_image.py "내 서비스 마스코트 - 물방울 모양 귀여운 캐릭터"
    (설명을 인자로 안 주면 실행 중에 입력받음)

API 키 준비 (둘 중 하나):
    1) PowerShell에서: $env:OPENAI_API_KEY = "sk-..."
    2) 이 폴더에 .env 파일을 만들고 한 줄만: OPENAI_API_KEY=sk-...
"""
import base64
import os
import re
import sys
from datetime import datetime

FOLDER = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(FOLDER, "outputs", "images")
ENV_FILE = os.path.join(FOLDER, ".env")


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


def slugify(text, max_len=30):
    text = re.sub(r"[^0-9A-Za-z가-힣]+", "_", text).strip("_")
    return text[:max_len] or "image"


def generate_image_bytes_list(description, size="1024x1024", n=2):
    from openai import OpenAI

    client = OpenAI(api_key=get_api_key())
    result = client.images.generate(
        model="gpt-image-1",
        prompt=description,
        size=size,
        n=n,
    )
    return [base64.b64decode(item.b64_json) for item in result.data]


def save_image(image_bytes, description, index, timestamp):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    # 파일명에 설명·날짜(타임스탬프)를 넣고, 한 번에 여러 장을 만들 때 겹치지 않도록 순번을 붙인다.
    filename = f"{timestamp}_{slugify(description)}_{index}.png"
    path = os.path.join(IMAGES_DIR, filename)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path


def run(description, n=2):
    print(f"이미지 생성 중... (설명: {description}, {n}장)")
    images = generate_image_bytes_list(description, n=n)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = []
    for i, image_bytes in enumerate(images, start=1):
        path = save_image(image_bytes, description, i, timestamp)
        print(f"저장 완료: {path}")
        paths.append(path)
    return paths


if __name__ == "__main__":
    if len(sys.argv) > 1:
        desc = " ".join(sys.argv[1:])
    else:
        desc = input("이미지 설명을 입력하세요: ").strip()
    if not desc:
        print("설명이 비어 있습니다.")
        sys.exit(1)
    run(desc)
