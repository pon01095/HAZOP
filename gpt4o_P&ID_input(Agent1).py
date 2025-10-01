# -*- coding: utf-8 -*-
"""
Agent 1: P&ID 도면에서 공정 구성요소 식별 (개선 버전)
HAZOP 분석에 필요한 모든 공정 구성요소를 체계적으로 식별합니다.
"""
import json

# 공통 유틸리티 및 설정
from config import config
from hazop_utils import (
    encode_image,
    call_openai_api,
    create_vision_payload,
    write_txt,
    get_output_path
)

# 이미지 준비
image_path = config.DEFAULT_IMAGE
base64_image = encode_image(image_path)

# System Prompt - 전문가 역할 및 프레임워크 정의
system_prompt = """당신은 P&ID(Piping and Instrumentation Diagram) 도면 분석 전문가입니다.
도면에서 **보이는 장비 태그와 계기 기호**를 정확하게 식별하는 것이 목표입니다.

## 목표
P&ID 도면에서 태그 번호가 표시된 모든 장비와 계기를 찾아서 목록화

## 식별 대상 (우선순위)

### 1. 주요 공정 장비 (대문자 태그)
- 탱크/용기: V-101, D-201 등
- 펌프: P-101, P-102 등
- 압축기/블로워: C-101, B-101 등
- 열교환기: E-101, HX-201 등
- 필터/흡착기: F-101, A-101 등
- 멤브레인: M-101 등

### 2. 안전 장치
- PSV (압력안전밸브): PSV-101
- 파열판: RD-101
- 긴급차단밸브: ESD-101

### 3. 계측기 (2-3글자 조합)
- 압력: PI-101, PT-102, PG-103
- 온도: TI-101, TE-102, TT-103
- 유량: FI-101, FE-102, FT-103
- 레벨: LI-101, LT-102, LG-103
- 분석: AI-101 (가스분석기 등)

### 4. 제어밸브 및 주요 밸브
- 제어밸브: FCV-101, PCV-102, TCV-103
- 차단밸브: V-101 (태그 있는 경우만)
- 체크밸브: CV-101 (태그 있는 경우만)

## 수집 정보 (도면에서 확인 가능한 것만)
- **태그 번호**: 반드시 정확하게 (도면에 표시된 그대로)
- **장비 유형**: 기호로 판단 (Vessel, Pump, Valve 등)
- **대략적 위치**: 공정 흐름 상의 위치 (입구쪽/중간/출구쪽)
- **연결관계**: 바로 앞/뒤 장비 태그 (화살표 방향)

## 제외 사항
❌ 도면에 없는 운전조건 (압력, 온도, 유량 수치) - 추측하지 말것
❌ 상세한 기능 설명 - 간단히만
❌ 태그가 없는 소형 밸브/배관 부속

## 중요
✅ 도면에 **실제로 보이는 태그**만 기록
✅ 불명확하면 "TAG-XXX (확인필요)" 형식으로 표시
✅ 빠뜨리는 것보다 불명확해도 일단 기록하는 것이 중요
"""

# User Prompt - 구체적 지시사항
input_ = f"""
첨부된 P&ID 도면 이미지를 분석하여 **모든 장비 태그와 계기 태그**를 찾아서 JSON으로 출력하세요.

## 공정 개요
{config.HAZOP_OBJECT}

## 작업 순서
1. 도면 전체를 스캔하여 태그 번호가 있는 모든 장비 찾기
2. 장비 기호를 보고 유형 판단
3. 모든 계측기 태그 찾기
4. 장비 간 연결 흐름 파악

## JSON 출력 형식 (필수 필드만)

{{
  "equipment_list": [
    {{
      "tag": "장비 태그 번호",
      "type": "장비 유형",
      "location": "공정상 위치"
    }}
  ],
  "instrument_list": [
    {{
      "tag": "계기 태그 번호",
      "type": "계기 유형",
      "measured_equipment": "측정 대상"
    }}
  ],
  "total_count": {{
    "equipment": 0,
    "instruments": 0
  }}
}}

## 중요
- 도면에 실제로 보이는 태그만 기록
- 불명확한 태그는 "확인필요"로 표시
- 모든 태그를 빠뜨리지 말고 기록

P&ID 이미지를 분석하여 JSON으로 출력하세요.
"""

# API 호출
print("[INFO] Agent 1 실행 중: P&ID 구성요소 식별...")
print(f"[INFO] 분석 대상: {config.HAZOP_OBJECT}")

payload = create_vision_payload(system_prompt, input_, base64_image, max_tokens=8000)
content = call_openai_api(payload, timeout=180)

# 응답 출력
print("\n" + "="*60)
print("Agent 1 분석 결과")
print("="*60)
print(content)

# JSON 검증
try:
    # JSON 추출 (마크다운 코드 블록 제거)
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content

    parsed_json = json.loads(json_str)

    # 기본 검증
    equipment_count = len(parsed_json.get("equipment_list", []))
    print(f"\n[VALIDATION] JSON 파싱 성공")
    print(f"[VALIDATION] 식별된 장비 수: {equipment_count}")

    if equipment_count < 5:
        print(f"[WARNING] 장비가 너무 적습니다 ({equipment_count}개). 누락 확인 필요")

    # 안전 Critical 장비 확인
    safety_critical = [eq for eq in parsed_json.get("equipment_list", [])
                       if eq.get("safety_criticality") == "High"]
    print(f"[VALIDATION] 안전 Critical 장비: {len(safety_critical)}개")

    # 저장 (JSON과 텍스트 모두)
    json_path = get_output_path("공정요소.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_json, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] JSON 저장 완료: {json_path}")

except json.JSONDecodeError as e:
    print(f"[ERROR] JSON 파싱 실패: {e}")
    print(f"[ERROR] LLM 출력을 텍스트로만 저장합니다.")

# 결과 저장 (텍스트 버전 - 하위 호환성)
file_path = get_output_path("공정요소.txt")
write_txt(file_path, content)
print(f"[SUCCESS] 텍스트 저장 완료: {file_path}")

print("\n[INFO] Agent 1 완료")