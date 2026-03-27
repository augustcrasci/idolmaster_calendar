# idolmaster_calendar

아이마스 공식 포털의 일정과 생일, 티켓 응모 마감, 한국/일본 공휴일을 한곳에 모아 보는 로컬 캘린더 프로젝트입니다.

월간 / 주간 / 리스트 보기, 관심 일정, 메모, 업데이트 변경 확인까지 한 번에 사용할 수 있습니다.

## 주요 기능

- 아이마스 포털 공식 일정 / 이벤트 수집
- 아이돌 / 캐스트 생일 수집
- 티켓 응모 마감일 수집
- 한국 / 일본 공휴일 표시
- 월간 / 주간 / 리스트 보기
- 관심 일정 저장
- 날짜별 메모와 배경색 지정
- 이번 DB 업데이트에서 추가 / 변경 / 삭제된 일정 확인
- 다크모드 지원
- UI 한글 / 영어 전환

## 요구 사항

- Windows
- Python 3.x
- 인터넷 연결

## 설치

CMD 또는 PowerShell에서 아래 순서대로 실행합니다.

```bat
pip install playwright requests beautifulsoup4 holidays
playwright install
```

추가로 필요한 `pip` 패키지는 없습니다.

- `launcher.pyw`는 Python 기본 포함 라이브러리인 `tkinter`를 사용합니다.
- 일반적인 Windows Python 설치에서는 별도 설치가 필요 없습니다.

## 실행 방법

가장 편한 방법은 `launcher.pyw`를 더블클릭하는 것입니다.

실행 후 아래 3가지 중 하나를 선택할 수 있습니다.

- `DB 업데이트만`
- `뷰어만 실행`
- `DB 업데이트 후 뷰어 실행`

추천 사용 방식:

1. 처음 실행할 때는 `DB 업데이트 후 뷰어 실행`
2. 이후 화면만 볼 때는 `뷰어만 실행`

## 폴더 구조

```text
launcher.pyw          GUI 실행기
app/                  크롤러, 공통 로직, 로컬 서버
data/                 수집된 JSON 데이터
web/                  캘린더 프론트엔드
```

### app/

- `imasportal_year.py`: 공식 일정 수집
- `idolbd.py`: 생일 데이터 수집
- `ticketing.py`: 티켓 응모 마감 수집
- `get_holidays.py`: 공휴일 데이터 생성
- `refresh_all.py`: 전체 데이터 갱신
- `viewer.py`: 로컬 웹 서버 실행
- `run_mode.py`: 뷰어 실행 엔트리포인트

### data/

- `schedule_data.json`: 공식 일정 데이터
- `birthday_data.json`: 생일 데이터
- `ticket_grouped_data.json`: 티켓 응모 마감 데이터
- `holidays.json`: 한국 / 일본 공휴일 데이터
- `change_summary.json`: 최근 업데이트 변경 요약

### web/

- `index.html`: 캘린더 화면
- `index_backup.html`: 백업 파일

## 데이터 처리 기준

- 티켓 데이터는 `시작일`이 아니라 `마감일` 기준으로 표시됩니다.
- 진행 중 이벤트는 포털 표시 방식에 따라 날짜가 보정되어 저장됩니다.
- 메모 / 테마 / 관심 일정 / UI 언어 설정은 브라우저 `localStorage`에 저장됩니다.

## 주의 사항

- 공식 사이트 구조가 바뀌면 크롤러가 일시적으로 동작하지 않을 수 있습니다.
- 브라우저 화면이 이상하게 보이면 `Ctrl + F5`로 강력 새로고침해 주세요.
- 뷰어는 로컬 서버를 사용하므로, 새로고침을 정상적으로 쓰려면 백그라운드 서버가 살아 있어야 합니다.

## 빠른 시작

```text
1. Python 설치
2. pip install playwright requests beautifulsoup4 holidays
3. playwright install
4. launcher.pyw 실행
5. DB 업데이트 후 뷰어 실행 선택
```

## Git 사용 메모

로컬에서 수정 후 저장하는 가장 기본 흐름:

```bat
git add .
git commit -m "변경 내용 요약"
git push
```

