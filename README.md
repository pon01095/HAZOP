# HAZOP 자동화 시스템

OpenAI GPT-4를 활용한 P&ID 다이어그램 기반 HAZOP 분석 자동화 시스템

## 🚀 시작하기

### 1. 사전 준비

#### 필요한 라이브러리 설치
```bash
pip install -r requirements.txt
```

#### API 키 설정
1. `.env` 파일에서 `OPENAI_API_KEY`를 실제 API 키로 수정:
```env
OPENAI_API_KEY=여기에_실제_API_키를_입력
```
### 2. 시스템 구조

```
코드/
├── .env                                    # 환경 설정 파일
├── config.py                              # 설정 관리
├── requirements.txt                        # 필수 라이브러리
├── gpt4o_P&ID_input(Agent1).py           # 공정 요소 분석
├── GPT4o Node (Agent2).py                # 노드 분리
├── GPT4o Node2 (Agent2).py               # 노드 분리 (대안)
├── GPT4o Parameter_Guideword (Agent3).py # 공정 변수 분석
├── GPT4o CreateDeviation (Agent4).py     # 이탈 시나리오 생성
├── GPT4o Safeguard (Agent5).py           # 안전장치 분석
└── GPT4o HAZOP Table (Agent6).py         # HAZOP 테이블 생성
```

### 3. 실행 순서

HAZOP 분석은 다음 순서로 실행:

1. **Agent1**: P&ID 다이어그램에서 공정 요소 식별
   ```bash
   python "gpt4o_P&ID_input(Agent1).py"
   ```

2. **Agent2**: 공정을 HAZOP 분석을 위한 노드별로 분리
   ```bash
   python "GPT4o Node (Agent2).py"
   ```

3. **Agent3**: 특정 노드의 공정 변수 식별
   ```bash
   python "GPT4o Parameter_Guideword (Agent3).py"
   ```

4. **Agent4**: 공정 변수와 가이드워드를 결합하여 이탈 시나리오 생성
   ```bash
   python "GPT4o CreateDeviation (Agent4).py"
   ```

5. **Agent5**: 각 이탈에 대한 원인, 결과, 안전장치 분석
   ```bash
   python "GPT4o Safeguard (Agent5).py"
   ```

6. **Agent6**: 최종 HAZOP 테이블 생성 (Excel 파일 출력)
   ```bash
   python "GPT4o HAZOP Table (Agent6).py"
   ```

### 4. 주요 변경사항

#### 보안 개선
✅ **적용된 수정사항**:
- API 키 하드코딩 제거 → 환경변수 사용
- 불필요한 라이브러리 import 제거
- 중복된 함수 호출 제거 (base64 인코딩)
- 하드코딩된 파일 경로를 설정 파일로 이동
- `eval()` 함수를 `ast.literal_eval()`로 대체 (Agent6)
- 설정 중앙화를 통한 유지보수성 향상

#### Agent 4 품질 개선 (v3) 🆕
✅ **CSV 데이터베이스 통합**:
- 전문 failure scenarios 데이터베이스 참고
- 산업 표준 수준의 deviation 설명 생성
- 구체적인 원인-현상-결과 구조 작성
- 장비 태그 및 설계값 포함

✅ **확률 기반 위험도 평가 + 시각화**:
- 각 deviation의 발생 가능성 1-10 점수 평가
- Bar plot + Cumulative probability 그래프 자동 생성
- 고위험 deviation (점수 7 이상) 자동 추출
- 고해상도 PNG 그래프 (300 DPI)

**개선 예시**:
- ❌ 기존: "압력 증가 (High Pressure)"
- ✅ 개선: "BL-1101 블로워 과부하로 토출 압력 0.3→0.5 bar.g 상승. 배관 과압으로 안전밸브 작동 가능" + 발생 가능성 9/10 점

📖 **상세 가이드**: `AGENT4_IMPROVEMENT_GUIDE.md` 참조

### 5. 설정 파일 (.env) 사용법

`.env` 파일에서 다음 설정을 변경:

```env
# OpenAI API 설정
OPENAI_API_KEY=your_api_key_here

# 파일 경로 설정
BASE_DIRECTORY=""
IMAGE_DIRECTORY=""
DEFAULT_IMAGE=""

# 공정 개요
""
```

### 6. 출력 파일

각 Agent는 다음 파일들을 생성:

- **Agent1**: `공정요소.txt/json` - 공정 구성요소 목록
- **Agent2**: `Agent2.txt/json` - 노드별 분리 결과
- **Agent3**: `Agent3.txt/json` - 공정 변수 목록
- **Agent4**:
  - `Agent4.txt` - 이탈 시나리오 (텍스트)
  - `Agent4_nodeX.json` - 이탈 시나리오 (JSON, probability_score 포함)
  - `Agent4_nodeX_probability_graph.png` - 확률 분석 그래프 🆕
- **Agent5**: `Agent5.txt/json` - 안전장치 분석
- **Agent6**: `HAZOP_table.xlsx` - 최종 HAZOP 테이블 (Excel)

### 7. 문제 해결

#### 공통 문제
- **ModuleNotFoundError**: `pip install -r requirements.txt` 실행
- **API 키 오류**: `.env` 파일의 API 키 확인
- **파일 경로 오류**: `.env` 파일의 경로 설정 확인

#### 지원
시스템 사용 중 문제가 발생하면 다음을 확인:
1. 모든 필수 라이브러리가 설치되었는지
2. API 키가 올바르게 설정되었는지
3. 파일 경로가 올바른지
4. 이전 Agent의 출력 파일이 존재하는지
5. .env 파일 생성
