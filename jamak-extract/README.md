# jamak-extract

CLI utility for jamak-extract.

## 주요 변경 사항

1. **모든 자막 일괄 추출 지원**
   - 첫 번째 자막만 추출하던 방식에서 영상 파일 내의 **모든 자막 스트림을 탐색**하여 추출하도록 변경되었습니다.
   - 단일 패스(single-pass) 일괄 추출 방식을 적용하여 대용량 영상 파일도 비디오 전체를 한 번만 읽고 모든 자막을 동시에 고속으로 추출합니다. (실패 시 개별 스트림 추출 fallback)
   - 텍스트 자막(SRT/ASS 등)은 `.srt`로 인코딩/복사하며, 텍스트 변환이 불가능한 PGS(이미지) 자막은 손상 없이 `.sup`로 자동 분기 처리합니다.

2. **`-o` / `--output` 폴더 지정 및 유효성 검사**
   - `-o` 옵션을 **자막을 저장할 출력 폴더 경로**로 변경했습니다.
   - 지정한 폴더가 존재하지 않거나 디렉터리가 아닌 경우 명확한 오류 메시지를 출력하고 종료합니다 (`sys.exit(1)`).
   - `-o` 옵션이 생략되면 현재 실행 폴더(`Path.cwd()`)를 기본 저장 위치로 사용합니다.

3. **파일명 자동 생성 (`<영어명>-국적-기타분류키워드.srt`)**
   - **`<영어명>`**: 파일명 앞부분에 한글/특수문자가 있는 경우 영문 타이틀 부분만 스마트하게 분리합니다. (예: `미스 마치 Miss.March.2009...` $\rightarrow$ `Miss.March.2009...`, 순수 한글명은 원본 유지)
   - **`국적`**: ffprobe 스트림의 언어 메타데이터를 표준 2자리 코드(`ko`, `en`, `zh`, `ja` 등)로 정규화합니다.
   - **`기타분류키워드`**: `forced`(강제 자막), `sdh`(청각장애인용), `commentary`(해설/코멘터리), `traditional`/`simplified`(중국어 번체/간체) 및 트랙 타이틀 태그에서 키워드를 추출하여 하이픈으로 결합합니다.
   - 일반 기본 자막은 불필요한 태그 없이 `<영어명>-<국적>.srt`로 생성되며, 동일 언어 파일이 중복될 경우 `<영어명>-<국적>-2.srt` 형태로 파일 덮어쓰기를 방지합니다.

## 생성 파일명 예시

| 자막 스트림 속성 | 생성 파일명 |
| :--- | :--- |
| 한국어 일반 자막 | `MovieTitle-ko.srt` |
| 한국어 강제 자막 (Forced) | `MovieTitle-ko-forced.srt` |
| 한국어 청각장애인용 (SDH) | `MovieTitle-ko-sdh.srt` |
| 영어 코멘터리 자막 | `MovieTitle-en-commentary.srt` |
| 영어 Forced + British 자막 | `MovieTitle-en-forced-british.srt` |
| 중국어 번체 PGS 자막 | `MovieTitle-zh-traditional.sup` |

## 실행 방법

```bash
# 개발 가상환경에서 실행
uv run jamak-extract <video-file> [-o 출력폴더]

# 전역 설치 상태에서 직접 실행
jamak-extract <video-file> [-o 출력폴더]
```

## 옵션

- `input`: 자막을 추출할 영상 파일 경로 (mkv 등)
- `-o`, `--output`: 자막을 저장할 출력 폴더 경로 (미지정 시 현재 실행 폴더, 폴더 미존재 시 오류)
- `-v`, `--version`: 버전 정보 출력
- `-h`, `--help`: 도움말 출력
