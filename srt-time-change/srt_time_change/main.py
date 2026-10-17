import argparse
import re
import sys
from pathlib import Path


def parse_time_input(time_str: str) -> int:
    """다양한 시간 형식(MMSS, HHMMSS, MM:SS, HH:MM:SS, 초 단위 등)을 ms로 변환"""
    s = time_str.strip().replace(",", ".")

    # 1. '0327' (4자리: MMSS) -> 3분 27초
    if re.fullmatch(r"\d{4}", s):
        mm, ss = int(s[:2]), int(s[2:])
        return (mm * 60 + ss) * 1000

    # 2. '010327' (6자리: HHMMSS) -> 1시간 3분 27초
    if re.fullmatch(r"\d{6}", s):
        hh, mm, ss = int(s[:2]), int(s[2:4]), int(s[4:])
        return (hh * 3600 + mm * 60 + ss) * 1000

    # 3. 'MM:SS' 또는 'HH:MM:SS' (밀리초 포함 가능)
    parts = s.split(":")
    if len(parts) in (2, 3):
        if len(parts) == 2:
            hh = 0
            mm, sec_part = int(parts[0]), float(parts[1])
        else:
            hh, mm, sec_part = int(parts[0]), int(parts[1]), float(parts[2])
        return int((hh * 3600 + mm * 60 + sec_part) * 1000)

    # 4. 순수 숫자(초 단위 float)
    try:
        return int(float(s) * 1000)
    except ValueError:
        raise ValueError(
            f"지원하지 않는 시간 포맷입니다: '{time_str}'. (예: 0327, 03:27, 01:03:27)"
        )


def srt_time_to_ms(tc: str) -> int:
    """SRT 타임코드(HH:MM:SS,mmm) -> ms"""
    hh, mm, sec_milli = tc.strip().split(":")
    ss, ms = sec_milli.replace(".", ",").split(",")
    return (int(hh) * 3600 + int(mm) * 60 + int(ss)) * 1000 + int(ms)


def ms_to_srt_time(ms: int) -> str:
    """ms -> SRT 타임코드(HH:MM:SS,mmm)"""
    ms = max(0, ms)  # 00:00:00 이전으로 내려가지 않도록 클램핑
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def process_srt(input_path: Path, output_path: Path, from_time_str: str, to_time_str: str) -> None:
    from_ms = parse_time_input(from_time_str)
    to_ms = parse_time_input(to_time_str)
    diff_ms = to_ms - from_ms

    # SRT 인코딩 자동 폴백
    raw_bytes = input_path.read_bytes()
    content = None
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            content = raw_bytes.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if content is None:
        raise UnicodeDecodeError("지원되는 인코딩(UTF-8, CP949 등)으로 읽을 수 없습니다.")

    # 00:03:27,000 --> 00:03:30,000 타임라인 패턴 매칭
    time_line_regex = re.compile(
        r"^(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})$"
    )

    new_lines = []
    modified_count = 0

    for line in content.splitlines():
        match = time_line_regex.match(line.strip())
        if match:
            start_ms = srt_time_to_ms(match.group(1))
            end_ms = srt_time_to_ms(match.group(2))

            # 지정한 기준 시작 시점(from_ms) 이상인 경우 시간 이동
            if start_ms >= from_ms:
                start_ms = max(0, start_ms + diff_ms)
                end_ms = max(0, end_ms + diff_ms)
                modified_count += 1

            new_lines.append(f"{ms_to_srt_time(start_ms)} --> {ms_to_srt_time(end_ms)}")
        else:
            new_lines.append(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    diff_sec = diff_ms / 1000.0
    sign = "+" if diff_sec >= 0 else ""
    print(f"기준 시점: {ms_to_srt_time(from_ms)} 이후 자막 대상")
    print(f"시간 조정: {sign}{diff_sec:.3f}초 ({modified_count}개 자막 구간 수정)")
    print(f"저장 완료: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SRT 자막의 특정 시점 이후 타임코드를 오프셋만큼 일괄 조정합니다."
    )
    parser.add_argument("srt_file", type=str, help="입력 SRT 파일 경로")
    parser.add_argument("from_time", type=str, help="기준 시작 시점 (예: 0327, 03:27)")
    parser.add_argument("to_time", type=str, help="변경 목표 시점 (예: 0355, 03:55)")
    parser.add_argument("-o", "--output", type=str, help="출력 SRT 파일 경로 (미지정 시 <이름>-settime.srt)")

    args = parser.parse_args()

    input_path = Path(args.srt_file)
    if not input_path.is_file():
        print(f"오류: 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(f"{input_path.stem}-settime{input_path.suffix}")

    try:
        process_srt(input_path, output_path, args.from_time, args.to_time)
    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()