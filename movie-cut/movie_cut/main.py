import argparse
import os
import sys
import tkinter as tk
from tkinter import filedialog, font, messagebox
from typing import Optional

from moviepy import VideoFileClip

VERSION = "1.0.0"


def parse_time(value: str) -> float:
    """'00:01:30', '01:30', '90', '000223'(HHMMSS), '0223'(MMSS) -> 초(sec)로 변환."""
    val = value.strip()
    if not val:
        raise ValueError("Time value is empty.")

    # 1. 숫자로만 이루어진 연속 포맷 처리 (예: '000223', '0223', '45')
    if val.isdigit():
        length = len(val)
        if length == 6:  # HHMMSS
            h, m, s = int(val[:2]), int(val[2:4]), int(val[4:])
            return h * 3600 + m * 60 + s
        elif length == 4:  # MMSS
            m, s = int(val[:2]), int(val[2:])
            return m * 60 + s
        elif length <= 2:  # SS
            return float(val)

    # 2. 콜론(:) 구분자 포맷 처리 (예: '01:02:03', '01:30')
    if ":" in val:
        parts = val.split(":")
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            raise ValueError(f"Invalid time format: {value!r}")
        if len(nums) == 2:
            return nums[0] * 60 + nums[1]
        if len(nums) == 3:
            return nums[0] * 3600 + nums[1] * 60 + nums[2]
        raise ValueError(f"Invalid time format: {value!r}")

    # 3. 소수점 포함 초 단위 숫자 (예: '90.5')
    try:
        return float(val)
    except ValueError:
        raise ValueError(f"Invalid time format: {value!r}")


def get_default_output_path(filename: str) -> str:
    """원본 경로와 상관없이 현재 작업 디렉터리(cwd) 기준으로 출력 경로 생성."""
    base_name = os.path.basename(filename)
    stem, ext = os.path.splitext(base_name)
    if not ext:
        ext = ".mp4"
    return os.path.join(os.getcwd(), f"{stem}_cut{ext}")


def cut_movie(filename: str, start: str, end: str, out_path: Optional[str] = None) -> None:
    """파일을 start ~ end 구간으로 잘라 저장."""
    start_sec = parse_time(start)
    end_sec = parse_time(end)

    if end_sec <= start_sec:
        raise ValueError("End time must be greater than start time.")

    if not out_path:
        out_path = get_default_output_path(filename)

    with VideoFileClip(filename) as clip:
        sub = clip.subclipped(start_sec, end_sec)
        sub.write_videofile(out_path, codec="libx264", audio_codec="aac")

    print(f"Saved: {out_path}")


def run_gui() -> None:
    root = tk.Tk()
    root.title("Movie Cutter")
    root.resizable(False, False)

    # 고해상도 스케일링 강제 적용 (DPI 배율)
    root.tk.call("tk", "scaling", 2.0)

    # 기본 폰트 설정
    ui_font = font.Font(family="DejaVu Sans", size=13)
    bold_font = font.Font(family="DejaVu Sans", size=13, weight="bold")
    root.option_add("*Font", ui_font)

    pad_opts = {"padx": 16, "pady": 12}

    # 파일 선택 행
    tk.Label(root, text="File:").grid(row=0, column=0, sticky="e", **pad_opts)
    file_entry = tk.Entry(root, width=36)
    file_entry.grid(row=0, column=1, **pad_opts)

    def browse():
        path = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[
                ("Video Files", "*.mp4 *.mov *.mkv *.avi *.webm"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, path)

    tk.Button(root, text="Browse...", width=10, command=browse).grid(
        row=0, column=2, **pad_opts
    )

    # Start Time 행
    tk.Label(root, text="Start:").grid(row=1, column=0, sticky="e", **pad_opts)
    start_entry = tk.Entry(root, width=16)
    start_entry.grid(row=1, column=1, sticky="w", **pad_opts)
    start_entry.insert(0, "000000")

    # End Time 행
    tk.Label(root, text="End:").grid(row=2, column=0, sticky="e", **pad_opts)
    end_entry = tk.Entry(root, width=16)
    end_entry.grid(row=2, column=1, sticky="w", **pad_opts)

    def on_confirm():
        filename = file_entry.get().strip()
        start = start_entry.get().strip()
        end = end_entry.get().strip()

        if not filename:
            messagebox.showwarning("Warning", "Please select a video file.")
            return
        if not start or not end:
            messagebox.showwarning("Warning", "Please specify start and end times.")
            return

        try:
            root.config(cursor="watch")
            root.update()
            cut_movie(filename, start, end)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        finally:
            root.config(cursor="")

        messagebox.showinfo("Done", "Video trimming completed.")
        root.destroy()

    # 하단 버튼 행
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=3, column=0, columnspan=3, pady=(16, 24))

    tk.Button(btn_frame, text="OK", width=12, font=bold_font, command=on_confirm).pack(
        side="left", padx=12
    )
    tk.Button(btn_frame, text="Cancel", width=12, font=bold_font, command=root.destroy).pack(
        side="left", padx=12
    )

    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="movie_cutter",
        description="Video trimming tool supporting both CLI and GUI.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    parser.add_argument(
        "--gui", action="store_true", help="Launch the GUI interface."
    )
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        default=None,
        help="Output file path (e.g. /tmp/1.mp4). Defaults to current working directory.",
    )
    parser.add_argument("filename", nargs="?", help="Input video file path.")
    parser.add_argument(
        "start",
        nargs="?",
        help="Start time (e.g., 000130, 00:01:30, or seconds).",
    )
    parser.add_argument(
        "end",
        nargs="?",
        help="End time (e.g., 000223, 00:02:23, or seconds).",
    )

    args = parser.parse_args()

    if args.gui:
        run_gui()
        return

    if args.filename and args.start and args.end:
        try:
            cut_movie(args.filename, args.start, args.end, out_path=args.out)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()