#!/usr/bin/env bash
set -euo pipefail

# 스크립트가 위치한 루트 디렉터리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_TOML="${SCRIPT_DIR}/pyproject.toml"

# 인자 확인
if [ $# -lt 1 ] || [ -z "$1" ]; then
    echo "========================================================"
    echo " [사용법] $0 <cli-name>"
    echo " [예  시] $0 diary-extract"
    echo "========================================================"
    echo "새로운 CLI 유틸리티의 보일러플레이트(패키지 구조, pyproject.toml 등)를"
    echo "생성하고, uv 워크스페이스 등록 및 전역(--editable) 설치까지 자동으로 수행합니다."
    exit 1
fi

CLI_NAME="$1"

# 이름 유효성 검사 (영문 소문자, 숫자, 하이픈, 언더스코어)
if [[ ! "$CLI_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
    echo "[오류] CLI 이름은 영문 소문자, 숫자, 하이픈(-), 언더스코어(_)만 사용할 수 있습니다: '$CLI_NAME'"
    exit 1
fi

# 파이썬 모듈명 (하이픈 -> 언더스코어)
MODULE_NAME="${CLI_NAME//-/_}"
TARGET_DIR="${SCRIPT_DIR}/${CLI_NAME}"

# 디렉터리 중복 체크
if [ -d "$TARGET_DIR" ]; then
    echo "[오류] 이미 존재하는 디렉터리입니다: ${TARGET_DIR}"
    exit 1
fi

echo "[*] 새 CLI 유틸리티 생성 중: ${CLI_NAME} (모듈명: ${MODULE_NAME})"

# 1. 디렉터리 생성
mkdir -p "${TARGET_DIR}/${MODULE_NAME}"

# 2. pyproject.toml 생성
cat <<EOF > "${TARGET_DIR}/pyproject.toml"
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "${CLI_NAME}"
version = "0.1.0"
description = "CLI tool for ${CLI_NAME}"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
${CLI_NAME} = "${MODULE_NAME}.main:main"
EOF

# 3. __init__.py 생성
cat <<EOF > "${TARGET_DIR}/${MODULE_NAME}/__init__.py"
from .main import main

__all__ = ["main"]
EOF

# 4. main.py 생성 (기본 CLI 템플릿)
cat <<EOF > "${TARGET_DIR}/${MODULE_NAME}/main.py"
import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("${CLI_NAME}")
except PackageNotFoundError:
    __version__ = "0.1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="${CLI_NAME}",
        description="CLI utility for ${CLI_NAME}",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    # 필요한 옵션 및 인자를 여기에 추가하세요
    # parser.add_argument("path", nargs="?", default=".", help="대상 경로")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Hello from ${CLI_NAME}!")


if __name__ == "__main__":
    main()
EOF

# 5. README.md 생성
cat <<EOF > "${TARGET_DIR}/README.md"
# ${CLI_NAME}

CLI utility for ${CLI_NAME}.

## 실행 방법

\`\`\`bash
# 개발 가상환경에서 실행
uv run ${CLI_NAME}

# 전역 설치 상태에서 직접 실행
${CLI_NAME}
\`\`\`
EOF

# 6. 루트 pyproject.toml 워크스페이스 members에 추가
python3 - <<PYEOF
from pathlib import Path
import re

root_toml = Path("${ROOT_TOML}")
content = root_toml.read_text(encoding="utf-8")
cli_name = "${CLI_NAME}"

if f'"{cli_name}"' not in content:
    # members = [ 뒤에 새 멤버 추가
    pattern = r'(members\s*=\s*\[)'
    replacement = r'\1\n    "' + cli_name + '",'
    new_content = re.sub(pattern, replacement, content, count=1)
    root_toml.write_text(new_content, encoding="utf-8")
    print(f"[*] 루트 pyproject.toml 워크스페이스 멤버에 '{cli_name}' 추가 완료")
else:
    print(f"[*] 이미 루트 pyproject.toml 워크스페이스에 '{cli_name}'이 등록되어 있습니다.")
PYEOF

# 7. 워크스페이스 동기화
echo "[*] uv 워크스페이스 동기화 중..."
(cd "${SCRIPT_DIR}" && uv sync)

# 8. 전역 CLI 도구로 editable 설치
echo "[*] 전역 CLI 도구로 설치 (--editable) 중..."
(cd "${SCRIPT_DIR}" && uv tool install --editable "./${CLI_NAME}" --force)

echo ""
echo "========================================================"
echo " 🎉 '${CLI_NAME}' 생성이 완료되었습니다!"
echo "========================================================"
echo " - 소스 위치 : ${TARGET_DIR}/${MODULE_NAME}/main.py"
echo " - 설정 파일 : ${TARGET_DIR}/pyproject.toml"
echo ""
echo " [사용 방법]"
echo "   1) 터미널 어디서든 바로 실행:"
echo "      $ ${CLI_NAME}"
echo ""
echo "   2) 개발 중 가상환경에서 실행:"
echo "      $ uv run ${CLI_NAME}"
echo ""
echo "   3) 의존성 패키지 추가 시:"
echo "      $ uv add <패키지명> --package ${CLI_NAME}"
echo "========================================================"
