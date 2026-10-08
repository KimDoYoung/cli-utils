# hdd-rename

## 개요

- 이동식 hdd를 쭉 돌면서 폴더안에 a.mkv와 a.smi 또는 a.srt가 있는 경우 즉 1개의 동영상파일과 1개 또는 서로다른 확장자의 자막파일이 있는 경우에 한해서 자막 파일의 파일명을  동영상파일의 파일명으로 바꾸어 준다.


- uv를 사용해서 개발한다.
- 파일명은 hdd-rename 으로 한다.
- 사용법 : hdd-rename <hdd mout point> --log a.log
- 사용법 : hdd-rename --version 

## 주의

1. 폴더 안에 여러개의 동영상파일이 있는 경우 그 폴더를 skip한다.
2. 폴더 안에 동영상파일 1개, 자막파일 1개 또는 2개일 경우가 아니라면 skip한다.
3. 동영상 파일 a.mkv, 자막 파일 a1.smi 라면 a.mkv, a.smi 가 되어야한다.
4. --log 옵션이 없으면 실행폴더에 out.log 파일에 실행 로그를 남긴다.