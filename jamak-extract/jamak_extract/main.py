#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

__version__ = "0.2.0"

# ISO 639-2 및 주요 언어명을 ISO 639-1 (2글자) 코드로 매핑
LANG_MAP = {
    "kor": "ko", "korean": "ko", "ko": "ko", "kr": "ko",
    "eng": "en", "english": "en", "en": "en",
    "jpn": "ja", "japanese": "ja", "ja": "ja",
    "chi": "zh", "zho": "zh", "chinese": "zh", "zh": "zh",
    "fre": "fr", "fra": "fr", "french": "fr", "fr": "fr",
    "ger": "de", "deu": "de", "german": "de", "de": "de",
    "spa": "es", "spanish": "es", "es": "es",
    "ita": "it", "italian": "it", "it": "it",
    "rus": "ru", "russian": "ru", "ru": "ru",
    "por": "pt", "portuguese": "pt", "pt": "pt",
    "cze": "cs", "ces": "cs", "czech": "cs", "cs": "cs",
    "tha": "th", "thai": "th", "th": "th",
    "vie": "vi", "vietnamese": "vi", "vi": "vi",
    "swe": "sv", "swedish": "sv", "sv": "sv",
    "tur": "tr", "turkish": "tr", "tr": "tr",
    "ukr": "uk", "ukrainian": "uk", "uk": "uk",
    "rum": "ro", "ron": "ro", "romanian": "ro", "ro": "ro",
    "ara": "ar", "arabic": "ar", "ar": "ar",
    "hin": "hi", "hindi": "hi", "hi": "hi",
    "ind": "id", "indonesian": "id", "id": "id",
    "pol": "pl", "polish": "pl", "pl": "pl",
    "dan": "da", "danish": "da", "da": "da",
    "nor": "no", "norwegian": "no", "no": "no",
    "fin": "fi", "finnish": "fi", "fi": "fi",
    "dut": "nl", "nld": "nl", "dutch": "nl", "nl": "nl",
    "gre": "el", "ell": "el", "greek": "el", "el": "el",
    "hun": "hu", "hungarian": "hu", "hu": "hu",
    "heb": "he", "hebrew": "he", "he": "he",
}


def check_ffmpeg_installed() -> None:
    """ffmpeg 및 ffprobe 설치 여부 검사"""
    for cmd in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run(
                [cmd, "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            print(f"오류: '{cmd}' 명령어를 찾을 수 없습니다. 시스템에 ffmpeg가 설치되어 있는지 확인하세요.", file=sys.stderr)
            sys.exit(1)


def get_all_subtitle_streams(video_path: Path) -> list[dict]:
    """ffprobe를 통해 영상 내의 모든 자막 스트림 메타데이터 조회"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "s",
        "-show_entries", "stream=index,codec_name:stream_tags:stream_disposition",
        "-of", "json",
        str(video_path),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        if not streams:
            print(f"오류: '{video_path.name}' 파일 내에 자막 스트림이 없습니다.", file=sys.stderr)
            sys.exit(1)
        return streams
    except subprocess.CalledProcessError as e:
        print(f"ffprobe 실행 실패: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def extract_english_title(stem: str) -> str:
    """비디오 파일명(stem)에서 영어명 부분 추출 (불필요한 앞쪽 한글/특수문자 분리)"""
    # 비ASCII 문자(한글, 한자 등)가 포함되어 있지 않으면 stem 전체가 제목
    if not any(ord(c) > 127 for c in stem):
        return stem

    # 비ASCII 문자열 직후에 등장하는 영문 타이틀 부분 탐색
    m = re.search(r'[\uac00-\ud7a3\u4e00-\u9fff\u3040-\u30ff]+[^\w]*([A-Za-z].*)$', stem)
    if m:
        candidate = m.group(1).strip(" -_.:")
        tech_pattern = r'^(e\d+|ep\d+|s\d+|s\d+e\d+|\d+p|x264|x265|h264|h265|hevc|bluray|web-dl|webrip)\b'
        if not re.match(tech_pattern, candidate, re.IGNORECASE):
            if len(re.findall(r'[A-Za-z]', candidate)) >= 3:
                return candidate

    return stem


def get_language_code(tags: dict) -> str:
    """스트림 메타데이터에서 언어(국적) 코드 추출"""
    lang = tags.get("language", "").strip().lower()
    if lang and lang != "und":
        return LANG_MAP.get(lang, lang)

    # tags에 language가 없거나 und인 경우 title 태그에서 언어명 탐색
    title = tags.get("title", "").strip().lower()
    for key, val in LANG_MAP.items():
        if key in title:
            return val

    return "und"


def get_classification_keywords(stream: dict) -> list[str]:
    """자막 스트림의 disposition 및 title에서 분류 키워드 추출"""
    keywords: list[str] = []
    disposition = stream.get("disposition", {})
    tags = stream.get("tags", {})
    title = tags.get("title", "").strip()
    title_lower = title.lower()

    # 1. 강제 자막 (Forced)
    if disposition.get("forced") == 1 or "forced" in title_lower or "포스" in title:
        keywords.append("forced")

    # 2. 청각장애인용 자막 (SDH / CC)
    if disposition.get("hearing_impaired") == 1 or "sdh" in title_lower or re.search(r'\bcc\b', title_lower):
        keywords.append("sdh")

    # 3. 코멘터리 자막 (Commentary)
    if disposition.get("comment") == 1 or "commentary" in title_lower or "코멘터리" in title or "해설" in title:
        keywords.append("commentary")

    # 4. 중국어 번체 / 간체
    if "traditional" in title_lower or "繁体" in title or "繁體" in title or "cht" in title_lower:
        keywords.append("traditional")
    elif "simplified" in title_lower or "简体" in title or "簡體" in title or "chs" in title_lower:
        keywords.append("simplified")

    # 5. title에 추가 부가 정보가 있는 경우 (예: "British", "Canadian", "Director" 등)
    if title:
        cleaned_title = re.sub(
            r'\b(forced|sdh|cc|commentary|traditional|simplified|korean|english|japanese|chinese|cht|chs|sup|srt|原盘|原盤)\b',
            '',
            title,
            flags=re.IGNORECASE,
        )
        cleaned_title = re.sub(r'[^\w\s-]', '', cleaned_title).strip()
        sub_words = [w for w in re.split(r'[\s_-]+', cleaned_title) if w]
        for w in sub_words:
            w_lower = w.lower()
            if w_lower not in keywords and len(w_lower) > 1 and w_lower not in LANG_MAP:
                keywords.append(w_lower)

    return keywords


def generate_subtitle_filename(
    english_title: str,
    lang_code: str,
    keywords: list[str],
    extension: str,
    used_filenames: set[str],
) -> str:
    """<영어명>-국적-기타분류키워드.srt 형식의 고유 파일명 생성"""
    parts = [english_title, lang_code]
    if keywords:
        parts.extend(keywords)

    base_name = "-".join(parts)
    filename = f"{base_name}{extension}"

    # 중복 파일명 방지 (예: Movie-ko-2.srt)
    if filename in used_filenames:
        idx = 2
        while f"{base_name}-{idx}{extension}" in used_filenames:
            idx += 1
        filename = f"{base_name}-{idx}{extension}"

    used_filenames.add(filename)
    return filename


def _get_codec_args(codec_name: str) -> list[str]:
    """코덱 종류에 따른 ffmpeg 인자 반환"""
    if codec_name == "subrip":
        return ["-c:s", "copy"]
    elif codec_name in ("ass", "ssa", "mov_text", "webvtt", "text"):
        return ["-c:s", "srt"]
    elif codec_name == "hdmv_pgs_subtitle":
        return ["-c:s", "copy"]
    else:
        return ["-c:s", "copy"]


def extract_subtitles_batch(video_path: Path, extraction_targets: list[dict]) -> tuple[int, int]:
    """
    모든 자막을 1회의 ffmpeg 호출(single-pass)로 일괄 추출.
    실패 시 개별 스트림 추출로 fallback.
    반환: (성공 개수, 실패 개수)
    """
    cmd = ["ffmpeg", "-y", "-i", str(video_path)]

    for target in extraction_targets:
        cmd.extend(["-map", f"0:{target['stream_index']}"])
        cmd.extend(_get_codec_args(target["codec_name"]))
        cmd.append(str(target["output_path"]))

    for target in extraction_targets:
        print(f"자막 추출 중: [Stream #{target['stream_index']} ({target['codec_name']})] -> {target['output_path'].name}")

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        for target in extraction_targets:
            print(f"추출 완료: {target['output_path'].resolve()}")
        return len(extraction_targets), 0
    except subprocess.CalledProcessError as e:
        print(f"일괄 추출 실패(개별 추출 시도): {e.stderr.strip()[:200]}", file=sys.stderr)

    # 개별 추출 fallback
    success = 0
    failed = 0
    for target in extraction_targets:
        single_cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-map", f"0:{target['stream_index']}",
            *_get_codec_args(target["codec_name"]),
            str(target["output_path"]),
        ]
        try:
            subprocess.run(single_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            print(f"추출 완료: {target['output_path'].resolve()}")
            success += 1
        except subprocess.CalledProcessError as sub_e:
            print(f"오류: Stream #{target['stream_index']} 추출 실패: {sub_e.stderr.strip()[:200]}", file=sys.stderr)
            failed += 1

    return success, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jamak-extract",
        description="영화 파일(MKV 등)의 모든 자막 트랙을 추출하여 지정 폴더에 저장하는 CLI 유틸리티",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="자막을 추출할 영상 파일 경로 (mkv 등)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="자막을 저장할 출력 폴더 경로 (미지정 시 현재 실행 폴더, 폴더 미존재 시 오류)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="버전 정보 출력",
    )

    args = parser.parse_args()

    check_ffmpeg_installed()

    input_file: Path = args.input
    if not input_file.exists() or not input_file.is_file():
        print(f"오류: 입력 파일 '{input_file}'을(를) 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)

    # 출력 폴더 검증 및 결정
    if args.output is not None:
        output_dir: Path = args.output
        if not output_dir.exists() or not output_dir.is_dir():
            print(f"오류: 출력 폴더 '{output_dir}'이(가) 존재하지 않거나 디렉터리가 아닙니다.", file=sys.stderr)
            sys.exit(1)
    else:
        output_dir = Path.cwd()

    # 모든 자막 스트림 확인
    sub_streams = get_all_subtitle_streams(input_file)
    print(f"'{input_file.name}' 파일에서 자막 스트림 {len(sub_streams)}개를 발견했습니다.")

    english_title = extract_english_title(input_file.stem)
    used_filenames: set[str] = set()
    extraction_targets: list[dict] = []

    for stream in sub_streams:
        stream_index = stream.get("index")
        codec_name = stream.get("codec_name", "unknown")
        tags = stream.get("tags", {})

        lang_code = get_language_code(tags)
        keywords = get_classification_keywords(stream)

        # 이미지 자막(PGS/VobSub)은 srt 변환이 불가능하므로 원본 포맷 확장자로 보존
        if codec_name == "hdmv_pgs_subtitle":
            ext = ".sup"
            print(f"안내: [Stream #{stream_index}] 이미지 기반(PGS) 자막은 SRT 변환이 지원되지 않아 SUP 형식으로 저장합니다.")
        elif codec_name == "dvd_subtitle":
            ext = ".sub"
            print(f"안내: [Stream #{stream_index}] 이미지 기반(VobSub) 자막은 SRT 변환이 지원되지 않아 SUB 형식으로 저장합니다.")
        else:
            ext = ".srt"

        filename = generate_subtitle_filename(
            english_title=english_title,
            lang_code=lang_code,
            keywords=keywords,
            extension=ext,
            used_filenames=used_filenames,
        )

        output_path = output_dir / filename
        extraction_targets.append({
            "stream_index": stream_index,
            "codec_name": codec_name,
            "output_path": output_path,
        })

    success_count, _ = extract_subtitles_batch(input_file, extraction_targets)
    print(f"총 {len(sub_streams)}개 중 {success_count}개 자막 추출 완료 (저장 폴더: {output_dir.resolve()})")


if __name__ == "__main__":
    main()