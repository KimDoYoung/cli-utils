import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from moviepy import VideoFileClip


def cut_movie(filename: str, start: str, end: str) -> None:
    """파일을 start ~ end 구간으로 잘라 저장."""
    start_sec = parse_time(start)
    end_sec = parse_time(end)

    if end_sec <= start_sec:
        raise ValueError("종료 시간은 시작 시간보다 커야 합니다.")

    base, dot, ext = filename.rpartition(".")
    if not dot:
        base, ext = filename, "mp4"
    out_path = f"{base}_cut.{ext}"

    with VideoFileClip(filename) as clip:
        sub = clip.subclipped(start_sec, end_sec)
        sub.write_videofile(out_path, codec="libx264", audio_codec="aac")

    print(f"저장 완료: {out_path}")


def parse_time(value: str) -> float:
    """'00:01:30', '01:30', '90' 형식을 모두 초로 변환."""
    value = value.strip()
    if not value:
        raise ValueError("시간이 비어 있습니다.")
    parts = value.split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        raise ValueError(f"시간 형식이 잘못되었습니다: {value!r}")
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        m, s = nums
        return m * 60 + s
    if len(nums) == 3:
        h, m, s = nums
        return h * 3600 + m * 60 + s
    raise ValueError(f"시간 형식이 잘못되었습니다: {value!r}")


def run_gui() -> None:
    root = tk.Tk()
    root.title("movie-cut")
    root.resizable(False, False)

    tk.Label(root, text="파일").grid(row=0, column=0, sticky="e", padx=6, pady=4)
    file_entry = tk.Entry(root, width=40)
    file_entry.grid(row=0, column=1, padx=6, pady=4)

    def browse():
        path = filedialog.askopenfilename(
            title="동영상 선택",
            filetypes=[
                ("동영상", "*.mp4 *.mov *.mkv *.avi *.webm"),
                ("모든 파일", "*.*"),
            ],
        )
        if path:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, path)

    tk.Button(root, text="찾아보기", command=browse).grid(row=0, column=2, padx=6, pady=4)

    tk.Label(root, text="시작 시간").grid(row=1, column=0, sticky="e", padx=6, pady=4)
    start_entry = tk.Entry(root, width=20)
    start_entry.grid(row=1, column=1, sticky="w", padx=6, pady=4)

    tk.Label(root, text="종료 시간").grid(row=2, column=0, sticky="e", padx=6, pady=4)
    end_entry = tk.Entry(root, width=20)
    end_entry.grid(row=2, column=1, sticky="w", padx=6, pady=4)

    def on_confirm():
        filename = file_entry.get().strip()
        start = start_entry.get().strip()
        end = end_entry.get().strip()

        if not filename:
            messagebox.showwarning("입력 오류", "파일을 선택하세요.")
            return
        if not start or not end:
            messagebox.showwarning("입력 오류", "시작/종료 시간을 입력하세요.")
            return

        try:
            cut_movie(filename, start, end)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return

        messagebox.showinfo("완료", "자르기가 완료되었습니다.")
        root.destroy()

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=3, column=0, columnspan=3, pady=8)
    tk.Button(btn_frame, text="확인", width=10, command=on_confirm).pack(side="left", padx=4)
    tk.Button(btn_frame, text="취소", width=10, command=root.destroy).pack(side="left", padx=4)

    root.mainloop()


def print_usage() -> None:
    print("사용법:")
    print("  movie-cut <파일명> <시작시간> <종료시간>")
    print("  movie-cut --gui")
    print()
    print("예시:")
    print("  movie-cut input.mp4 00:00:10 00:01:30")
    print("  movie-cut --gui")


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