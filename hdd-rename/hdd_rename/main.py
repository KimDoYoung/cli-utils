import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("hdd-rename")
except PackageNotFoundError:
    __version__ = "0.1.0"

# 지원할 확장자 정의
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".wmv", ".mov", ".flv", ".ts"}
SUBTITLE_EXTENSIONS = {".smi", ".srt", ".vtt", ".ass", ".ssa"}


def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("hdd_rename")
    logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 파일 핸들러
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # 콘솔 출력 핸들러
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def process_directory(target_dir: Path, logger: logging.Logger) -> None:
    if not target_dir.exists() or not target_dir.is_dir():
        logger.error(f"지정한 경로가 유효한 디렉터리가 아닙니다: {target_dir}")
        return

    logger.info(f"스캔 시작: {target_dir}")

    # 하위 디렉터리 순회
    for folder in [target_dir] + [p for p in target_dir.rglob("*") if p.is_dir()]:
        # 현재 폴더 내 파일만 필터링
        files = [f for f in folder.iterdir() if f.is_file()]

        video_files = [f for f in files if f.suffix.lower() in VIDEO_EXTENSIONS]
        subtitle_files = [f for f in files if f.suffix.lower() in SUBTITLE_EXTENSIONS]

        # 조건 1 & 2 검사:
        # - 동영상 파일은 정확히 1개여야 함
        # - 자막 파일은 1개 또는 2개여야 함
        # - 자막 파일이 2개일 경우 서로 다른 확장자여야 함
        if len(video_files) != 1:
            if len(video_files) > 1:
                logger.info(
                    f"[SKIP] 동영상 파일이 여러 개 존재합니다 ({len(video_files)}개): {folder}"
                )
            continue

        if len(subtitle_files) not in (1, 2):
            continue

        # 자막이 2개일 때 확장자가 중복되는지 확인 (예: .srt가 2개인 경우 skip)
        sub_exts = [sub.suffix.lower() for sub in subtitle_files]
        if len(sub_exts) != len(set(sub_exts)):
            logger.info(
                f"[SKIP] 동일한 확장자의 자막 파일이 2개 이상 있습니다: {folder}"
            )
            continue

        target_video = video_files[0]
        base_name = target_video.stem

        # 자막 파일 이름 변경 처리
        for sub in subtitle_files:
            new_sub_name = f"{base_name}{sub.suffix}"
            target_path = folder / new_sub_name

            if sub.name == new_sub_name:
                continue

            if target_path.exists():
                logger.warning(
                    f"[SKIP] 대상 파일명이 이미 존재합니다: {target_path.name} in {folder}"
                )
                continue

            try:
                sub.rename(target_path)
                logger.info(f"[RENAME] {sub.name} -> {new_sub_name} (폴더: {folder})")
            except OSError as e:
                logger.error(
                    f"[ERROR] 이름 변경 실패: {sub.name} -> {new_sub_name} (사유: {e})"
                )

    logger.info("모든 작업이 완료되었습니다.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hdd-rename",
        description="동영상 1개와 자막 1~2개가 있는 폴더의 자막 파일명을 동영상명과 일치시킵니다.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "mount_point",
        nargs="?",
        type=str,
        help="HDD 마운트 경로",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="out.log",
        help="로그 파일 경로 (미지정 시 현재 작업 디렉터리의 out.log)",
    )

    args = parser.parse_args()
    if not args.mount_point:
        parser.print_help()
        sys.exit(1)

    return args


def main() -> None:
    args = parse_args()

    mount_dir = Path(args.mount_point).resolve()
    log_file = Path(args.log).resolve()

    logger = setup_logger(log_file)
    process_directory(mount_dir, logger)


if __name__ == "__main__":
    main()