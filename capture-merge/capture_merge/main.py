#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pillow>=10.0.0",
# ]
# ///
"""capture-merge: 여러 캡처 이미지를 하나의 이미지로 병합하는 CLI 도구.

Usage:
    uv run main.py "*Snake*"
    uv run main.py "*Snake*" --width=1600 --columns-per-row=3 --out=merged.png
"""

import argparse
import glob
import os
import sys

from PIL import Image

__version__ = "1.0.0"

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="capture-merge",
        description="여러 캡처 이미지를 하나의 이미지로 병합합니다.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "pattern",
        nargs="+",                      # ← 여러 인자 허용
        help="입력 파일 패턴 또는 파일 목록 (예: '*Snake*')",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="결과 이미지의 너비 (500-2800)",
    )
    parser.add_argument(
        "--columns-per-row",
        type=int,
        default=2,
        help="한 행에 배치할 이미지 수",
    )
    parser.add_argument(
        "--x-gap",
        type=int,
        default=5,
        help="이미지 간 x축 간격",
    )
    parser.add_argument(
        "--y-gap",
        type=int,
        default=5,
        help="이미지 간 y축 간격",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="출력 파일명 (미지정 시 capture-merged-N.png 자동 생성)",
    )

    args = parser.parse_args(argv)

    if not (500 <= args.width <= 2800):
        parser.error(f"--width 는 500-2800 사이여야 합니다. (입력값: {args.width})")
    if args.columns_per_row < 1:
        parser.error("--columns-per-row 는 1 이상이어야 합니다.")
    if args.x_gap < 0 or args.y_gap < 0:
        parser.error("--x-gap, --y-gap 은 0 이상이어야 합니다.")

    return args


def collect_files(patterns):
    """패턴/파일 목록을 받아 존재하는 이미지 파일 리스트로 변환(정렬, 중복 제거)."""
    files = []
    for p in patterns:
        if os.path.isfile(p):           # 셸이 이미 확장해 넘겨준 실제 파일
            if p.lower().endswith(VALID_EXTENSIONS):
                files.append(p)
        else:                            # glob 패턴으로 직접 처리
            files.extend(
                f for f in glob.glob(p)
                if os.path.isfile(f) and f.lower().endswith(VALID_EXTENSIONS)
            )
    # 중복 제거 + 정렬
    return sorted(set(files))


def determine_output_path(out):
    """출력 경로를 결정. out 미지정 시 capture-merged-N.png 자동 번호 부여."""
    if out:
        if not out.lower().endswith(".png"):
            out = out + ".png"
        return out

    n = 1
    while True:
        candidate = f"capture-merged-{n}.png"
        if not os.path.exists(candidate):
            return candidate
        n += 1


def compute_cell_size(target_width, columns, x_gap):
    """각 이미지의 목표 너비를 계산."""
    total_gap = x_gap * (columns - 1)
    cell_width = (target_width - total_gap) // columns
    if cell_width <= 0:
        raise ValueError(
            f"옵션 조합으로 이미지 너비가 0 이하입니다. (width={target_width}, "
            f"columns={columns}, x_gap={x_gap})"
        )
    return cell_width


def fit_image(img, cell_width):
    """비율을 유지하며 cell_width 에 맞춰 축소 (확대는 하지 않음)."""
    orig_w, orig_h = img.size
    if orig_w <= cell_width:
        return img
    ratio = cell_width / orig_w
    new_h = max(1, int(round(orig_h * ratio)))
    return img.resize((cell_width, new_h), Image.LANCZOS)


def merge_images(files, target_width, columns, x_gap, y_gap, out_path):
    cell_width = compute_cell_size(target_width, columns, x_gap)

    resized = []
    for f in files:
        try:
            with Image.open(f) as im:
                im = im.convert("RGBA")
                resized.append((f, fit_image(im, cell_width)))
        except Exception as e:
            print(f"[warn] '{f}' 로드 실패: {e}", file=sys.stderr)

    if not resized:
        raise RuntimeError("처리할 이미지가 없습니다.")

    rows = [resized[i:i + columns] for i in range(0, len(resized), columns)]
    row_heights = [max(img.size[1] for _, img in row) for row in rows]
    total_height = sum(row_heights) + y_gap * (len(rows) - 1)

    canvas = Image.new("RGBA", (target_width, total_height), (255, 255, 255, 255))

    y = 0
    for row, row_h in zip(rows, row_heights):
        row_width_used = sum(img.size[0] for _, img in row) + x_gap * (len(row) - 1)
        x = (target_width - row_width_used) // 2

        for _, img in row:
            canvas.paste(img, (x, y), img)
            x += img.size[0] + x_gap
        y += row_h + y_gap

    final = Image.new("RGB", canvas.size, (255, 255, 255))
    final.paste(canvas, (0, 0), canvas)
    final.save(out_path, "PNG")
    return out_path, final.size, len(resized)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    files = collect_files(args.pattern)   # args.pattern 은 이제 리스트
    if not files:
        print(f"[error] '{args.pattern}' 에 해당하는 이미지 파일이 없습니다.", file=sys.stderr)
        return 1

    out_path = determine_output_path(args.out)

    try:
        saved, size, count = merge_images(
            files,
            target_width=args.width,
            columns=args.columns_per_row,
            x_gap=args.x_gap,
            y_gap=args.y_gap,
            out_path=out_path,
        )
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1

    print(f"완료: {count}장 병합 → {saved} ({size[0]}x{size[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())