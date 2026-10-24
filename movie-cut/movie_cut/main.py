import sys
import tkinter as tk
from tkinter import filedialog, font, messagebox

from moviepy import VideoFileClip


def cut_movie(filename: str, start: str, end: str) -> None:
    """파일을 start ~ end 구간으로 잘라 저장."""
    start_sec = parse_time(start)
    end_sec = parse_time(end)

    if end_sec <= start_sec:
        raise ValueError("End time must be greater than start time.")

    base, dot, ext = filename.rpartition(".")
    if not dot:
        base, ext = filename, "mp4"
    out_path = f"{base}_cut.{ext}"

    with VideoFileClip(filename) as clip:
        sub = clip.subclipped(start_sec, end_sec)
        sub.write_videofile(out_path, codec="libx264", audio_codec="aac")

    print(f"Saved: {out_path}")


def parse_time(value: str) -> float:
    """'00:01:30', '01:30', '90' -> 초(sec)로 변환."""
    value = value.strip()
    if not value:
        raise ValueError("Time value is empty.")
    parts = value.split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        raise ValueError(f"Invalid time format: {value!r}")
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        m, s = nums
        return m * 60 + s
    if len(nums) == 3:
        h, m, s = nums
        return h * 3600 + m * 60 + s
    raise ValueError(f"Invalid time format: {value!r}")


def run_gui() -> None:
    root = tk.Tk()
    root.title("Movie Cutter")
    root.resizable(False, False)

    # 1. 고해상도 스케일링 강제 적용 (DPI 배율)
    # 1.5 ~ 2.0 사이로 설정하면 컴포넌트와 텍스트가 시원시원하게 커집니다.
    root.tk.call("tk", "scaling", 2.0)

    # 2. 넉넉한 글꼴 크기 지정 (size=13 ~ 14)
    ui_font = font.Font(family="DejaVu Sans", size=13)
    bold_font = font.Font(family="DejaVu Sans", size=13, weight="bold")

    # 전체 위젯 기본 폰트 적용
    root.option_add("*Font", ui_font)

    # 3. 내부 여백(패딩)을 시원하게 확장
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
    start_entry.insert(0, "00:00:00")

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

    # 하단 버튼 행 (버튼 높이/패딩 확장)
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=3, column=0, columnspan=3, pady=(16, 24))

    tk.Button(btn_frame, text="OK", width=12, font=bold_font, command=on_confirm).pack(
        side="left", padx=12
    )
    tk.Button(btn_frame, text="Cancel", width=12, font=bold_font, command=root.destroy).pack(
        side="left", padx=12
    )

    root.mainloop()

def print_usage() -> None:
    print("Usage:")
    print("  GUI : python script.py --gui")
    print("  CLI : python script.py <filename> <start> <end>")


def main() -> None:
    args = sys.argv[1:]

    if "--gui" in args:
        run_gui()
        return

    if len(args) >= 3:
        cut_movie(args[0], args[1], args[2])
        return

    print_usage()
    sys.exit(1)


if __name__ == "__main__":
    main()