# -*- coding: utf-8 -*-
"""
Agent 3: 특정 노드의 공정 변수 식별 (개선 버전)
"""
import json
import os

# 공통 유틸리티 및 설정
from config import config
from hazop_utils import (
    encode_image,
    read_txt,
    call_openai_api,
    create_vision_payload,
    write_txt,
    get_output_path
)

# 환경변수에서 대상 노드 번호 읽기 (기본값: 1)
target_node = int(os.getenv('TARGET_NODE', '1'))

# 이전 결과 읽기
agent2_result = read_txt(get_output_path('Agent2.txt'))

# Agent2 JSON 파싱하여 특정 노드 정보 추출
try:
    if "```json" in agent2_result:
        json_str = agent2_result.split("```json")[1].split("```")[0].strip()
    else:
        json_str = agent2_result

    agent2_data = json.loads(json_str)
    nodes = agent2_data.get('nodes', [])

    # 해당 노드 찾기
    target_node_data = None
    for node in nodes:
        if node.get('node_id') == target_node:
            target_node_data = node
            break

    if not target_node_data:
        print(f"[ERROR] Node {target_node}을 찾을 수 없습니다.")
        exit(1)

except Exception as e:
    print(f"[ERROR] Agent2 결과 파싱 실패: {e}")
    exit(1)

# 이미지 준비
image_path = config.DEFAULT_IMAGE
base64_image = encode_image(image_path)

# System Prompt
system_prompt = """당신은 HAZOP 공정변수 식별 전문가입니다.
특정 노드에서 의미있는 deviation을 발생시킬 수 있는 공정 변수를 선택합니다.

## 변수 선택 원칙
1. **실제 변화 가능성**: 해당 노드에서 실제로 변할 수 있는 변수
2. **영향도**: 변화 시 공정이나 안전에 영향을 주는 변수
3. **측정/제어 가능**: 계측이나 제어가 가능한 변수 우선
4. **HAZOP 효율성**: 너무 많으면 비효율적 (5-7개가 적절)

## 특정 변수 (Specific Parameters)
- **Flow**: 유체 흐름이 있는 경우
- **Pressure**: 압력이 중요한 경우
- **Temperature**: 온도 변화가 중요한 경우
- **Level**: 액체 레벨이 있는 경우
- **Composition**: 혼합물 조성이 중요한 경우
- **Phase**: 상변화가 일어나는 경우
- **Viscosity**: 점도가 중요한 경우

## 일반 변수 (General Parameters)
- **Reaction**: 화학반응이 있는 경우만
- **Mixing**: 혼합이 중요한 경우만
- **Corrosion/Erosion**: 부식성 물질이 있는 경우
- **Maintenance**: 모든 노드 적용 가능 (우선순위 낮음)
"""

# User Prompt
input_ = f"""
Node {target_node}에 대해 적용 가능한 공정 변수를 선택하세요.

## 노드 정보
- 노드명: {target_node_data.get('node_name')}
- 목적: {target_node_data.get('design_intent')}
- 장비: {', '.join(target_node_data.get('equipment_tags', []))}
- 계기: {', '.join(target_node_data.get('instrument_tags', []))}

## 공정 개요
{config.HAZOP_OBJECT}

## 분석 방법
1. 노드의 장비와 계기를 보고 어떤 공정이 일어나는지 파악
2. 각 변수가 이 노드에서 의미있는지 판단
3. 계측기(PI, TI, FI 등)가 있으면 해당 변수는 중요함

## JSON 출력 형식

{{
  "node_id": {target_node},
  "node_name": "{target_node_data.get('node_name')}",
  "applicable_parameters": [
    {{
      "parameter": "Flow",
      "applicable": true,
      "reason": "FI-1101 유량계가 있어 유량 제어가 중요함"
    }},
    {{
      "parameter": "Viscosity",
      "applicable": false,
      "reason": "기체이므로 점도는 중요하지 않음"
    }}
  ],
  "selected_parameters": ["Flow", "Pressure", "Temperature"],
  "total_count": 0
}}

## 주의
- 계측기가 있으면 해당 변수는 거의 확실히 적용됨
- 너무 많이 선택하면 HAZOP이 비효율적 (5-7개 적절)
- 불필요한 변수는 제외

P&ID와 노드 정보를 보고 적용 가능한 변수를 JSON으로 출력하세요.
"""

# API 호출
print(f"[INFO] Agent 3 실행 중: Node {target_node} 공정변수 식별...")
print(f"[INFO] 대상 노드: {target_node_data.get('node_name')}")

payload = create_vision_payload(system_prompt, input_, base64_image)
content = call_openai_api(payload)

# 응답 출력
print("\n" + "="*60)
print(f"Agent 3 분석 결과 (Node {target_node})")
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

    selected = parsed_json.get("selected_parameters", [])
    print(f"\n[VALIDATION] JSON 파싱 성공")
    print(f"[VALIDATION] 선택된 변수 수: {len(selected)}")
    print(f"[VALIDATION] 선택된 변수: {', '.join(selected)}")

    if len(selected) < 3:
        print(f"[WARNING] 변수가 너무 적습니다 ({len(selected)}개)")
    elif len(selected) > 10:
        print(f"[WARNING] 변수가 너무 많습니다 ({len(selected)}개)")

    # 저장
    json_path = get_output_path(f"Agent3_node{target_node}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_json, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] JSON 저장 완료: {json_path}")

except json.JSONDecodeError as e:
    print(f"[ERROR] JSON 파싱 실패: {e}")

# 텍스트 저장
file_path = get_output_path("Agent3.txt")
write_txt(file_path, content)
print(f"[SUCCESS] 텍스트 저장 완료: {file_path}")

print(f"\n[INFO] Agent 3 완료 (Node {target_node})")