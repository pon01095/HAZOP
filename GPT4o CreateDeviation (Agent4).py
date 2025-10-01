# -*- coding: utf-8 -*-
"""
Agent 4: 공정 변수와 가이드워드를 결합하여 이탈 시나리오 생성 (개선 버전)
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

# 환경변수에서 대상 노드 번호 읽기 (기본값: 1)
target_node = int(os.getenv('TARGET_NODE', '1'))

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

# 가이드워드 정의
guidewords = ['None', 'More', 'Less', 'As well as', 'Other than', 'Part of', 'Reverse']

# System Prompt
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

## 이탈 작성 원칙
1. **구체성**: 막연한 표현 대신 명확한 현상 기술
2. **현실성**: 실제 발생 가능한 시나리오
3. **간결성**: 한 문장으로 핵심 표현
4. **기술성**: 공학적 용어 사용

## 출력 형식
각 변수별로 적용 가능한 가이드워드만 선택하여 이탈을 생성합니다.
- 적용 불가능한 가이드워드는 "N/A" 처리
- 각 이탈은 "가이드워드 + 변수" 형태로 간결하게 표현
"""

# User Prompt
user_text = f"""
다음 공정 변수들에 대해 HAZOP deviation을 생성하세요.

## 노드 정보
- Node {target_node}: {node_name}

## 공정 변수
{', '.join(parameters)}

## 가이드워드
{', '.join(guidewords)}

## JSON 출력 형식

{{
  "node_id": {target_node},
  "node_name": "{node_name}",
  "deviations": [
    {{
      "parameter": "Flow",
      "guideword": "None",
      "deviation": "유량 없음 (No Flow)",
      "description": "가스 공급 중단으로 인한 유량 완전 차단"
    }},
    {{
      "parameter": "Flow",
      "guideword": "More",
      "deviation": "유량 증가 (High Flow)",
      "description": "설계 유량을 초과하는 과도한 가스 공급"
    }}
  ]
}}

## 주의사항
1. 각 변수에 대해 가능한 모든 가이드워드 조합을 검토
2. 적용 불가능한 조합은 제외 (예: Reverse Flow가 물리적으로 불가능한 경우)
3. deviation은 영문 표준 용어 포함 (예: No Flow, High Pressure)
4. description은 구체적인 현상 설명

모든 변수에 대해 가능한 deviation을 JSON으로 출력하세요.
"""

# API 호출
print(f"[INFO] Agent 4 실행 중: Node {target_node} deviation 생성...")
payload = create_text_payload(system_prompt, user_text)
content = call_openai_api(payload)

# 응답 출력
print("\n" + "="*60)
print(f"Agent 4 분석 결과 (Node {target_node})")
print("="*60)
print(content)

# JSON 검증
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

print(f"\n[INFO] Agent 4 완료 (Node {target_node})")
