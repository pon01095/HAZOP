# -*- coding: utf-8 -*-
"""
Agent 2: 공정을 HAZOP 노드별로 분리 (개선 버전)
"""
import json

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

# 이전 결과 읽기
answer_before = read_txt(get_output_path('공정요소.txt'))

# 이미지 준비
image_path = config.DEFAULT_IMAGE
base64_image = encode_image(image_path)

# System Prompt
system_prompt = """당신은 HAZOP 노드 분리 전문가입니다.
공정을 기능별로 논리적인 HAZOP 노드로 나누는 것이 목표입니다.

## HAZOP 노드 분리 원칙
1. **기능적 독립성**: 각 노드는 명확한 공정 목적을 가져야 함
2. **적절한 크기**: 너무 크거나 작지 않게 (노드당 5-20개 deviation 발생 예상)
3. **경계 명확성**: 노드 간 입출력이 명확해야 함
4. **공정 단계별**: 주요 공정 변화 지점에서 분리

## 노드 분리 기준
- 주요 장비 단위 (압축기, 제습기, 분리막 등)
- 압력/온도 레벨 변화
- 공정 목적 변화 (압축 → 제습 → 분리)
- 물리적 상태 변화

## 주의사항
- 한 장비를 한 노드로 하면 너무 작음
- 전체를 한 노드로 하면 너무 큼
- 3-7개 노드가 적절
"""

# User Prompt
input_ = f"""
P&ID 도면과 Agent1의 장비 목록을 참고하여 공정을 HAZOP 노드로 분리하세요.

## 공정 개요
{config.HAZOP_OBJECT}

## Agent1에서 식별한 장비 목록
{answer_before}

## JSON 출력 형식

{{
  "nodes": [
    {{
      "node_id": 1,
      "node_name": "노드명",
      "design_intent": "이 노드의 공정 목적",
      "equipment_tags": ["B-1101", "D-1101"],
      "instrument_tags": ["PI-1101", "TI-1102"],
      "boundary": {{
        "inlet": "입구 지점",
        "outlet": "출구 지점"
      }}
    }}
  ],
  "total_nodes": 0
}}

## 지침
- 공정 흐름을 따라 순서대로 노드 번호 부여
- 각 노드는 명확한 기능을 가져야 함
- 모든 장비가 어느 한 노드에 포함되어야 함

P&ID 이미지와 장비 목록을 보고 노드를 분리하여 JSON으로 출력하세요.
"""

# API 호출
print("[INFO] Agent 2 실행 중: HAZOP 노드 분리...")
print(f"[INFO] 분석 대상: {config.HAZOP_OBJECT}")

payload = create_vision_payload(system_prompt, input_, base64_image)
content = call_openai_api(payload)

# 응답 출력
print("\n" + "="*60)
print("Agent 2 분석 결과")
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

    node_count = len(parsed_json.get("nodes", []))
    print(f"\n[VALIDATION] JSON 파싱 성공")
    print(f"[VALIDATION] 식별된 노드 수: {node_count}")

    if node_count < 2:
        print(f"[WARNING] 노드가 너무 적습니다 ({node_count}개)")
    elif node_count > 10:
        print(f"[WARNING] 노드가 너무 많습니다 ({node_count}개)")

    # 저장
    json_path = get_output_path("Agent2.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_json, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] JSON 저장 완료: {json_path}")

except json.JSONDecodeError as e:
    print(f"[ERROR] JSON 파싱 실패: {e}")

# 텍스트 저장
file_path = get_output_path("Agent2.txt")
write_txt(file_path, content)
print(f"[SUCCESS] 텍스트 저장 완료: {file_path}")

print("\n[INFO] Agent 2 완료")