# -*- coding: utf-8 -*-
"""
Agent 5: 이탈에 대한 원인, 결과, 안전장치 분석 (개선 버전)
"""

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
import json
import os

# 환경변수에서 대상 노드 번호 읽기 (기본값: 1)
target_node = int(os.getenv('TARGET_NODE', '1'))

# Agent2 결과 읽기 (노드 정보)
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

# Agent4 결과 읽기 (deviation 정보)
agent4_result = read_txt(get_output_path(f'Agent4_node{target_node}.json'))
try:
    agent4_data = json.loads(agent4_result)
    deviations = agent4_data.get('deviations', [])
    if not deviations:
        print(f"[ERROR] Agent4 결과에서 deviation을 찾을 수 없습니다.")
        exit(1)
    print(f"[INFO] 분석할 deviation 수: {len(deviations)}")
except Exception as e:
    print(f"[ERROR] Agent4 JSON 파싱 실패: {e}")
    exit(1)

# 이미지 준비
image_path = config.DEFAULT_IMAGE
base64_image = encode_image(image_path)

# System Prompt
system_prompt = """당신은 HAZOP 안전 분석 전문가입니다.
각 deviation에 대해 원인(Cause), 결과(Consequence), 안전장치(Safeguard), 개선사항(Recommendation)을 분석합니다.

## 분석 항목
1. **원인(Cause)**: 이탈이 발생하는 근본 원인 (장비 고장, 운전 오류, 설계 결함 등)
2. **결과(Consequence)**: 이탈로 인한 영향 (안전, 환경, 생산성 등)
3. **안전장치(Safeguard)**: P&ID에서 식별된 기존 보호 장치 (알람, 인터록, 릴리프밸브 등)
4. **개선사항(Recommendation)**: 추가 필요한 안전 조치

## 분석 원칙
- **구체성**: 일반적인 표현보다 구체적인 원인/결과 기술
- **P&ID 기반**: 도면에 표시된 계기와 안전장치를 반드시 확인
- **현실성**: 실제 발생 가능한 시나리오 중심
- **우선순위**: 심각도가 높은 항목 우선 기술

## P&ID 안전장치 식별
- **PI, TI, FI**: 측정 계기 (알람 기능 가능)
- **PC, TC, FC**: 제어 계기 (자동 제어)
- **PSV, PRV**: 압력 릴리프 밸브
- **XV**: 차단 밸브 (긴급 차단)
- **AI**: 분석 계기 (조성 모니터링)

## 심각도 평가 기준
- **High**: 인명 피해, 환경 오염, 설비 파손
- **Medium**: 생산 중단, 품질 저하
- **Low**: 경미한 운전 이상
"""

# User Prompt
user_text = f"""
다음 deviation에 대해 원인, 결과, 안전장치, 개선사항을 분석하세요.

## 노드 정보
- Node {target_node}: {target_node_data.get('node_name')}
- 목적: {target_node_data.get('design_intent')}
- 장비: {', '.join(target_node_data.get('equipment_tags', []))}
- 계기: {', '.join(target_node_data.get('instrument_tags', []))}

## Deviation 목록
{json.dumps(deviations, ensure_ascii=False, indent=2)}

## JSON 출력 형식

{{
  "node_id": {target_node},
  "node_name": "{target_node_data.get('node_name')}",
  "hazop_analysis": [
    {{
      "deviation_id": 1,
      "parameter": "Flow",
      "guideword": "None",
      "deviation": "유량 없음 (No Flow)",
      "causes": [
        "가스 공급원 차단",
        "배관 완전 막힘",
        "압축기 정지"
      ],
      "consequences": [
        "공정 중단으로 인한 생산 손실",
        "하류 공정의 압력 강하"
      ],
      "severity": "Medium",
      "safeguards": [
        "FI-1101 (유량 저 알람)",
        "PI-1101 (압력 감시)"
      ],
      "recommendations": [
        "유량 저저 인터록 추가",
        "압축기 자동 재시작 로직 검토"
      ]
    }}
  ]
}}

## 주의사항
1. P&ID를 보고 실제 존재하는 안전장치만 기재
2. 각 deviation의 심각도를 High/Medium/Low로 평가
3. causes와 consequences는 각각 2-3개씩 구체적으로 작성
4. safeguards는 P&ID의 계기 태그와 함께 기재
5. recommendations는 실용적이고 구현 가능한 개선사항

모든 deviation에 대해 분석 결과를 JSON으로 출력하세요.
"""

# API 호출
print(f"[INFO] Agent 5 실행 중: Node {target_node} 안전 분석...")
payload = create_vision_payload(system_prompt, user_text, base64_image, image_format="png")
content = call_openai_api(payload)

# 응답 출력
print("\n" + "="*60)
print(f"Agent 5 분석 결과 (Node {target_node})")
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

    hazop_analysis = parsed_json.get("hazop_analysis", [])
    print(f"\n[VALIDATION] JSON 파싱 성공")
    print(f"[VALIDATION] 분석 완료된 deviation 수: {len(hazop_analysis)}")

    # 심각도별 통계
    severity_count = {"High": 0, "Medium": 0, "Low": 0}
    for analysis in hazop_analysis:
        severity = analysis.get('severity', 'Unknown')
        if severity in severity_count:
            severity_count[severity] += 1

    print(f"[VALIDATION] 심각도별 분포:")
    for severity, count in severity_count.items():
        if count > 0:
            print(f"  - {severity}: {count}개")

    # JSON 저장
    json_path = get_output_path(f"Agent5_node{target_node}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_json, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] JSON 저장 완료: {json_path}")

except json.JSONDecodeError as e:
    print(f"[ERROR] JSON 파싱 실패: {e}")

# 텍스트 저장
file_path = get_output_path("Agent5.txt")
write_txt(file_path, content)
print(f"[SUCCESS] 텍스트 저장 완료: {file_path}")

print(f"\n[INFO] Agent 5 완료 (Node {target_node})")