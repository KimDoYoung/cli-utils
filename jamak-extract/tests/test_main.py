import pytest
import sys
from pathlib import Path
from jamak_extract.main import (
    extract_english_title,
    get_language_code,
    get_classification_keywords,
    generate_subtitle_filename,
    main,
)


def test_extract_english_title():
    # 1. 영문 파일명
    assert extract_english_title("Escape.From.Mogadishu.2021.BluRay") == "Escape.From.Mogadishu.2021.BluRay"
    assert extract_english_title("Mondo.Cane.1962.(Documentary-Horror)") == "Mondo.Cane.1962.(Documentary-Horror)"

    # 2. 한글 + 영문 타이틀 혼합
    assert extract_english_title("미스 마치 Miss.March.2009.1080p.BluRay.x265-RARBG") == "Miss.March.2009.1080p.BluRay.x265-RARBG"
    assert extract_english_title("만개한 벚나무 숲 아래：크라이테리언 Under.the.Blossoming.Cherry.Trees.1975") == "Under.the.Blossoming.Cherry.Trees.1975"
    assert extract_english_title("리허설 Rehearsal.(1995).1080p.H264.AAC") == "Rehearsal.(1995).1080p.H264.AAC"
    assert extract_english_title("개인교수 My.Tutor.1983.1080p.BluRay.x264-SADPANDA") == "My.Tutor.1983.1080p.BluRay.x264-SADPANDA"

    # 3. 특수 릴리즈 태그 + 한글/한자 + 영문 타이틀
    assert extract_english_title("(X-R) 레드 헤어 우먼 赤い髮의女 The Woman With Red Hair 1979") == "The Woman With Red Hair 1979"

    # 4. 순수 한글 / 에피소드
    assert extract_english_title("모범형사2 E06.2022.0814.1080P.H264-FOA") == "모범형사2 E06.2022.0814.1080P.H264-FOA"
    assert extract_english_title("괴물.2006.1080p.KOR.HDRip") == "괴물.2006.1080p.KOR.HDRip"


def test_get_language_code():
    assert get_language_code({"language": "kor"}) == "ko"
    assert get_language_code({"language": "eng"}) == "en"
    assert get_language_code({"language": "chi"}) == "zh"
    assert get_language_code({"language": "jpn"}) == "ja"
    assert get_language_code({"language": "fre"}) == "fr"
    assert get_language_code({"language": "spa"}) == "es"
    assert get_language_code({"language": "swe"}) == "sv"
    assert get_language_code({"language": "xyz"}) == "xyz"

    # language가 없거나 und인 경우 title 태그에서 탐색
    assert get_language_code({"language": "und", "title": "Korean Full"}) == "ko"
    assert get_language_code({"title": "English Forced"}) == "en"
    assert get_language_code({}) == "und"


def test_get_classification_keywords():
    # Forced
    stream_forced = {
        "disposition": {"forced": 1},
        "tags": {"title": "Forced"},
    }
    assert "forced" in get_classification_keywords(stream_forced)

    # SDH
    stream_sdh = {
        "disposition": {"hearing_impaired": 1},
        "tags": {"title": "SDH"},
    }
    assert "sdh" in get_classification_keywords(stream_sdh)

    # Commentary
    stream_comm = {
        "disposition": {"comment": 1},
        "tags": {"title": "Commentary"},
    }
    assert "commentary" in get_classification_keywords(stream_comm)

    # Traditional / Simplified
    stream_trad = {
        "disposition": {},
        "tags": {"title": "Traditional"},
    }
    assert "traditional" in get_classification_keywords(stream_trad)

    stream_simp = {
        "disposition": {},
        "tags": {"title": "简体"},
    }
    assert "simplified" in get_classification_keywords(stream_simp)

    # Additional description in title (e.g., British Forced)
    stream_british = {
        "disposition": {"forced": 1},
        "tags": {"title": "British Forced"},
    }
    kw = get_classification_keywords(stream_british)
    assert "forced" in kw
    assert "british" in kw


def test_generate_subtitle_filename():
    used = set()

    # 1. 일반 자막 (키워드 없음)
    f1 = generate_subtitle_filename("MovieName", "ko", [], ".srt", used)
    assert f1 == "MovieName-ko.srt"

    # 2. 강제 자막
    f2 = generate_subtitle_filename("MovieName", "ko", ["forced"], ".srt", used)
    assert f2 == "MovieName-ko-forced.srt"

    # 3. SDH 자막
    f3 = generate_subtitle_filename("MovieName", "ko", ["sdh"], ".srt", used)
    assert f3 == "MovieName-ko-sdh.srt"

    # 4. 키워드 없는 자막이 중복 생성될 때 넘버링 방지 확인
    f4 = generate_subtitle_filename("MovieName", "ko", [], ".srt", used)
    assert f4 == "MovieName-ko-2.srt"

    # 5. 영어 다중 키워드
    f5 = generate_subtitle_filename("MovieName", "en", ["forced", "british"], ".srt", used)
    assert f5 == "MovieName-en-forced-british.srt"


def test_cli_output_dir_not_exist(monkeypatch, tmp_path, capsys):
    test_video = tmp_path / "test.mkv"
    test_video.write_text("dummy")

    non_exist_dir = tmp_path / "non_existent_folder"

    monkeypatch.setattr(sys, "argv", ["jamak-extract", str(test_video), "-o", str(non_exist_dir)])

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "존재하지 않거나 디렉터리가 아닙니다" in captured.err


def test_cli_input_not_exist(monkeypatch, tmp_path, capsys):
    non_exist_file = tmp_path / "non_existent_video.mkv"

    monkeypatch.setattr(sys, "argv", ["jamak-extract", str(non_exist_file)])

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "입력 파일" in captured.err and "찾을 수 없습니다" in captured.err
