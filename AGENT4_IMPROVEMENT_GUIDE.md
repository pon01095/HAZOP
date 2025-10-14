# Agent 4 개선 가이드 (v3)

## 📋 개선 개요

Agent 4를 개선하여 **CSV 데이터베이스의 전문 failure scenarios를 참고**하고,
**각 deviation의 발생 가능성을 확률로 평가하여 그래프로 시각화**합니다.
이를 통해 더 구체적이고 실무적인 HAZOP deviation 설명과 위험도 평가를 제공합니다.

---

## 🎯 개선 목적

### Before (기존)
```json
{
  "deviation": "유량 증가 (High Flow)",
  "description": "설계 유량을 초과하는 과도한 가스 공급"
}
```
→ 막연하고 일반적인 설명

### After (개선)
```json
{
  "deviation": "유량 증가 (High Flow)",
  "description": "BL-1101 블로워 토출 압력 이상 상승으로 인한 설계 유량 90 Nm³/hr 초과. 하류 D-1101 제습장치 과부하 및 수분 제거 효율 저하 유발"
}
```
→ 장비 태그, 설계값, 구체적 원인/결과 포함

---

## 🔧 주요 변경사항

### 1. CSV 데이터베이스 통합

**파일 경로**: `C:/Users/B/Desktop/HAZOP 자동화/참고문헌/수정 엑셀/Heat_Transfer_Equipment.csv`

**CSV 구조**:
| 컬럼 | 설명 |
|------|------|
| No. | 시나리오 번호 |
| Operational Deviations | Overpressure, High Temperature 등 |
| Failure Scenarios | 구체적인 고장 시나리오 설명 (실무 표준) |
| Inherently Safer/Passive | 본질안전/수동 안전장치 |
| Active | 능동 안전장치 |
| Procedural | 절차적 안전장치 |

**로드 로직**:
```python
# CSV 데이터베이스 로드
df = pd.read_csv(config.CSV_SCENARIOS_PATH)

# LLM이 참고할 수 있도록 텍스트 변환
csv_scenarios = "\n\n## 전문 Failure Scenarios 데이터베이스 (참고용)\n\n"
for idx, row in df.iterrows():
    csv_scenarios += f"**{row['Operational Deviations']}**\n"
    csv_scenarios += f"- Scenario: {row['Failure Scenarios']}\n"
    csv_scenarios += f"- Safeguards: {row['Inherently Safer/Passive']}\n\n"
```

### 2. 프롬프트 강화

#### System Prompt 개선
```python
## 이탈 작성 원칙 (중요!)
1. **구체성**: 막연한 표현 대신 명확한 현상 기술
   - 나쁜 예: "압력이 증가함"
   - 좋은 예: "압축기 과부하로 토출 압력이 0.3 bar.g에서 0.5 bar.g로 상승"

2. **현실성**: 실제 발생 가능한 시나리오
   - 설비 고장, 밸브 오작동, 제어 실패 등 구체적 원인 언급

3. **기술성**: 공학적 용어와 장비 태그 사용
   - 노드의 장비 태그를 활용 (예: "BL-1101 블로워", "D-1101 제습장치")

4. **전문성**: 제공된 Failure Scenarios 데이터베이스를 참고하여 산업 표준 수준의 설명 작성
```

#### User Prompt 개선
- **노드 상세 정보 추가**: 설계 의도, 장비 태그, 계기 태그
- **CSV scenarios 주입**: 전문 시나리오를 프롬프트에 직접 포함
- **명확한 작성 지침**: 원인-현상-결과 구조 요구

### 3. 품질 검증 추가

```python
# 품질 검증
low_quality_count = 0
for dev in deviations:
    desc = dev.get('description', '')
    if len(desc) < 20:  # 너무 짧은 설명
        low_quality_count += 1
        print(f"[WARNING] 짧은 설명 발견: {dev.get('deviation')}")

if low_quality_count > 0:
    print(f"[WARNING] {low_quality_count}개의 deviation이 충분히 상세하지 않습니다.")
```

### 4. Agent2 정보 활용

기존에는 Agent3에서만 정보를 가져왔지만, 이제 Agent2의 노드 정보도 활용:
- 설계 의도 (design_intent)
- 장비 태그 목록 (equipment_tags)
- 계기 태그 목록 (instrument_tags)

---

## 📊 기대 효과

### 1. 설명 품질 향상
- ❌ 기존: "압력 증가"
- ✅ 개선: "BL-1101 블로워 과부하로 토출 압력 0.3→0.5 bar.g 상승"

### 2. 실무 적용성
- 산업 표준 failure scenarios 참고
- 실제 발생 가능한 구체적 원인 제시

### 3. 장비 추적성
- 장비 태그 명시로 P&ID와 연결
- 담당자가 즉시 위치 파악 가능

### 4. **확률 기반 위험도 평가** 🆕
- 각 deviation의 발생 가능성을 1-10 점수로 평가
- 고위험 deviation을 시각적으로 즉시 파악
- 우선순위 기반 안전 대책 수립 지원

### 5. **시각화** 🆕
- Bar plot: 각 deviation의 발생 가능성 점수
- Cumulative plot: 누적 위험도 분포
- 고해상도 PNG 그래프 자동 생성 (300 DPI)

### 6. 최종 HAZOP 테이블 품질
- Agent 5의 원인/결과 분석에 더 나은 입력 제공
- Agent 6의 Excel 테이블이 더 전문적으로 작성됨
- JSON에 probability_score 필드 추가로 확장성 확보

---

## 🚀 사용 방법

### 1. 기본 실행 (변경 없음)
```bash
# 개별 실행
python "GPT4o CreateDeviation (Agent4).py"

# 통합 실행
python main_integrated_all_nodes.py --agents 4
```

### 2. CSV 파일 커스터마이징

다른 CSV 파일을 사용하고 싶다면 `.env` 파일에 추가:

```env
# .env 파일
CSV_SCENARIOS_PATH=C:/Users/B/Desktop/내_시나리오.csv
```

**CSV 파일 형식**:
```csv
No.,Operational Deviations,Failure Scenarios,Inherently Safer/Passive,Active,Procedural
1,Overpressure,Corrosion/erosion of exchanger internals...,PSV-101,Emergency relief,Corrosion detection
```

### 3. CSV 없이 실행

CSV 파일이 없어도 작동합니다 (기본 모드로 폴백):
```
[WARNING] CSV 파일을 찾을 수 없습니다: ...
[WARNING] 기본 deviation 생성 모드로 진행합니다.
```

---

## 🔍 실행 예시

### 콘솔 출력
```
[INFO] 노드: 1차 제습
[INFO] 선택된 변수: Flow, Pressure, Temperature
[INFO] Agent 4 실행 중: Node 1 deviation 생성...
[INFO] CSV 데이터베이스 참조 모드: 활성화
[INFO] CSV 데이터베이스 로드: 16개 시나리오

==========================================================
Agent 4 분석 결과 (Node 1)
==========================================================
{
  "node_id": 1,
  "node_name": "1차 제습",
  "deviations": [
    {
      "parameter": "Flow",
      "guideword": "None",
      "deviation": "유량 없음 (No Flow)",
      "description": "가스 공급원 차단 또는 BL-1101 블로워 정지로 인한 유량 완전 차단. 하류 D-1101 제습장치 공정 중단 및 압력 강하 발생. FI-1101 유량계 저 알람 작동"
    },
    ...
  ]
}

[VALIDATION] JSON 파싱 성공
[VALIDATION] 생성된 deviation 수: 18
  - Flow: 5개
  - Pressure: 6개
  - Temperature: 7개
[SUCCESS] JSON 저장 완료: C:/Users/B/Desktop/HAZOP 자동화/GPT4o/Agent4_node1.json
[SUCCESS] 텍스트 저장 완료: C:/Users/B/Desktop/HAZOP 자동화/GPT4o/Agent4.txt

==========================================================
확률 분석 시작 (각 deviation의 발생 가능성 평가)
==========================================================
[INFO] 확률 평가 결과: 7, 5, 8, 3, 9, 6, 4, 7, 5, 8, 6, 7, 5, 9, 4, 6, 7, 5
[SUCCESS] 확률 정보가 추가된 JSON 저장 완료

[INFO] 그래프 생성 중...
[SUCCESS] 확률 그래프 저장: C:/Users/B/Desktop/HAZOP 자동화/GPT4o/Agent4_node1_probability_graph.png

==========================================================
확률 분석 통계
==========================================================
평균 발생 가능성 점수: 6.39/10
최고 위험 deviation: 압력 증가 (High Pressure / Overpressure) (점수: 9)
최저 위험 deviation: 조성 변화 일부 (Part of Composition) (점수: 3)

고위험 Deviations (점수 7 이상): 6개
  - [9점] 압력 증가 (High Pressure / Overpressure)
  - [8점] 유량 증가 (High Flow)
  - [8점] 온도 상승 (High Temperature)
  - [7점] 유량 없음 (No Flow)
  - [7점] 압력 저하 (Low Pressure)
  - [7점] 온도 저하 (Low Temperature)

[INFO] Agent 4 완료 (Node 1)
```

---

## 📂 파일 변경 내역

### 1. `config.py`
```python
# 추가된 설정
CSV_SCENARIOS_PATH = os.getenv('CSV_SCENARIOS_PATH',
    'C:/Users/B/Desktop/HAZOP 자동화/참고문헌/수정 엑셀/Heat_Transfer_Equipment.csv')
DEVIATION_OUTPUT_DIR = os.getenv('DEVIATION_OUTPUT_DIR',
    os.path.join(BASE_DIRECTORY, '이탈시나리오'))
DEVIATION_IMAGE_PATH = os.getenv('DEVIATION_IMAGE_PATH', DEFAULT_IMAGE)
```

### 2. `GPT4o CreateDeviation (Agent4).py`
- **추가**: pandas, matplotlib import
- **추가**: Agent2 결과 읽기 (노드 정보)
- **추가**: CSV 데이터베이스 로드 로직
- **개선**: System Prompt (구체성 강조)
- **개선**: User Prompt (CSV scenarios 포함)
- **추가**: 품질 검증 로직
- **추가**: 확률 평가 API 호출 (2차 GPT-4o 호출) 🆕
- **추가**: Matplotlib 그래프 생성 (Bar + Cumulative plot) 🆕
- **추가**: 통계 분석 및 고위험 deviation 자동 추출 🆕

---

## 🎓 참고: CSV 데이터베이스 확장

다른 장비 유형의 CSV도 사용 가능:
- `Heat_Transfer_Equipment.csv` (현재 사용 중)
- `Dryers.csv`
- `Vessels.csv`
- 커스텀 CSV (동일 포맷으로 작성)

**여러 CSV 사용 방법**:
장비 유형별로 다른 CSV를 자동 선택하려면 Agent 4에 로직 추가:

```python
# 예시: 노드 이름에 따라 CSV 선택
if "제습" in node_name:
    csv_path = "Dryers.csv"
elif "열교환" in node_name:
    csv_path = "Heat_Transfer_Equipment.csv"
else:
    csv_path = config.CSV_SCENARIOS_PATH
```

---

## ⚠️ 주의사항

1. **CSV 파일 필수 아님**: CSV가 없어도 기본 모드로 작동
2. **CSV 형식 준수**: 컬럼명이 정확해야 함 (Operational Deviations, Failure Scenarios 등)
3. **UTF-8 인코딩**: CSV 파일은 UTF-8로 저장 권장
4. **토큰 제한**: CSV가 너무 크면 프롬프트가 길어짐 (필요시 필터링)

---

## 🔗 관련 파일

- `config.py`: CSV 경로 설정
- `GPT4o CreateDeviation (Agent4).py`: 개선된 Agent 4
- `Heat_Transfer_Equipment.csv`: 기본 CSV 데이터베이스
- `main_integrated_all_nodes.py`: 통합 실행 스크립트

---

## 📝 버전 히스토리

### v3 (현재) 🆕
- **확률 기반 위험도 평가**: 각 deviation의 발생 가능성 1-10 점수화
- **그래프 시각화**: Bar plot + Cumulative probability plot
- **고위험 deviation 자동 추출**: 점수 7 이상 자동 필터링
- **통계 분석**: 평균, 최고/최저 위험 deviation 표시
- **JSON 확장**: probability_score 필드 추가

### v2
- CSV 데이터베이스 통합
- 프롬프트 품질 강화
- Agent2 정보 활용
- 품질 검증 추가

### v1 (기존)
- 기본 deviation 생성
- 간단한 설명만 제공

---

## 💡 향후 개선 방향

1. **다중 CSV 지원**: 장비 유형별 자동 선택
2. **시나리오 매칭**: AI가 유사한 CSV 시나리오를 자동으로 찾아 매칭
3. **학습 데이터베이스**: 과거 HAZOP 결과를 CSV로 누적하여 품질 향상
4. **안전장치 자동 제안**: CSV의 Safeguards 정보를 Agent 5에 전달

---

**문의**: 문제 발생 시 콘솔 출력의 `[WARNING]` 및 `[ERROR]` 메시지 확인
