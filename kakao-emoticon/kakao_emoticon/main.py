import argparse
import random
import shutil
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

try:
    __version__ = version("kakao-emoticon")
except PackageNotFoundError:
    __version__ = "0.1.0"


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        print("[Error] 시스템에 'ffmpeg'가 설치되어 있지 않습니다.", file=sys.stderr)
        print("        GIF 변환을 사용하려면 ffmpeg를 먼저 설치해주세요.", file=sys.stderr)
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="kakao-emoticon",
        description="카카오 이모티콘을 스크래핑하고, 필요 시 GIF 변환 및 이름 변경용 index.html을 생성합니다.",
        add_help=True,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="카카오 이모티콘 상세 페이지 URL (예: https://e.kakao.com/t/...)",
    )
    parser.add_argument(
        "--gif",
        action="store_true",
        help="다운로드한 원본 이미지를 무한 반복 GIF 파일로 변환합니다. (ffmpeg 필요)",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="다운로드/변환된 파일들을 웹에서 확인하고 이름 변경 쉘 명령어를 생성하는 index.html을 만듭니다.",
    )

    args = parser.parse_args()
    if not args.url:
        parser.print_help()
        sys.exit(1)

    return args


def fetch_image_urls(target_url: str) -> list[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://e.kakao.com/",
    }

    print(f"[*] 페이지 분석 중: {target_url}")
    with httpx.Client(headers=headers, follow_redirects=True, timeout=15.0) as client:
        response = client.get(target_url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    section = soup.find("section", attrs={"aria-label": "상세 이모티콘"})
    if not section:
        print("[Error] '<section aria-label=\"상세 이모티콘\">' 영역을 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)

    image_urls = []
    for li in section.select("ul > li"):
        anim_url = (
            li.get("data-animated-src")
            or li.get("data-src")
            or li.get("data-motion-url")
        )

        img = li.find("img")
        if not anim_url and img:
            anim_url = (
                img.get("data-animated-src")
                or img.get("data-original")
                or img.get("data-src")
                or img.get("src")
            )

        if anim_url:
            image_urls.append(urljoin(target_url, anim_url))

    return image_urls


def convert_to_gif(input_path: Path, output_path: Path) -> bool:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop",
        "0",
        str(output_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0


def generate_index_html(target_files: list[Path], output_path: Path) -> None:
    items_html = []
    for f in target_files:
        filename = f.name
        stem = f.stem
        ext = f.suffix
        items_html.append(f"""
        <div class="bg-white border rounded-lg p-3 shadow-sm flex flex-col items-center">
            <div class="w-full aspect-square flex items-center justify-center bg-gray-50 rounded overflow-hidden mb-2">
                <img src="./{filename}" alt="{filename}" class="max-w-full max-h-full object-contain">
            </div>
            <span class="text-xs text-gray-400 mb-2 truncate w-full text-center" title="{filename}">{filename}</span>
            <input type="text" 
                   data-src="./{filename}" 
                   data-ext="{ext}" 
                   placeholder="새 파일명 (확장자 제외)" 
                   class="name-input w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>
        """)

    cards_string = "\n".join(items_html)

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>카카오 이모티콘 이름 변경기</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- jQuery CDN -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
</head>
<body class="bg-gray-100 min-h-screen text-gray-800">
    <div id="content" class="max-w-7xl mx-auto p-6">
        <header class="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
                <h1 class="text-2xl font-bold text-gray-900">카카오 이모티콘 스티커 이름 정리</h1>
                <p class="text-sm text-gray-500 mt-1">원하는 이미지 아래에 새 이름을 입력한 후 아래 버튼을 눌러 터미널 명령어를 복사하세요.</p>
            </div>
            <div class="text-sm bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg border border-blue-200">
                총 {len(target_files)}개 이미지 로드됨
            </div>
        </header>

        <!-- 1행 5개 그리드 나열 (모바일은 반응형 조정) -->
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
            {cards_string}
        </div>

        <!-- 하단 액션 컨트롤 영역 -->
        <div class="bg-white border rounded-xl p-6 shadow-md mb-8">
            <div class="flex flex-wrap items-center gap-3">
                <button id="btn-generate" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-lg transition-colors shadow-sm">
                    이름 바꾸어 복사 명령어 생성
                </button>
                <button id="btn-copy" class="hidden bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-5 py-2.5 rounded-lg transition-colors shadow-sm">
                    클립보드 복사
                </button>
                <span id="copy-msg" class="hidden text-sm text-emerald-600 font-semibold">복사되었습니다!</span>
            </div>

            <!-- 숨겨진 명령어 출력 영역 -->
            <div id="output-area" class="mt-4 hidden">
                <label for="cmd-result" class="block text-xs font-semibold text-gray-500 mb-1">터미널 실행 명령어 (Bash/Fish)</label>
                <textarea id="cmd-result" rows="8" readonly class="w-full font-mono text-sm bg-gray-900 text-green-400 p-3 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
            </div>
        </div>
    </div>

    <script>
        $(document).ready(function() {{$("#btn-generate").on("click", function() {{
                const commands = [];

                $(".name-input").each(function() {{
                    const newName = $(this).val().trim();
                    if (newName !== "") {{
                        const srcPath = $(this).data("src");
                        const ext = $(this).data("ext");
                        // mv ./original_01.webp "./새이름.webp"
                        commands.push(`cp "${{srcPath}}" "./${{newName}}${{ext}}"`);
                    }}
                }});

                if (commands.length === 0) {{
                    alert("이름을 입력한 항목이 없습니다. 적어도 하나의 입력창에 새 이름을 적어주세요.");
                    $("#output-area").addClass("hidden");
                    $("#btn-copy").addClass("hidden");
                    return;
                }}

                $("#cmd-result").val(commands.join("\\n"));
                $("#output-area").removeClass("hidden");
                $("#btn-copy").removeClass("hidden");

                // 명령어 텍스트 영역으로 스크롤 이동
                $('html, body').animate({{
                    scrollTop: $("#output-area").offset().top - 100
                }}, 300);
            }});

            $("#btn-copy").on("click", function() {{
                const text = $("#cmd-result").val();
                if (!text) return;

                navigator.clipboard.writeText(text).then(function() {{
                    $("#copy-msg").removeClass("hidden").fadeIn(100).delay(1500).fadeOut(400);
                }}).catch(function(err) {{
                    alert("클립보드 복사에 실패했습니다. 수동으로 복사해주세요.");
                }});
            }});
        }});
    </script>
</body>
</html>
"""
    output_path.write_text(html_content, encoding="utf-8")
    print(f"[*] 'index.html' 파일이 생성되었습니다: {output_path.resolve()}")


def main() -> None:
    args = parse_args()

    if args.gif:
        check_ffmpeg()

    try:
        urls = fetch_image_urls(args.url)
    except Exception as e:
        print(f"[Error] 스크래핑 실패: {e}", file=sys.stderr)
        sys.exit(1)

    total = len(urls)
    if total == 0:
        print("[!] 대상 이모티콘 이미지를 발견하지 못했습니다.")
        return

    mode_msg = "다운로드 및 GIF 변환" if args.gif else "원본 다운로드"
    print(f"[*] 총 {total}개의 이모티콘 대상을 발견했습니다. ({mode_msg} 시작)")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://e.kakao.com/",
    }

    current_dir = Path.cwd()
    saved_files: list[Path] = []

    with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
        for idx, img_url in enumerate(urls, start=1):
            clean_url = img_url.split("?")[0]
            ext = clean_url.split(".")[-1].lower() if "." in clean_url else "webp"
            if ext not in ["webp", "png", "gif"]:
                ext = "webp"

            orig_file = current_dir / f"original_{idx:02d}.{ext}"

            print(f"[{idx}/{total}] 다운로드 중: {img_url}")
            try:
                img_res = client.get(img_url)
                img_res.raise_for_status()
                orig_file.write_bytes(img_res.content)
                print(f"       -> 원본 저장: {orig_file.name}")

                if args.gif:
                    gif_file = current_dir / f"emoticon_{idx:02d}.gif"
                    if convert_to_gif(orig_file, gif_file):
                        print(f"       -> GIF 변환: {gif_file.name}")
                        saved_files.append(gif_file)
                    else:
                        print(f"       -> [경고] GIF 변환 실패 ({orig_file.name})", file=sys.stderr)
                else:
                    saved_files.append(orig_file)

            except Exception as e:
                print(f"       -> [Error] 처리 실패: {e}", file=sys.stderr)

            # 마지막 이미지가 아닐 때 random wait
            if idx < total:
                sleep_sec = random.uniform(1.0, 10.0)
                print(f"[*] 대기 중: {sleep_sec:.2f}초...")
                time.sleep(sleep_sec)

    # --index 옵션 처리
    if args.index:
        index_file = current_dir / "index.html"
        generate_index_html(saved_files, index_file)

    print("[*] 모든 작업이 완료되었습니다.")


if __name__ == "__main__":
    main()