# API_USER
공개 API(KOSIS/관세청) 데이터를 수집해 포항 배터리 산업 분석용 산출물을 생성하는 프로젝트입니다.

## 1) API 키 발급 방법

### KOSIS API 키
1. KOSIS 국가통계포털 Open API 페이지 접속
2. 회원가입/로그인 후 Open API 활용 신청
3. 승인 후 발급된 API Key 확인
4. `.env`에 `KOSIS_API_KEY`로 등록

> 참고: 통계표(`tblId`)와 항목(`itmId`)은 사용하는 통계표에 따라 달라질 수 있으므로 사전에 KOSIS 개발자 문서에서 확인하세요.

### 관세청(관세무역개발원) API 키
1. 공공데이터포털(data.go.kr) 회원가입/로그인
2. `관세청` 또는 `수출입 무역통계` API 검색
3. 활용신청 후 일반 인증키(서비스키) 발급
4. `.env`에 `CUSTOMS_API_KEY`로 등록

## 2) `.env` 설정
프로젝트 루트(`/workspace/API_USER`)에 `.env` 파일을 생성하고 아래 값을 입력합니다. (요청하신 KOSIS API 키를 반영했습니다.)

```bash
KOSIS_API_KEY=NDVlZjliMTg2ZmY2OTExNjJkNzE3YWYzMjFkODIyYWM=
CUSTOMS_API_KEY=YOUR_CUSTOMS_API_KEY
```

## 3) 설치 및 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas requests python-dotenv openpyxl
```

실행 명령:

```bash
python src/main.py \
  --region 37010 \
  --start-period 202401 \
  --end-period 202412 \
  --industry-code T10 \
  --hs-code 850760 \
  --save-mode both
```

## 4) 필수 파라미터 설명
모든 파라미터는 필수입니다.

- `--region`: 지역 코드 (예: `37010`)
- `--start-period`: 시작 기간 `YYYYMM` (예: `202401`)
- `--end-period`: 종료 기간 `YYYYMM` (예: `202412`)
- `--industry-code`: 산업 코드 (KOSIS 통계표 기준 항목 코드)
- `--hs-code`: HS 코드 (관세청/무역통계 기준 품목 코드)
- `--save-mode`: 저장 방식
  - `separate`: KOSIS/관세청 개별 파일만 저장
  - `merged`: 병합 파일만 저장
  - `both`: 개별 + 병합 파일 모두 저장(기본값)

## 5) 산출물 저장 규칙
`src/main.py`는 저장 전에 `output/` 경로를 자동 생성합니다(없으면 생성).

파일명 규칙:
- 병합 파일: `pohang_battery_industry_YYYYMMDD.csv`, `pohang_battery_industry_YYYYMMDD.xlsx`
- KOSIS 개별 파일: `pohang_battery_industry_YYYYMMDD_kosis.csv`, `..._kosis.xlsx`
- 관세청 개별 파일: `pohang_battery_industry_YYYYMMDD_customs.csv`, `..._customs.xlsx`

즉, CSV/XLSX를 항상 쌍으로 저장합니다.

## 6) EIS(고용보험) 연계 계획
현재는 EIS 고용보험 현재값 연계를 즉시 구현하지 않습니다.

대신 아래 절차를 먼저 수행합니다.
1. EIS API 명세에서 **산업분류(산업코드) 기반 조회 지원 여부**를 사전 검증
2. 지원 여부/제약사항(지역 단위, 기간 단위, 응답 스키마)을 문서화
3. 검증 완료 후 `src/clients/eis.py`로 클라이언트 모듈을 분리 구현
4. `src/main.py`에서 `src/clients/eis.py`를 선택적으로 호출하도록 확장

위 절차 전에는 EIS 기능을 본 파이프라인 기본 흐름에 포함하지 않습니다.
