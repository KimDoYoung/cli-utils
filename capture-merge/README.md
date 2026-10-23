# capture-merge

CLI utility for capture-merge.

## 실행 방법

```bash
# 개발 가상환경에서 실행
uv run capture-merge

# 전역 설치 상태에서 직접 실행
capture-merge
```

## 프롬프트

- python으로 ‘capture-merge’ 작성한다.

- pc에서 영화를 보면서 capture한 이미지들 여러장을 1개의 이미지로 만드는 커맨드라인 명령어 프로그램 cli 명령어로 동작한다.

- 파일명을 입력받는다.

- capture-merge Snake 라고 하면 ls Snake 로 나타나는 이미지를 대상으로 한다.
- 여러가지 옵션이 있다.
```
    –version
    –help
    –width=1200 (만들어지는 target image의 width 를 지정) default 1200, 500-2800 의 크기를 갖는다. 넘어가면 오류
    –columns-per-row=2 ( 1 row에 몇장의 이미지를 배치할지 결정 default 2)
    –x-gap=5 (x 축으로 각 이미지 사이의 공간 default 5)
    –y-gap=5 (y 축으로 각 이미지 사이의 공간 default 5)
    –out abc.png (만들어질 파일명을 지정한다. 파일은 png로 한다.out옵션이 없다면 catpure-merged-1.png 와 같이 만들어지고 이미 있다면 
    번호를 올린다. 즉 catpure-merged-2.png … 이런식으로 한다.
```
-소스 이미지는 옵션값 width의 값과 x-gap , columns-per-row의 값에 따라서 각 이미지의 width를 계산하고 ratio비율을 맞추어서 계산한다. 단 소스이미지를 확대하지는 말고 소스이미지를 축소를 한다.