# -*- coding: utf-8 -*-
"""
Agent 4: 공정 변수와 가이드워드를 결합하여 이탈 시나리오 생성 (개선 버전 v3)
CSV 데이터베이스의 전문 failure scenarios를 참고하여 고품질 deviation 생성
+ 확률 기반 분석 및 시각화 기능 추가
"""

# 공통 유틸리티 및 설정
from config import config
from hazop_utils import (
    read_txt,
    call_openai_api,
    create_text_payload,
    write_txt,
    get_output_path
)
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI 없이 그래프 생성
import requests
import math

# 환경변수에서 대상 노드 번호 읽기 (기본값: 1)
target_node = int(os.getenv('TARGET_NODE', '1'))

# Agent2 결과 읽기 (노드 정보 필요)
agent2_result = read_txt(get_output_path('Agent2.txt'))
try:
    if "```json" in agent2_result:
        json_str = agent2_result.split("```json")[1].split("```")[0].strip()
    else:
        json_str = agent2_result
    agent2_data = json.loads(json_str)
    nodes = agent2_data.get('nodes', [])
    target_node_data = None
    for node in nodes:
        if node.get('node_id') == target_node:
            target_node_data = node
            break
    if not target_node_data:
        print(f"[ERROR] Node {target_node}을 찾을 수 없습니다.")
        exit(1)
except Exception as e:
    print(f"[ERROR] Agent2 JSON 파싱 실패: {e}")
    exit(1)

# Agent3 결과 읽기 (JSON 형식)
agent3_result = read_txt(get_output_path(f'Agent3_node{target_node}.json'))

# Agent3 JSON 파싱
try:
    agent3_data = json.loads(agent3_result)
    node_name = agent3_data.get('node_name', '')
    parameters = agent3_data.get('selected_parameters', [])

    if not parameters:
        print(f"[ERROR] Agent3 결과에서 선택된 변수를 찾을 수 없습니다.")
        exit(1)

    print(f"[INFO] 노드: {node_name}")
    print(f"[INFO] 선택된 변수: {', '.join(parameters)}")

except Exception as e:
    print(f"[ERROR] Agent3 JSON 파싱 실패: {e}")
    exit(1)

# CSV 데이터베이스 로드 (전문 failure scenarios)
csv_scenarios = ""
try:
    csv_path = config.CSV_SCENARIOS_PATH
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"[INFO] CSV 데이터베이스 로드: {len(df)}개 시나리오")

        # CSV 데이터를 텍스트로 변환 (LLM이 참고할 수 있도록)
        csv_scenarios = "\n\n## 전문 Failure Scenarios 데이터베이스 (참고용)\n\n"
        for idx, row in df.iterrows():
            csv_scenarios += f"**{row['Operational Deviations']}**\n"
            csv_scenarios += f"- Scenario: {row['Failure Scenarios']}\n"
            if pd.notna(row.get('Inherently Safer/Passive')):
                csv_scenarios += f"- Safeguards: {row['Inherently Safer/Passive']}\n"
            csv_scenarios += "\n"
    else:
        print(f"[WARNING] CSV 파일을 찾을 수 없습니다: {csv_path}")
        print(f"[WARNING] 기본 deviation 생성 모드로 진행합니다.")
except Exception as e:
    print(f"[WARNING] CSV 로드 실패: {e}")
    print(f"[WARNING] 기본 deviation 생성 모드로 진행합니다.")

# 가이드워드 정의
guidewords = ['None', 'More', 'Less', 'As well as', 'Other than', 'Part of', 'Reverse']

# System Prompt (개선됨)
system_prompt = """당신은 HAZOP deviation 시나리오 생성 전문가입니다.
공정 변수와 가이드워드를 결합하여 구체적이고 현실적인 이탈 시나리오를 생성합니다.

## 가이드워드 의미
- **None**: 의도된 결과가 발생하지 않음 (완전 중단)
- **More**: 양적 증가 (유량↑, 압력↑, 온도↑ 등)
- **Less**: 양적 감소 (유량↓, 압력↓, 온도↓ 등)
- **As well as**: 의도된 결과 + 추가적인 활동/물질
- **Other than**: 의도와 완전히 다른 결과
- **Part of**: 의도된 결과의 일부만 발생
- **Reverse**: 의도와 반대 방향

## 이탈 작성 원칙 (중요!)
1. **구체성**: 막연한 표현 대신 명확한 현상 기술
   - 나쁜 예: "압력이 증가함"
   - 좋은 예: "압축기 과부하로 토출 압력이 0.3 bar.g에서 0.5 bar.g로 상승"

2. **현실성**: 실제 발생 가능한 시나리오
   - 설비 고장, 밸브 오작동, 제어 실패 등 구체적 원인 언급

3. **기술성**: 공학적 용어와 장비 태그 사용
   - 노드의 장비 태그를 활용 (예: "BL-1101 블로워", "D-1101 제습장치")

4. **전문성**: 제공된 Failure Scenarios 데이터베이스를 참고하여 산업 표준 수준의 설명 작성
   - 유사한 deviation type을 데이터베이스에서 찾아 표현 방식 참고
   - 실무에서 사용되는 전문 용어 활용

## 출력 형식
각 변수별로 적용 가능한 가이드워드만 선택하여 이탈을 생성합니다.
- 적용 불가능한 가이드워드는 제외
- 각 이탈은 "가이드워드 + 변수" 형태로 간결하게 표현
- description은 2-3문장으로 구체적인 시나리오 작성
"""

# User Prompt (개선됨)
user_text = f"""
다음 공정 변수들에 대해 전문가 수준의 HAZOP deviation을 생성하세요.

## 노드 정보
- Node {target_node}: {node_name}
- 설계 의도: {target_node_data.get('design_intent', '')}
- 장비: {', '.join(target_node_data.get('equipment_tags', []))}
- 계기: {', '.join(target_node_data.get('instrument_tags', []))}

## 공정 개요
{config.HAZOP_OBJECT}

## 공정 변수
{', '.join(parameters)}

## 가이드워드
{', '.join(guidewords)}

{csv_scenarios}

## JSON 출력 형식

{{
  "node_id": {target_node},
  "node_name": "{node_name}",
  "deviations": [
    {{
      "parameter": "Flow",
      "guideword": "None",
      "deviation": "유량 없음 (No Flow)",
      "description": "가스 공급원 차단 또는 BL-1101 블로워 정지로 인한 유량 완전 차단. 하류 공정 중단 및 압력 강하 발생"
    }},
    {{
      "parameter": "Pressure",
      "guideword": "More",
      "deviation": "압력 증가 (High Pressure / Overpressure)",
      "description": "하류 밸브 폐쇄 또는 D-1101 제습장치 출구 막힘으로 인해 설계 압력 0.3 bar.g 초과. 배관 및 장비 과압으로 안전밸브 작동 가능"
    }}
  ]
}}

## 주의사항
1. 각 변수에 대해 가능한 모든 가이드워드 조합을 검토
2. 적용 불가능한 조합은 제외 (예: Reverse Flow가 물리적으로 불가능한 경우)
3. deviation은 영문 표준 용어 포함 (예: No Flow, High Pressure, Overpressure)
4. description은 **반드시 구체적인 원인과 결과를 포함**:
   - 어떤 장비 고장/오작동으로 인해 (원인)
   - 어떤 현상이 발생하고 (현상)
   - 어떤 영향이 있는지 (결과)
5. 제공된 전문 Failure Scenarios를 참고하여 산업 표준 수준으로 작성
6. 노드의 장비 태그를 적극 활용

모든 변수에 대해 가능한 deviation을 JSON으로 출력하세요.
"""

# API 호출
print(f"[INFO] Agent 4 실행 중: Node {target_node} deviation 생성...")
print(f"[INFO] CSV 데이터베이스 참조 모드: {'활성화' if csv_scenarios else '비활성화'}")
payload = create_text_payload(system_prompt, user_text)
content = call_openai_api(payload)

# 응답 출력
print("\n" + "="*60)
print(f"Agent 4 분석 결과 (Node {target_node})")
print("="*60)
print(content)

# JSON 검증
parsed_json = None
deviations = []
try:
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content

    parsed_json = json.loads(json_str)

    deviations = parsed_json.get("deviations", [])
    print(f"\n[VALIDATION] JSON 파싱 성공")
    print(f"[VALIDATION] 생성된 deviation 수: {len(deviations)}")

    # Parameter별 통계
    param_count = {}
    for dev in deviations:
        param = dev.get('parameter', 'Unknown')
        param_count[param] = param_count.get(param, 0) + 1

    for param, count in param_count.items():
        print(f"  - {param}: {count}개")

    # 품질 검증
    low_quality_count = 0
    for dev in deviations:
        desc = dev.get('description', '')
        if len(desc) < 20:  # 너무 짧은 설명
            low_quality_count += 1
            print(f"[WARNING] 짧은 설명 발견: {dev.get('deviation')}")

    if low_quality_count > 0:
        print(f"[WARNING] {low_quality_count}개의 deviation이 충분히 상세하지 않습니다.")

    # JSON 저장
    json_path = get_output_path(f"Agent4_node{target_node}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_json, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] JSON 저장 완료: {json_path}")

except json.JSONDecodeError as e:
    print(f"[ERROR] JSON 파싱 실패: {e}")

# 텍스트 저장
file_path = get_output_path("Agent4.txt")
write_txt(file_path, content)
print(f"[SUCCESS] 텍스트 저장 완료: {file_path}")

# ========== 확률 분석 및 그래프 생성 ==========
print(f"\n{'='*60}")
print(f"확률 분석 시작 (각 deviation의 발생 가능성 평가)")
print(f"{'='*60}")

if parsed_json and deviations:
    try:
        # 각 deviation에 대해 발생 가능성을 1-10 점수로 평가 요청
        probability_prompt = f"""
다음 deviation들에 대해 발생 가능성을 1-10 점수로 평가하세요.

## 노드 정보
- Node {target_node}: {node_name}
- 장비: {', '.join(target_node_data.get('equipment_tags', []))}

## Deviations
{json.dumps(deviations, ensure_ascii=False, indent=2)}

## 평가 기준
1-3: 발생 가능성 매우 낮음 (극히 드문 상황)
4-6: 발생 가능성 보통 (일반적인 고장 상황)
7-10: 발생 가능성 높음 (흔한 고장, 운전 오류)

각 deviation에 대해 순서대로 1-10 사이의 숫자 하나만 출력하세요.
예시 출력: 7, 5, 8, 3, 9, 6, 4

{len(deviations)}개의 숫자를 쉼표로 구분하여 출력하세요.
"""

        # 확률 평가 API 호출
        prob_payload = {
            "model": config.MODEL_NAME,
            "messages": [
                {"role": "system", "content": "당신은 HAZOP 전문가로서 deviation의 발생 가능성을 평가합니다."},
                {"role": "user", "content": probability_prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.3  # 일관성을 위해 낮은 온도
        }

        headers = config.API_HEADERS
        prob_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=prob_payload,
            timeout=config.API_TIMEOUT
        )
        prob_response.raise_for_status()
        prob_content = prob_response.json()['choices'][0]['message']['content']

        print(f"[INFO] 확률 평가 결과: {prob_content}")

        # 숫자 추출
        import re
        numbers = re.findall(r'\d+', prob_content)
        probabilities = [int(n) for n in numbers if 1 <= int(n) <= 10]

        if len(probabilities) != len(deviations):
            print(f"[WARNING] 확률 개수 불일치: 기대 {len(deviations)}개, 실제 {len(probabilities)}개")
            # 부족하면 평균값(5)로 채우기
            while len(probabilities) < len(deviations):
                probabilities.append(5)
            # 초과하면 자르기
            probabilities = probabilities[:len(deviations)]

        # Deviation에 확률 추가
        for i, dev in enumerate(deviations):
            dev['probability_score'] = probabilities[i]

        # 확률 점수를 JSON에 추가하여 다시 저장
        parsed_json['deviations'] = deviations
        json_path = get_output_path(f"Agent4_node{target_node}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] 확률 정보가 추가된 JSON 저장 완료")

        # ========== 그래프 생성 ==========
        print(f"\n[INFO] 그래프 생성 중...")

        # 한글 폰트 설정 (Windows)
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False

        # 그래프 데이터 준비
        deviation_labels = [f"{i+1}. {dev['deviation'][:30]}..." if len(dev['deviation']) > 30
                           else f"{i+1}. {dev['deviation']}"
                           for i, dev in enumerate(deviations)]
        prob_scores = [dev['probability_score'] for dev in deviations]

        # 누적 확률 계산 (정규화)
        total_score = sum(prob_scores)
        normalized_probs = [score / total_score for score in prob_scores]
        cumulative_probs = []
        current_sum = 0
        for prob in normalized_probs:
            current_sum += prob
            cumulative_probs.append(current_sum)

        # Figure 생성
        fig, ax1 = plt.subplots(figsize=(14, 8), dpi=300)

        # Bar plot (발생 가능성 점수)
        color_primary = '#3776ab'
        x_pos = range(len(deviation_labels))
        ax1.set_xlabel('Deviation Number', fontsize=12)
        ax1.set_ylabel('Probability Score (1-10)', color=color_primary, fontsize=12)
        bars = ax1.bar(x_pos, prob_scores, color=color_primary, alpha=0.7)
        ax1.tick_params(axis='y', labelcolor=color_primary)
        ax1.set_ylim(0, 10)
        ax1.grid(axis='y', alpha=0.3)

        # 막대 위에 점수 표시
        for i, (bar, score) in enumerate(zip(bars, prob_scores)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{score}',
                    ha='center', va='bottom', fontsize=9)

        # Cumulative probability (누적 확률)
        ax2 = ax1.twinx()
        color_secondary = '#ab373b'
        ax2.set_ylabel('Cumulative Probability', color=color_secondary, fontsize=12)
        ax2.plot(x_pos, cumulative_probs, color=color_secondary, marker='o', linewidth=2, markersize=6)
        ax2.tick_params(axis='y', labelcolor=color_secondary)
        ax2.set_ylim(0, 1.0)

        # 제목 및 레이블
        plt.title(f'Deviation Probability Analysis - Node {target_node}: {node_name}',
                 fontsize=14, fontweight='bold', pad=20)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels([str(i+1) for i in x_pos], rotation=0)

        # 범례
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color=color_primary, lw=4, label='Probability Score'),
            Line2D([0], [0], color=color_secondary, lw=4, label='Cumulative Probability')
        ]
        ax1.legend(handles=legend_elements, loc='upper left', fontsize=10)

        fig.tight_layout()

        # 그래프 저장
        graph_path = get_output_path(f"Agent4_node{target_node}_probability_graph.png")
        plt.savefig(graph_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[SUCCESS] 확률 그래프 저장: {graph_path}")

        # 통계 출력
        print(f"\n{'='*60}")
        print(f"확률 분석 통계")
        print(f"{'='*60}")
        print(f"평균 발생 가능성 점수: {sum(prob_scores)/len(prob_scores):.2f}/10")
        print(f"최고 위험 deviation: {deviations[prob_scores.index(max(prob_scores))]['deviation']} (점수: {max(prob_scores)})")
        print(f"최저 위험 deviation: {deviations[prob_scores.index(min(prob_scores))]['deviation']} (점수: {min(prob_scores)})")

        # 고위험 deviation 목록
        high_risk = [dev for dev in deviations if dev['probability_score'] >= 7]
        if high_risk:
            print(f"\n고위험 Deviations (점수 7 이상): {len(high_risk)}개")
            for dev in high_risk:
                print(f"  - [{dev['probability_score']}점] {dev['deviation']}")

    except Exception as e:
        print(f"[WARNING] 확률 분석 실패: {e}")
        print(f"[INFO] 기본 deviation 생성은 완료되었습니다.")
        import traceback
        traceback.print_exc()

else:
    print(f"[SKIP] JSON 파싱 실패로 확률 분석을 건너뜁니다.")

print(f"\n[INFO] Agent 4 완료 (Node {target_node})")
