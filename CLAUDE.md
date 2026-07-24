# CLAUDE.md

이 파일은 이 저장소에서 작업할 때 Claude Code(claude.ai/code)에게 제공되는 가이드입니다.

## 이 저장소는 무엇인가

"판촉사원(행사자) 매출 요약" 도구를 위한 연습/프로토타입 프로젝트입니다 — 매주 판촉사원 매출 데이터(전부 가짜/연습용 데이터이며 실제 회사 데이터는 절대 사용하지 않음)를 받아 행사자별 요약과 매니저별 코칭 화면으로 만드는 작업입니다. 프레임워크나 패키지 구조, 빌드 단계 없이 몇 개의 독립적인 단일 파일 파이썬 스크립트와 이를 뒷받침하는 마크다운 명세·샘플 데이터로 구성되어 있습니다. 이 폴더는 git 저장소가 아닙니다.

각 스크립트는 그 자체로 독립 실행 가능합니다. 스크립트 사이에 공유하는 라이브러리 모듈은 없으며, `feature2_manager_view.py`는 패키지 경계 없이 `feature1_engine.py`를 직접 임포트합니다(`import feature1_engine as f1`).

## 명령어

패키지 매니페스트(requirements.txt/pyproject.toml)가 없어서, 의존성은 그때그때 수동으로 설치했습니다:

```powershell
pip install openpyxl   # feature1_engine.py(.xlsx 읽기), feature3/feature4(.xlsx 쓰기)
pip install openai     # generate_image.py, categorize_memos.py
```

각 기능은 저장소 루트에서 실행합니다(스크립트 안의 경로는 스크립트 자신의 위치를 기준으로 계산되므로, `python <경로>\feature1_engine.py` 형태로 어디서든 실행 가능하며 `cd`는 필요 없습니다):

```powershell
python feature1_engine.py                      # 매출 요약 계산 엔진, inputs/sales/*.xlsx를 읽음
python feature2_manager_view.py                # 매니저 코칭 화면, feature1의 결과 위에서 동작
python feature3_employee_pages.py               # 행사자별 요약 엑셀 파일 생성 -> outputs/employee-pages/
python feature4_manager_pages.py                # 매니저코칭용 엑셀 파일 생성 -> outputs/manager-pages/
python generate_image.py "짧은 이미지 설명"      # OpenAI 이미지 생성 -> outputs/images/
python categorize_memos.py                     # inputs/memos/*.md를 OpenAI로 분류
python gpt_review.py [파일경로]                 # GPT API로 문서 검증 -> outputs/{파일명}-gpt-review.md (cross-review 스킬 1단계, 기본값: specs/기획서.md)
```

테스트 스위트나 린터는 설정되어 있지 않습니다. 정확성 검증은 `inputs/`의 샘플 데이터로 각 스크립트를 직접 실행하고 콘솔 출력을 확인하는 방식으로 합니다 — `feature1_engine.py`의 계산 로직을 바꿀 때는, 완료로 간주하기 전에 다시 실행해서 `[데이터 정제 로그]`와 행사자별 출력이 여전히 기대한 대로 나오는지 확인해야 합니다.

`generate_image.py`, `categorize_memos.py`, `gpt_review.py`는 실제 OpenAI API를 호출하며 실행마다 비용이 발생합니다 — 먼저 `.env`(저장소 루트) 또는 환경변수에 `OPENAI_API_KEY`가 설정되어 있어야 합니다.

## 아키텍처

### 데이터 흐름: feature1 -> feature2 -> feature3 / feature4

`feature1_engine.py`는 핵심 계산 엔진이며 매출 관련 모든 것의 의존성 루트입니다:

1. `inputs/sales/*유인행사매출*.xlsx` 파일을 전부 읽습니다. **파일 하나당 채널 하나**이며, 채널 코드는 파일명 자체에서 정규식(`"...월 <채널> ...주차..."`)으로 파싱됩니다 — 데이터 안에 채널 컬럼은 없습니다.
2. 26개 필수 컬럼을 검증하고 행을 파싱한 뒤, 두 단계로 정제합니다: `remove_missing`(필수 항목 빈 값)과 `remove_outliers`(음수 금액, 총판매금액 대 판매금액1+2+3 불일치, *자기 자신을 제외한* 그룹 평균 대비 5배 이상 급증, 거래처번호+행사자사번+마감일+품목군 기준 중복 행).
3. `compute_employee_summaries`: 행사자별 누적 매출과, 누적일수 비율로 환산한 목표 대비 달성률(목표 × 월중 경과일수 ÷ 해당월 전체일수 — 원본 달성률 컬럼이 아닙니다. 그 컬럼은 하루 단위 값이라 DayRate/LineCount처럼 이 앱에서는 쓰지 않습니다).
4. `compute_store_rankings`: (채널, 품목군 조합) 기준으로 그룹핑합니다. 그룹 소속 여부는 **순서 무관**입니다 — `item_group_tuple()`이 품목군 값을 정렬하므로 `["가전","생활가전"]`과 `["생활가전","가전"]`은 같은 그룹입니다. 그룹 내 순위는 누적 총액이 아니라 **일평균매출(누적매출 ÷ 근무일수)** 기준입니다 — 이는 의도된 설계로, 단순히 근무일이 많다는 이유만으로 우위를 점하지 못하게 하기 위함입니다. "그룹인원수"는 행사자사번 기준으로 중복 제거됩니다(한 사람이 같은 그룹에 거래처 두 곳으로 들어가 있어도, 순위 슬롯은 두 개 차지하지만 인원수는 한 명으로 셉니다).
5. `compute_all()`은 (각 항목의 자기 순위뿐 아니라 그룹별 전국 전체 순위 목록인 `group_rankings`까지 포함해) 아무것도 출력하지 않고 전체 결과를 반환하며, `run()`은 이를 감싸서 콘솔 출력을 덧붙입니다. **feature1의 데이터를 프로그램적으로 사용할 때는 `run()`이 아니라 `compute_all()`을 호출해야** 콘솔 로그가 중복 출력되지 않습니다. `attach_achievement_rate()`가 `group_rankings`의 순위 행마다 해당 행사자의 달성률을 붙여주는데, 이건 `report`에는 행사자당 1개로만 있던 값을 그룹 순위 행 단위로도 쓸 수 있게 하기 위함입니다(feature4가 필요로 함).

`feature2_manager_view.py`는 `compute_all()`의 `report` + `group_rankings`를 사용합니다: 매니저별로 소속 행사자가 속한 모든 (채널, 품목군 조합) 그룹을 찾아, 그 그룹의 **전국 전체 순위**를 그대로 보여주고(매니저 자기 소속 행사자만 뽑은 목록이 아님) 어느 행이 그 매니저 소속인지 표시합니다(`내소속`). 이는 의도된 설계입니다 — 매니저는 자기 팀만 따로 떼어놓은 시야가 아니라, 전체 순위 안에서 자기 팀이 어디에 있는지를 봐야 합니다.

`feature3_employee_pages.py`와 `feature4_manager_pages.py`는 각각 feature1의 `report`, feature2의 `manager_views`를 그대로 받아 openpyxl로 엑셀 파일을 렌더링만 합니다 — 계산 로직은 전혀 갖고 있지 않고, 행사자/매니저 한 명당 파일 하나씩 `outputs/employee-pages/`, `outputs/manager-pages/`에 `.xlsx`로 저장합니다. 새 계산이 필요 없으므로 두 스크립트 모두 각자 `run()` 안에서 바로 `f1.compute_all()`(feature4는 `f2.build_manager_views()`까지)을 호출합니다. (기획서상 최종 형태는 웹페이지/URL 링크지만, 지금은 연습 단계 간소화로 엑셀 파일로 대체 — `feature-3-spec.md`/`feature-4-spec.md`에 명시)

`generate_image.py`와 `categorize_memos.py`는 서로 무관한 별개의 OpenAI API 기능(이미지 생성, 메모 분류)이지만, `.env` 로딩 패턴(`load_env_file()` / `get_api_key()`, `OPENAI_API_KEY` 읽기)을 그대로 복붙해서 공유하고 있습니다 — 공유 모듈이 없으므로, 이 로직을 바꾸려면 두 곳 모두 수정해야 합니다.

### 폴더 구조

- 루트: 실행 코드만 있음(`feature1_engine.py`, `feature2_manager_view.py`, `feature3_employee_pages.py`, `feature4_manager_pages.py`, `generate_image.py`, `categorize_memos.py`), 그리고 `.env`와 `.claude/`. 스크립트는 `os.path.dirname(os.path.abspath(__file__))`로 자기 위치를 기준 삼아 데이터를 찾으므로, **스크립트를 루트 밖으로 옮기면 `inputs/`/`outputs/`로의 상대경로가 깨집니다** (해당 경로 상수도 같이 고치지 않는 한).
- `inputs/` — 샘플/연습용 데이터만 있으며, 어떤 기능이 쓰는지에 따라 나뉘어 있습니다(`sales/`, `memos/`). 전부 가상 데이터이며, 실제 회사 데이터는 절대 여기에 넣지 않습니다.
- `specs/` — 기획 문서: `기획서.md`(전체 26단계 파이프라인 + 제약사항을 담은 마스터 플랜)와 `매출요약앱_흐름도.md`(같은 내용을 흐름도 형식으로 정리한 것)는 서로, 그리고 각 기능별 명세(`feature-1-spec.md` ~ `feature-4-spec.md`)와 내용이 맞아야 합니다. 코드에서 계산 규칙을 바꾸면 `기획서.md`/`매출요약앱_흐름도.md`의 해당 항목과 관련 `feature-N-spec.md`를 같이 갱신하세요 — 예전에 이 문서들이 서로 어긋나서 나중에 맞춰야 했던 적이 있습니다.
- `outputs/` — 생성된 결과물(`images/`, `employee-pages/`, `manager-pages/`, 리포트 파일들). 이 안의 것은 전부 자동 생성된 것이며 사람이 직접 작성한 게 아닙니다.
- `practice/` — 기획서와 무관한 실습용 연습 자료·산출물(엑셀→워드 데모, 노션 정리 연습, 주간보고 샘플 등). "진짜 App"과는 분리되어 있고, 어떤 스크립트도 이 폴더를 참조하지 않습니다.

### 스코프 원칙 (기능 명세)

각 `feature-N-spec.md`에는 "지금은 뺄 것" 섹션이 있습니다. `feature-3-spec.md`(행사자별 요약페이지)와 `feature-4-spec.md`(매니저코칭용페이지) 덕분에 **파일 형태의 결과물 생성까지는 구현되었지만**, 기획서가 말하는 "웹페이지(URL 링크)"가 아니라 **엑셀 파일**로 대체되어 있습니다(연습 단계 간소화). 저장(영속화)·담당자 승인 절차·카카오톡 자동 발송·실제 URL 배포는 네 기능 모두에서 여전히 범위 밖입니다. `기획서.md`의 전체 파이프라인 중 19~20, 25~26단계(승인 + 카카오톡 발송)가 아직 구현되지 않은 부분입니다.

### 엑셀 입력 포맷 관련 주의사항

`기획서.md`/`매출요약앱_흐름도.md`의 입력 컬럼 목록은 `feature1_engine.py`의 `REQUIRED_COLUMNS`와 일치하도록 정리되어 있습니다: 실제 파일에는 `2차점ID`/`2차점명`이 있고 `채널`/`본부` 컬럼은 없습니다(채널은 위에서 설명했듯 파일명에서 가져옴). 혹시라도 둘이 어긋나 보이면 `feature1_engine.py`의 `REQUIRED_COLUMNS`가 실제 파일 구조를 반영한 최종 기준이니 이쪽을 따르고, 스펙 문서 쪽을 다시 맞추세요.

## 작업 규칙

세부 규칙은 `rules/` 폴더에 주제별로 나눠져 있습니다.

**절대 규칙** (항상 지킬 것)
- 실명·실제 사내 자료는 절대 넣지 않는다 — 연습은 항상 가짜 데이터로만 진행한다.
- 답변은 항상 한국어로, 공손하고 간결하게 쓴다.

**규칙 인덱스**
- 역할 규칙 → [rules/role.md](rules/role.md)
- 말투 규칙 → [rules/tone.md](rules/tone.md)
- 결과 형식 규칙 → [rules/format.md](rules/format.md)
- 하지 말 것 규칙 → [rules/restrictions.md](rules/restrictions.md)

**우선순위**
- 규칙끼리 부딪치면, 형식 제약(예: 세 줄 요약)보다 내용을 빠짐없이 보여주는 것을 우선한다.