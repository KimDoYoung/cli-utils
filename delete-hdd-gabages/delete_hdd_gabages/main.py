#!/usr/bin/env python3
"""
delete-hdd-gabages: 지정한 디렉터리 내의 불필요한 파일들을 일괄 정리하는 CLI 도구
"""

import argparse
import fnmatch
from pathlib import Path
import sys

__version__ = "0.1.2"

# 100MB 기준 (100 * 1024 * 1024 바이트)
MAX_RARBG_SIZE_BYTES = 100 * 1024 * 1024

# 단순 확장자 매칭 패턴 목록
SIMPLE_PATTERNS = [
    "*.txt",
    "*.nfo",
    "*.url",
    "*.exe",
]


def format_size(size_bytes: int) -> str:
    """바이트 크기를 읽기 쉬운 단위(B, KB, MB, GB)로 변환합니다."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def is_target_file(path: Path) -> bool:
    """
    주어진 파일이 삭제 대상인지 검사합니다.
    1. 'RARBG'로 시작 + 파일 크기 <= 100MB
    2. *.txt, *.nfo, *.url, *.exe 패턴 일치
    """
    if not path.is_file():
        return False

    name = path.name

    # 1. 'RARBG'로 시작하는 파일 검사 (100MB 이하 조건)
    if name.startswith("RARBG"):
        try:
            if path.stat().st_size <= MAX_RARBG_SIZE_BYTES:
                return True
        except (OSError, PermissionError):
            return False

    # 2. 단순 확장자 패턴 검사 (*.txt, *.nfo, *.url, *.exe)
    for pattern in SIMPLE_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return True

    return False


def collect_targets(base_dir: Path) -> list[Path]:
    """지정 디렉터리 하위를 재귀 순회하여 삭제 대상 파일 목록을 수집합니다."""
    matched_files: list[Path] = []
    try:
        for item in base_dir.rglob("*"):
            try:
                if is_target_file(item):
                    matched_files.append(item)
            except PermissionError:
                print(f"[경고] 권한 부족으로 접근 불가: {item}", file=sys.stderr)
    except PermissionError:
        print(f"[오류] 디렉터리 접근 권한이 없습니다: {base_dir}", file=sys.stderr)
        sys.exit(1)

    return matched_files


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="delete-hdd-gabages",
        description="지정한 디렉터리 하위의 불필요한 파일(RARBG* <= 100MB, *.txt, *.nfo, *.url, *.exe)을 삭제합니다.",
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        type=str,
        help="정리할 대상 디렉터리 경로",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="프로그램 버전을 출력하고 종료합니다.",
    )

    args = parser.parse_args()

    # 인자 유효성 검사
    if not args.target_dir:
        print("[오류] 대상 디렉터리 경로를 인자로 전달해야 합니다.", file=sys.stderr)
        parser.print_usage(file=sys.stderr)
        sys.exit(1)

    base_path = Path(args.target_dir).resolve()

    # 디렉터리 존재 여부 검사
    if not base_path.exists():
        print(f"[오류] 존재하지 않는 경로입니다: {base_path}", file=sys.stderr)
        sys.exit(1)

    if not base_path.is_dir():
        print(f"[오류] 대상 경로가 디렉터리가 아닙니다: {base_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 검색 대상 디렉터리: {base_path}")
    print("[*] 삭제 대상 파일을 검색하는 중...")

    # 대상 파일 수집
    targets = collect_targets(base_path)

    if not targets:
        print("[!] 삭제 대상 파일이 발견되지 않았습니다. 작업을 종료합니다.")
        return

    # 발견된 파일 목록 출력 (용량 정렬 표시)
    print(f"\n[!] 총 {len(targets)}개의 삭제 대상 파일이 발견되었습니다:")
    for path in targets:
        try:
            size_str = format_size(path.stat().st_size)
            print(f"  - [{size_str:>8}] {path}")
        except OSError:
            print(f"  - [--------] {path}")

    # 사용자 확인 (y/N)
    try:
        confirm = input("\n위 파일들을 영구 삭제하시겠습니까? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n[!] 작업이 취소되었습니다.")
        sys.exit(0)

    if confirm != "y":
        print("[!] 사용자에 의해 작업이 취소되었습니다.")
        sys.exit(0)

    # 파일 삭제 실행
    deleted_count = 0
    fail_count = 0

    for path in targets:
        try:
            path.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"[실패] {path}: {e}", file=sys.stderr)
            fail_count += 1

    print(f"\n[완료] {deleted_count}개 삭제 완료, {fail_count}개 실패.")


if __name__ == "__main__":
    main()