# kakao-emoticon

## 개요

- 카카오 이모티콘을 웹에서 스크래핑해서 PCMS에 gif이미지로 변환해서 스티커로 사용
- uv 사용, python 으로 개발
- kakao-emoticon <url> 
- ffmpeg를 이용하여 gif로 변환한다.

## 동작

1. uv 사용
2. command line에서 사용, no-gui
3. argument 1개 url 사용
4. url에서 html 소스를 get,
5. ''<section aria-label="상세 이모티콘"'  > ul > li 의 이미지 tag추출 리스트로 갖고 있는다.
6. 이미지리스트를 looping돌면서 이미지 다운로드 
7. wait시간은 1~10 random동안 wait후 다음 이미지 다운로드
8. 파일은 현재폴더에 저장하면 됨.

## uv install 사용

- 아무 폴더나 가서 kakao-emoticon으로 명렁어라인에서 수행
- 개발/수정 편의를 위해 --editable 권장 (코드 수정 시 재설치 불필요)

```bash
uv tool install --editable .
```

## 사용법
- [kakao 이모티지](https://e.kakao.com/?t_obj=item_homebtn) 에서 맘에 드는 것을 찾아서 url을 취득한다.

```bash
kakao-emoticon --help
kakao-emoticon --index <url>

```