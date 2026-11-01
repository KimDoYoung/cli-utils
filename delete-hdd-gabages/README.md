# delete-hdd-gabages

## 개요

- uv로 만든다.
- 인자로 받은 폴더 하위에서 지정한 쓰레기 파일들을 지운다.
- 지울 파일은 hard coding한다.
- 인자가 없거나, 폴더가 없으면 error 메세지 후 종료한다.
- 진행하기전에 confirm y/N를 묻는다.
- 지정한 폴더 하위 폴더를 모두 순회하면서 삭제목록 파일에 해당하면 지운다.
- 삭제목록은 와일드카드를 지원한다.
- --help 옵션과 , --version 옵션을 지원한다.

## 삭제 목록

- 'RARBG'로 시작하는 파일들이면서 파일크기가 100M이하인것들
- *.txt
- *.nfo
- *.url
- *.exe

## 실행 방법

```bash
# 개발 가상환경에서 실행
uv run delete-hdd-gabages <folder>

# 전역 설치 상태에서 직접 실행
delete-hdd-gabages <folder>
```
