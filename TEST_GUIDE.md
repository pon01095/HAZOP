# HAZOP 개별 실행 vs 통합 실행 비교 가이드

## 📋 목적
개별 실행(Agent 1~6을 수동으로 하나씩 실행)과 통합 실행(main_integrated.py로 자동 실행)의 결과를 비교하여 차이가 있는지 확인합니다.

---

## 🔧 준비 단계

### 1. 출력 디렉토리 설정

비교를 위해 결과를 별도 폴더에 저장해야 합니다.

#### `.env` 파일 수정:

**개별 실행용 설정:**
```env
BASE_DIRECTORY=C:/Users/B/Desktop/HAZOP 자동화/GPT4o_individual
```

**통합 실행용 설정:**
```env
BASE_DIRECTORY=C:/Users/B/Desktop/HAZOP 자동화/GPT4o_integrated
```

---

## 📝 테스트 절차

### **STEP 1: 개별 실행 (수동)**

1. `.env` 파일에서 `BASE_DIRECTORY`를 `GPT4o_individual`로 설정

2. 각 Agent를 순서대로 실행:

```bash
# Agent 1 실행
python "gpt4o_P&ID_input(Agent1).py"

# Agent 2 실행
python "GPT4o Node (Agent2).py"

# Agent 3 실행
python "GPT4o Parameter_Guideword (Agent3).py"

# Agent 4 실행
python "GPT4o CreateDeviation (Agent4).py"

# Agent 5 실행
python "GPT4o Safeguard (Agent5).py"

# Agent 6 실행
python "GPT4o HAZOP Table (Agent6).py"
```

3. 결과 파일 확인:
   - `GPT4o_individual/공정요소.txt`
   - `GPT4o_individual/Agent2.txt`
   - `GPT4o_individual/Agent3.txt`
   - `GPT4o_individual/Agent4.txt`
   - `GPT4o_individual/Agent5.txt`
   - `GPT4o_individual/HAZOP_table.xlsx`

4. **중요:** 실행 시간과 발생한 문제 기록

---

### **STEP 2: 통합 실행 (자동)**

1. `.env` 파일에서 `BASE_DIRECTORY`를 `GPT4o_integrated`로 변경

2. 통합 스크립트 실행:

```bash
python main_integrated.py
```

3. 실행 로그 확인:
   - 콘솔에 각 Agent 실행 상태 출력
   - `GPT4o_integrated/logs/execution_log_YYYYMMDD_HHMMSS.json` 생성

4. 결과 파일 확인:
   - `GPT4o_integrated/공정요소.txt`
   - `GPT4o_integrated/Agent2.txt`
   - `GPT4o_integrated/Agent3.txt`
   - `GPT4o_integrated/Agent4.txt`
   - `GPT4o_integrated/Agent5.txt`
   - `GPT4o_integrated/HAZOP_table.xlsx`

---

### **STEP 3: 결과 비교**

1. 비교 스크립트 실행:

```bash
python compare_results.py
```

2. 프롬프트에 따라 디렉토리 입력:
   - 디렉토리 1: `C:/Users/B/Desktop/HAZOP 자동화/GPT4o_individual`
   - 디렉토리 2: `C:/Users/B/Desktop/HAZOP 자동화/GPT4o_integrated`

3. 비교 보고서 확인:
   - 콘솔에 파일별 비교 결과 출력
   - `comparison_report_YYYYMMDD_HHMMSS.json` 생성

---

## 📊 결과 분석

### 비교 항목

| 항목 | 설명 | 예상 결과 |
|-----|------|----------|
| **파일 존재 여부** | 6개 파일 모두 생성되었는가? | 동일 |
| **파일 크기** | 파일 크기가 동일한가? | 유사 (API 응답의 비결정성으로 약간 차이 가능) |
| **내용 유사도** | 텍스트 내용이 얼마나 유사한가? | 90% 이상 유사 |
| **Excel 구조** | DataFrame 행/열 개수가 동일한가? | 동일 |
| **Excel 데이터** | DataFrame 내용이 동일한가? | 유사 |

### GPT-4o 응답의 비결정성

**중요:** GPT-4o는 같은 입력에도 다른 출력을 생성할 수 있습니다.
- Temperature=1 (기본값): 창의적, 다양한 응답
- 따라서 100% 동일한 결과는 기대하기 어려움
- **핵심 정보(노드 개수, 공정 변수, 이탈 종류 등)가 유사하면 정상**

---

## 🔍 차이 발생 가능 케이스

### 1. 정상적인 차이
- 문장 표현 차이 (의미는 동일)
- 순서 차이 (내용은 동일)
- 공백/줄바꿈 차이

### 2. 문제가 있는 차이
- 파일 누락
- 노드 개수 차이
- 공정 변수 누락
- Excel 행/열 개수 차이

---

## 🛠️ 문제 해결

### 문제 1: Agent 실행 실패

**증상:**
```
API 요청 오류: ...
파일 읽기 오류: ...
```

**해결:**
1. API 키 확인 (`.env`)
2. 이전 Agent 출력 파일 존재 확인
3. 네트워크 연결 확인

### 문제 2: 출력 파일 미생성

**증상:**
Agent가 완료되었지만 파일이 없음

**해결:**
1. `BASE_DIRECTORY` 경로 확인
2. 폴더 쓰기 권한 확인
3. 디스크 공간 확인

### 문제 3: 비교 결과가 크게 다름

**증상:**
유사도 50% 이하

**가능 원인:**
1. API 버전 차이
2. 프롬프트 수정 후 비교
3. 다른 이미지 파일 사용

---

## 📈 성능 비교

### 측정 항목

| 항목 | 개별 실행 | 통합 실행 |
|-----|---------|---------|
| **총 소요 시간** | 수동 + 대기 시간 | 자동 실행 |
| **사용 편의성** | 각 Agent 수동 실행 | 1회 실행 |
| **오류 추적** | 수동 확인 필요 | 자동 로깅 |
| **중단 후 재시작** | 어려움 | 어려움 (현재) |

---

## 💡 개선 제안

### 재현성 향상
```python
# config.py에 추가
TEMPERATURE = 0  # 결정적 응답
```

### 실행 시간 비교
```python
# 각 Agent 실행 전후 시간 기록
# 통합 실행은 자동으로 기록됨
```

---

## 📝 체크리스트

- [ ] `.env` 파일 설정 확인
- [ ] 개별 실행 완료 (6개 파일 생성)
- [ ] 통합 실행 완료 (6개 파일 생성)
- [ ] 비교 스크립트 실행
- [ ] 비교 보고서 확인
- [ ] 차이 원인 분석
- [ ] 결과 문서화

---

## 📞 문의

문제 발생 시:
1. `execution_log_*.json` 확인
2. `comparison_report_*.json` 확인
3. 콘솔 출력 캡처
