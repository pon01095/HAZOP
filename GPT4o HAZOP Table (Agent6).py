# -*- coding: utf-8 -*-
"""
Agent 6: 최종 HAZOP 테이블 생성 (Excel) - 개선 버전
Agent5 JSON 결과를 파싱하여 DataFrame 생성
"""
import pandas as pd
import json
import os
import glob

# 공통 유틸리티 및 설정
from config import config
from hazop_utils import (
    read_txt,
    get_output_path
)

# 환경변수에서 대상 노드 번호 읽기 (기본값: 1)
target_node = int(os.getenv('TARGET_NODE', '1'))

# Agent5 JSON 결과 파싱
def parse_agent5_json(json_data):
    """
    Agent5 JSON 출력을 파싱하여 HAZOP 테이블 데이터 추출
    """
    data = {
        '노드': [],
        '노드명': [],
        '파라미터': [],
        '가이드워드': [],
        '이탈': [],
        '원인': [],
        '결과': [],
        '심각도': [],
        '안전장치': [],
        '개선사항': []
    }

    node_id = json_data.get('node_id', 0)
    node_name = json_data.get('node_name', '')
    hazop_analysis = json_data.get('hazop_analysis', [])

    for analysis in hazop_analysis:
        data['노드'].append(f"Node {node_id}")
        data['노드명'].append(node_name)
        data['파라미터'].append(analysis.get('parameter', ''))
        data['가이드워드'].append(analysis.get('guideword', ''))
        data['이탈'].append(analysis.get('deviation', ''))

        # 리스트를 줄바꿈으로 연결
        causes = analysis.get('causes', [])
        data['원인'].append('\n'.join(f"- {c}" for c in causes))

        consequences = analysis.get('consequences', [])
        data['결과'].append('\n'.join(f"- {c}" for c in consequences))

        data['심각도'].append(analysis.get('severity', ''))

        safeguards = analysis.get('safeguards', [])
        data['안전장치'].append('\n'.join(f"- {s}" for s in safeguards))

        recommendations = analysis.get('recommendations', [])
        data['개선사항'].append('\n'.join(f"- {r}" for r in recommendations))

    return data

# 모든 노드의 Agent5 JSON 파일 찾기
print("[INFO] Agent5 JSON 파일 검색 중...")
output_dir = config.BASE_DIRECTORY
agent5_files = glob.glob(os.path.join(output_dir, 'Agent5_node*.json'))

if not agent5_files:
    print(f"[ERROR] Agent5 JSON 파일을 찾을 수 없습니다: {output_dir}")
    exit(1)

print(f"[INFO] {len(agent5_files)}개의 Agent5 JSON 파일 발견")

# 모든 노드 데이터 수집
all_data = {
    '노드': [],
    '노드명': [],
    '파라미터': [],
    '가이드워드': [],
    '이탈': [],
    '원인': [],
    '결과': [],
    '심각도': [],
    '안전장치': [],
    '개선사항': []
}

for agent5_file in sorted(agent5_files):
    print(f"[INFO] 파싱 중: {os.path.basename(agent5_file)}")

    try:
        with open(agent5_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        node_data = parse_agent5_json(json_data)

        # 데이터 병합
        for key in all_data.keys():
            all_data[key].extend(node_data[key])

        print(f"  - {len(node_data['노드'])}개 deviation 추가")

    except Exception as e:
        print(f"[WARNING] {agent5_file} 파싱 실패: {e}")
        continue

print(f"\n[INFO] 총 {len(all_data['노드'])}개의 deviation 추출됨")

# DataFrame 생성
HAZOP = pd.DataFrame(all_data)

print("[INFO] HAZOP DataFrame 생성 완료")
print(f"  - 행 수: {len(HAZOP)}")
print(f"  - 열 수: {len(HAZOP.columns)}")
print(f"  - 컬럼: {', '.join(HAZOP.columns)}")

# Excel 파일 저장
output_path = get_output_path('HAZOP_table.xlsx')

try:
    # Excel writer 설정 (셀 높이 자동 조정)
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        HAZOP.to_excel(writer, index=False, sheet_name='HAZOP Analysis')

        # 워크시트 가져오기
        worksheet = writer.sheets['HAZOP Analysis']

        # 열 너비 설정
        column_widths = {
            'A': 12,  # 노드
            'B': 20,  # 노드명
            'C': 15,  # 파라미터
            'D': 15,  # 가이드워드
            'E': 30,  # 이탈
            'F': 40,  # 원인
            'G': 40,  # 결과
            'H': 10,  # 심각도
            'I': 30,  # 안전장치
            'J': 40   # 개선사항
        }

        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

        # 텍스트 줄바꿈 설정
        from openpyxl.styles import Alignment
        for row in worksheet.iter_rows(min_row=2, max_row=len(HAZOP)+1):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

    print(f"\n[SUCCESS] HAZOP 테이블이 저장되었습니다: {output_path}")

    # 통계 출력
    print(f"\n[통계] 노드별 deviation 수:")
    node_counts = HAZOP['노드'].value_counts()
    for node, count in node_counts.items():
        print(f"  - {node}: {count}개")

    print(f"\n[통계] 심각도별 분포:")
    severity_counts = HAZOP['심각도'].value_counts()
    for severity, count in severity_counts.items():
        print(f"  - {severity}: {count}개")

except Exception as e:
    print(f"[ERROR] Excel 파일 저장 오류: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[INFO] HAZOP 테이블 생성이 완료되었습니다.")
