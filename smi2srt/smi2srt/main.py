import html
import re
import sys
from pathlib import Path


def ms_to_srt_time(ms: int) -> str:
    """밀리초(ms)를 SRT 타임코드 포맷(HH:MM:SS,mmm)으로 변환"""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def clean_text(raw_html: str) -> str:
    """HTML 태그 정리 및 개행/엔티티 처리"""
    # <br> 태그를 줄바꿈으로 변환
    text = re.sub(r"(?i)<br\s*/?>", "\n", raw_html)
    # 나머지 HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", text)
    # HTML 특수문자 디코딩 (&nbsp;, &lt;, &gt; 등)
    text = html.unescape(text)
    # 양끝 공백 정리
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def read_smi_file(filepath: Path) -> str:
    """인코딩 감지 및 파일 읽기 (UTF-8, CP949, EUC-KR 순서로 시도)"""
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]
    raw_bytes = filepath.read_bytes()

    for enc in encodings:
        try:
            return raw_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    raise UnicodeDecodeError(
        "지원되는 인코딩(UTF-8, CP949 등)으로 파일을 읽을 수 없습니다."
    )


def smi_to_srt(smi_path: str, srt_path: str = None) -> str:
    input_file = Path(smi_path)
    if not input_file.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {smi_path}")

    if srt_path is None:
        output_file = input_file.with_suffix(".srt")
    else:
        output_file = Path(srt_path)

    content = read_smi_file(input_file)

    # <SYNC Start=숫자> 패턴 매칭
    sync_pattern = re.compile(
        r"<SYNC\s+Start\s*=\s*([0-9]+)[^>]*>(.*?)(?=(?:<SYNC|\Z))",
        re.IGNORECASE | re.DOTALL,
    )

    matches = sync_pattern.findall(content)
    if not matches:
        raise ValueError("SMI 파일 내에서 <SYNC> 태그를 찾지 못했습니다.")

    subtitles = []
    for idx, (start_ms_str, raw_text) in enumerate(matches):
        start_ms = int(start_ms_str)
        text = clean_text(raw_text)

        # 다음 자막의 시작 시간을 종료 시간으로 설정
        if idx + 1 < len(matches):
            end_ms = int(matches[idx + 1][0])
        else:
            # 마지막 자막은 기본 3초 표시
            end_ms = start_ms + 3000

        # 자막 종료용 빈 태그(&nbsp; 등)이거나 텍스트가 없으면 건너뜀
        if not text:
            continue

        # 종료 시간이 시작 시간보다 앞서거나 같으면 보정 (최소 1초 노출)
        if end_ms <= start_ms:
            end_ms = start_ms + 1000

        subtitles.append((start_ms, end_ms, text))

    # SRT 형식으로 작성
    srt_lines = []
    for counter, (start, end, text) in enumerate(subtitles, start=1):
        srt_lines.append(str(counter))
        srt_lines.append(f"{ms_to_srt_time(start)} --> {ms_to_srt_time(end)}")
        srt_lines.append(text)
        srt_lines.append("")  # 자막 간 빈 줄 구분

    output_file.write_text("\n".join(srt_lines), encoding="utf-8")
    return str(output_file)


def main() -> None:
    if len(sys.argv) > 1:
        target = sys.argv[1]
        try:
            out = smi_to_srt(target)
            print(f"변환 완료: {out}")
        except Exception as e:
            print(f"오류: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("사용법: smi2srt <자막파일.smi>")
        sys.exit(1)

if __name__ == "__main__":
    main()