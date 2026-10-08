# cli-utils

개인용 Python 기반 CLI 유틸리티 모음 모노레포입니다.  
[`uv`](https://docs.astral.sh/uv/)의 **워크스페이스(Workspace)** 기능을 활용하여 각 도구별 독립적인 의존성 관리 및 통합 개발 환경을 제공합니다.

---

## 📁 프로젝트 구조

```text
cli-utils/
├── .gitignore
├── README.md                   # 프로젝트 전체 안내 문서
├── pyproject.toml              # uv 워크스페이스 루트 설정
├── uv.lock                     # 전체 의존성 잠금 파일
│
├── kakao-emoticon/             # [도구 1] 카카오 이모티콘 다운로더 & GIF 변환기
│   ├── pyproject.toml
│   ├── README.md
│   └── kakao_emoticon/
│       ├── __init__.py
│       └── main.py
│
└── hdd-rename/                 # [도구 2] HDD 파일 일괄 이름 변경 도구 (개발 진행 중)
    ├── pyproject.toml
    ├── README.md
    └── hdd_rename/
        ├── __init__.py
        └── main.py
```

---

## 🛠️ 포함된 도구 소개

### 1. `kakao-emoticon`
- **설명**: 카카오 이모티콘 상세 페이지 URL에서 원본 스티커 이미지를 다운로드하고, 필요한 경우 애니메이션 GIF 변환 및 파일명 일괄 변경용 `index.html`을 생성합니다.
- **주요 옵션**:
  - `url`: 이모티콘 상세 페이지 URL
  - `--gif`: 원본 webp를 무한 반복 GIF로 변환 (시스템에 `ffmpeg` 필요)
  - `--index`: 웹 브라우저에서 보며 이름을 변경할 수 있는 `index.html` 생성

### 2. `hdd-rename`
- **설명**: 하드디스크 내 대량 파일의 정리 및 이름 변경을 위한 CLI 도구 (개발 진행 중).

---

## 🚀 빠른 시작 & 개발 환경 구축

uv가 설치되어 있다면 루트 디렉터리에서 아래 명령어로 모든 패키지와 의존성을 가상환경에 동기화할 수 있습니다:

```bash
# 가상환경(.venv) 생성 및 모든 하위 패키지 의존성 설치
uv sync
```

---

## 💻 개발 워크플로우 (Development)

### 1. 개발 중 테스트 실행 (`uv run`)
가상환경을 활성화(`source .venv/bin/activate`)하지 않고도 `uv run`을 통해 바로 도구를 실행할 수 있습니다:

```bash
# kakao-emoticon 실행
uv run kakao-emoticon --help
uv run kakao-emoticon "https://e.kakao.com/t/sample-url" --gif

# hdd-rename 실행
uv run hdd-rename
```

### 2. 의존성 패키지 관리 (`uv add` / `uv remove`)
각 도구에 필요한 외부 라이브러리는 `--package` 옵션을 붙여 추가하거나 삭제합니다:

```bash
# kakao-emoticon에 라이브러리 추가
uv add httpx beautifulsoup4 --package kakao-emoticon

# hdd-rename에 라이브러리 추가 (예: click, rich)
uv add rich --package hdd-rename

# 특정 패키지 제거
uv remove <패키지명> --package <대상프로젝트>
```

### 3. 의존성 트리 확인 (`uv tree`)
```bash
# 전체 워크스페이스 의존성 트리 확인
uv tree

# 특정 패키지만 확인
uv tree --package kakao-emoticon
```

---

## 📦 전역 CLI 명령어로 설치 (uv tool)

어떤 디렉터리 경로에서든 터미널에서 명령어(`kakao-emoticon`, `hdd-rename`)로 직접 호출할 수 있도록 시스템 전역(사용자 계정 레벨)에 설치합니다.

### 1. 편집 모드(`--editable`)로 설치 (권장)
`--editable` 옵션으로 설치하면 로컬 소스 코드와 연결되므로, **코드를 수정하고 저장하면 별도 재설치 없이도 즉시 최신 코드가 실행**됩니다.

```bash
# kakao-emoticon 전역 등록 / 갱신
uv tool install --editable ./kakao-emoticon --force

# hdd-rename 전역 등록 / 갱신
uv tool install --editable ./hdd-rename --force
```

> **참고**: 전역 실행 파일은 `~/.local/bin/` 디렉터리에 설치됩니다. 터미널의 `PATH`에 해당 경로가 등록되어 있어야 합니다.

### 2. 설치된 전역 도구 관리
```bash
# 전역 설치된 툴 목록 확인
uv tool list

# 전역 도구 업데이트 (비 editable 설치 시)
uv tool upgrade kakao-emoticon

# 전역 도구 삭제
uv tool uninstall kakao-emoticon
uv tool uninstall hdd-rename
```

---

## ➕ 새로운 CLI 도구 추가하기

### ⚡ 자동 스크립트 사용 (권장)
제공된 `make-new-cli.sh` 스크립트를 실행하면 디렉터리 구성, `pyproject.toml`, 기본 코드 생성, 워크스페이스 등록 및 전역(--editable) 설치까지 한 번에 완료됩니다:

```bash
./make-new-cli.sh <새도구이름>

# 예시:
./make-new-cli.sh diary-extract
```

---

### 📝 수동 생성 절차
수동으로 추가할 경우 다음 절차를 따릅니다:

1. **디렉터리 및 패키지 생성**:
   ```bash
   mkdir -p my-tool/my_tool
   touch my-tool/my_tool/__init__.py
   touch my-tool/my_tool/main.py
   touch my-tool/README.md
   ```

2. **`my-tool/pyproject.toml` 작성**:
   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"

   [project]
   name = "my-tool"
   version = "0.1.0"
   description = "도구 설명"
   readme = "README.md"
   requires-python = ">=3.11"
   dependencies = []

   [project.scripts]
   my-tool = "my_tool.main:main"
   ```

3. **루트 `pyproject.toml`의 워크스페이스 멤버에 추가**:
   ```toml
   [tool.uv.workspace]
   members = [
       "hdd-rename",
       "kakao-emoticon",
       "my-tool",
   ]
   ```

4. **동기화 및 전역 설치**:
   ```bash
   uv sync
   uv tool install --editable ./my-tool
   ```

---

## 📖 핵심 uv 명령어 치트시트

| 분류 | 명령어 | 설명 |
| :--- | :--- | :--- |
| **동기화** | `uv sync` | `uv.lock`을 기반으로 가상환경 및 워크스페이스 동기화 |
| | `uv lock` | 의존성 잠금 파일(`uv.lock`) 최신 갱신 |
| **실행** | `uv run <명령어>` | 가상환경 컨텍스트 내에서 스크립트/명령어 실행 |
| | `uv run --package <이름> <명령어>` | 특정 서브패키지 환경으로 명령어 실행 |
| **의존성** | `uv add <패키지> --package <이름>` | 특정 프로젝트에 의존성 추가 |
| | `uv remove <패키지> --package <이름>` | 특정 프로젝트에서 의존성 제거 |
| | `uv tree` | 설치된 의존성 패키지 종속 트리 출력 |
| **전역 도구** | `uv tool install --editable <경로>` | 로컬 프로젝트를 전역 CLI로 심볼릭 링크 설치 |
| | `uv tool list` | 전역 설치된 CLI 도구 목록 조회 |
| | `uv tool uninstall <이름>` | 전역 설치된 CLI 도구 제거 |
| **파이썬 관리** | `uv python list` | 사용 가능한/설치된 Python 버전 목록 조회 |
| | `uv python install <버전>` | 특정 Python 런타임 다운로드 및 설치 (예: `3.13`) |
| | `uv python pin <버전>` | 현재 프로젝트의 기본 Python 버전 고정 (`.python-version`) |
