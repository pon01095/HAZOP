# -*- coding: utf-8 -*-
"""
HAZOP 분석 품질 평가 스크립트
개별 실행과 통합 실행의 HAZOP 분석 품질을 정량적/정성적으로 평가
"""

import os
import json
import re
import pandas as pd
from datetime import datetime
from config import config


class HAZOPQualityEvaluator:
    """HAZOP 분석 품질 평가 클래스"""

    def __init__(self, result_dir):
        self.result_dir = result_dir
        self.evaluation_results = {}

    def read_file(self, filename):
        """파일 읽기"""
        filepath = os.path.join(self.result_dir, filename)
        if not os.path.exists(filepath):
            return None

        try:
            if filename.endswith('.xlsx'):
                return pd.read_excel(filepath)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"파일 읽기 오류 ({filename}): {e}")
            return None

    # ========== Agent 1: 공정요소 분석 평가 ==========
    def evaluate_agent1_process_elements(self):
        """Agent 1: 공정 구성요소 식별 품질 평가"""
        content = self.read_file('공정요소.txt')
        if not content:
            return {'error': '파일 없음'}

        # 정량적 지표
        equipment_pattern = r'구성요소\s+\d+\.\s+\*\*([^*]+)\*\*'
        equipments = re.findall(equipment_pattern, content)

        description_pattern = r'설명:\s*(.+?)(?=\n\n|구성요소|\Z)'
        descriptions = re.findall(description_pattern, content, re.DOTALL)

        # 기기 종류별 분류
        equipment_types = {
            '펌프/블로워': ['pump', 'blower', 'compressor'],
            '탱크/용기': ['tank', 'vessel', 'tower', 'column'],
            '제습/분리': ['dehumid', 'separator', 'filter', 'removal'],
            '계측기': ['transmitter', 'indicator', 'controller', 'analyzer', 'gauge', 'sensor'],
            '밸브': ['valve'],
        }

        categorized = {cat: [] for cat in equipment_types.keys()}
        for eq in equipments:
            eq_lower = eq.lower()
            for category, keywords in equipment_types.items():
                if any(kw in eq_lower for kw in keywords):
                    categorized[category].append(eq)
                    break

        # 품질 지표
        avg_desc_length = sum(len(d.strip()) for d in descriptions) / len(descriptions) if descriptions else 0

        evaluation = {
            'equipment_count': len(equipments),
            'description_count': len(descriptions),
            'avg_description_length': avg_desc_length,
            'equipment_categories': {k: len(v) for k, v in categorized.items()},
            'equipment_list': equipments[:10],  # 처음 10개만

            # 품질 점수 (0-100)
            'completeness_score': min(100, len(equipments) * 10),  # 10개 이상이면 만점
            'detail_score': min(100, avg_desc_length / 3),  # 평균 300자 이상이면 만점
            'coverage_score': len([v for v in categorized.values() if v]) * 20,  # 5개 카테고리 커버면 만점
        }

        # 총점 계산
        evaluation['total_score'] = (
            evaluation['completeness_score'] * 0.4 +
            evaluation['detail_score'] * 0.3 +
            evaluation['coverage_score'] * 0.3
        )

        return evaluation

    # ========== Agent 2: 노드 분리 평가 ==========
    def evaluate_agent2_node_separation(self):
        """Agent 2: 노드 분리 품질 평가"""
        content = self.read_file('Agent2.txt')
        if not content:
            return {'error': '파일 없음'}

        # 노드 추출
        node_pattern = r'###\s*Node\s+(\d+):\s*([^\n]+)'
        nodes = re.findall(node_pattern, content)

        # 각 노드의 구성요소 개수
        node_details = []
        for node_num, node_name in nodes:
            # 해당 노드 섹션 추출
            node_section_pattern = rf'###\s*Node\s+{node_num}:.*?(?=###\s*Node|\Z)'
            node_section = re.search(node_section_pattern, content, re.DOTALL)

            if node_section:
                section_text = node_section.group(0)
                # 구성요소 개수 세기 (번호 매겨진 항목)
                component_pattern = r'^\d+\.\s+\*\*'
                components = len(re.findall(component_pattern, section_text, re.MULTILINE))

                node_details.append({
                    'node_number': node_num,
                    'node_name': node_name.strip(),
                    'component_count': components
                })

        # 품질 지표
        avg_components = sum(n['component_count'] for n in node_details) / len(node_details) if node_details else 0

        evaluation = {
            'node_count': len(nodes),
            'node_details': node_details,
            'avg_components_per_node': avg_components,
            'min_components': min((n['component_count'] for n in node_details), default=0),
            'max_components': max((n['component_count'] for n in node_details), default=0),

            # 품질 점수
            'node_coverage_score': min(100, len(nodes) * 25),  # 4개 이상이면 만점
            'balance_score': 100 if len(node_details) > 0 and (
                max((n['component_count'] for n in node_details), default=0) /
                max(min((n['component_count'] for n in node_details), default=1), 1) <= 3
            ) else 60,  # 노드 간 균형
            'detail_score': min(100, avg_components * 20),  # 노드당 평균 5개 이상이면 만점
        }

        evaluation['total_score'] = (
            evaluation['node_coverage_score'] * 0.4 +
            evaluation['balance_score'] * 0.3 +
            evaluation['detail_score'] * 0.3
        )

        return evaluation

    # ========== Agent 3: 공정변수 평가 ==========
    def evaluate_agent3_process_parameters(self):
        """Agent 3: 공정 변수 식별 품질 평가"""
        content = self.read_file('Agent3.txt')
        if not content:
            return {'error': '파일 없음'}

        # 공정변수 추출
        specific_params = ['Flow', 'Pressure', 'Temperature', 'Composition', 'Level', 'Phase', 'Viscosity']
        general_params = ['Addition', 'Service', 'Sampling', 'Testing', 'Reaction', 'Corrosion', 'Relief', 'Instrumentation', 'Maintenance', 'Mixing']

        found_specific = [p for p in specific_params if p in content or p in content.replace('유량', 'Flow').replace('압력', 'Pressure')]
        found_general = [p for p in general_params if p in content]

        # HAZOP 필수 변수 체크
        critical_params = ['Flow', 'Pressure', 'Temperature']
        critical_coverage = sum(1 for p in critical_params if p in content or
                               ('Flow' == p and '유량' in content) or
                               ('Pressure' == p and '압력' in content) or
                               ('Temperature' == p and '온도' in content))

        evaluation = {
            'specific_parameter_count': len(found_specific),
            'general_parameter_count': len(found_general),
            'total_parameter_count': len(found_specific) + len(found_general),
            'found_specific_params': found_specific,
            'found_general_params': found_general,
            'critical_coverage': critical_coverage,

            # 품질 점수
            'critical_coverage_score': (critical_coverage / len(critical_params)) * 100,
            'specific_coverage_score': (len(found_specific) / len(specific_params)) * 100,
            'general_coverage_score': (len(found_general) / len(general_params)) * 100,
        }

        evaluation['total_score'] = (
            evaluation['critical_coverage_score'] * 0.5 +
            evaluation['specific_coverage_score'] * 0.3 +
            evaluation['general_coverage_score'] * 0.2
        )

        return evaluation

    # ========== Agent 4: 이탈 시나리오 평가 ==========
    def evaluate_agent4_deviations(self):
        """Agent 4: 이탈 시나리오 품질 평가"""
        content = self.read_file('Agent4.txt')
        if not content:
            return {'error': '파일 없음'}

        # 가이드워드별 이탈 개수
        guidewords = ['None', 'More', 'Less', 'As well as', 'Other than', 'Part of', 'Reverse']

        # 각 공정변수별 이탈 개수 세기
        param_sections = re.split(r'####\s*(Flow|Pressure|Temperature|Composition|Level|Phase|Viscosity)', content)

        deviations_by_param = {}
        total_deviations = 0

        for i in range(1, len(param_sections), 2):
            if i+1 < len(param_sections):
                param = param_sections[i]
                section = param_sections[i+1]

                # 각 가이드워드 개수 세기
                deviations = []
                for gw in guidewords:
                    # "1. None" 또는 "None:" 형태 찾기
                    pattern = rf'\d+\.\s*{gw}\s*\n\s*-'
                    matches = len(re.findall(pattern, section, re.IGNORECASE))
                    if matches > 0:
                        deviations.append(gw)
                        total_deviations += matches

                deviations_by_param[param] = {
                    'guidewords_covered': len(deviations),
                    'guidewords': deviations
                }

        # 이탈 설명의 구체성 평가 (예시 개수)
        example_count = len(re.findall(r'-\s+[가-힣A-Za-z].{10,}', content))

        evaluation = {
            'parameter_count': len(deviations_by_param),
            'total_deviations': total_deviations,
            'deviations_by_parameter': deviations_by_param,
            'avg_guidewords_per_param': sum(d['guidewords_covered'] for d in deviations_by_param.values()) / len(deviations_by_param) if deviations_by_param else 0,
            'example_count': example_count,

            # 품질 점수
            'coverage_score': (len(deviations_by_param) / 4) * 100 if deviations_by_param else 0,  # 최소 4개 변수
            'completeness_score': (sum(d['guidewords_covered'] for d in deviations_by_param.values()) / (len(deviations_by_param) * 7)) * 100 if deviations_by_param else 0,
            'detail_score': min(100, example_count / len(deviations_by_param) * 10) if deviations_by_param else 0,
        }

        evaluation['total_score'] = (
            evaluation['coverage_score'] * 0.3 +
            evaluation['completeness_score'] * 0.4 +
            evaluation['detail_score'] * 0.3
        )

        return evaluation

    # ========== Agent 5: 안전장치 평가 ==========
    def evaluate_agent5_safeguards(self):
        """Agent 5: 원인/결과/안전장치 분석 품질 평가"""
        content = self.read_file('Agent5.txt')
        if not content:
            return {'error': '파일 없음'}

        # 키워드 기반 분석
        cause_keywords = ['원인:', 'cause:', '고장', '오작동', '누출', '막힘']
        consequence_keywords = ['결과:', 'consequence:', '위험', '폭발', '누출', '중단', '손상']
        safeguard_keywords = ['안전장치:', 'safeguard:', '경보', 'alarm', '차단', 'interlock', 'relief', 'PSV', '모니터링', '센서']

        cause_count = sum(content.lower().count(kw.lower()) for kw in cause_keywords)
        consequence_count = sum(content.lower().count(kw.lower()) for kw in consequence_keywords)
        safeguard_count = sum(content.lower().count(kw.lower()) for kw in safeguard_keywords)

        # 이탈별 분석 개수
        deviation_sections = re.split(r'\d+\.\s*(No |More |Less |Reverse )', content)
        analyzed_deviations = (len(deviation_sections) - 1) // 2 if len(deviation_sections) > 1 else 0

        # 구체적인 기기명 언급 (예: PT-1102, TC-1101)
        equipment_mentions = len(re.findall(r'[A-Z]{1,3}-\d{4}', content))

        # 개선사항 제안 여부
        improvement_keywords = ['개선', 'improvement', '추가', '설치', '이중화', '정기점검']
        improvement_count = sum(content.count(kw) for kw in improvement_keywords)

        evaluation = {
            'analyzed_deviations': analyzed_deviations,
            'cause_mentions': cause_count,
            'consequence_mentions': consequence_count,
            'safeguard_mentions': safeguard_count,
            'equipment_references': equipment_mentions,
            'improvement_suggestions': improvement_count,

            # 품질 점수
            'completeness_score': min(100, (cause_count + consequence_count + safeguard_count) / 3),
            'specificity_score': min(100, equipment_mentions * 5),  # 기기명 구체적 언급
            'actionability_score': min(100, improvement_count * 10),  # 개선 제안
        }

        evaluation['total_score'] = (
            evaluation['completeness_score'] * 0.4 +
            evaluation['specificity_score'] * 0.3 +
            evaluation['actionability_score'] * 0.3
        )

        return evaluation

    # ========== Agent 6: 최종 테이블 평가 ==========
    def evaluate_agent6_final_table(self):
        """Agent 6: 최종 HAZOP 테이블 품질 평가"""
        df = self.read_file('HAZOP_table.xlsx')
        if df is None:
            return {'error': '파일 없음'}

        # 기본 구조 평가
        expected_columns = ['노드', '이탈', 'Deviation Description', 'Safeguard']
        has_all_columns = all(col in df.columns for col in expected_columns)

        # 데이터 완성도
        row_count = len(df)
        non_empty_rows = df.dropna(how='all').shape[0]
        completeness_ratio = non_empty_rows / row_count if row_count > 0 else 0

        # 각 컬럼의 빈 값 비율
        empty_ratios = {}
        for col in df.columns:
            if col in df.columns:
                empty_count = df[col].isna().sum() + (df[col] == '').sum()
                empty_ratios[col] = empty_count / row_count if row_count > 0 else 0

        # 이탈 다양성 (중복 제거)
        unique_deviations = df['이탈'].nunique() if '이탈' in df.columns else 0

        # Safeguard 구체성 (평균 길이)
        avg_safeguard_length = df['Safeguard'].str.len().mean() if 'Safeguard' in df.columns else 0

        evaluation = {
            'row_count': row_count,
            'column_count': len(df.columns),
            'has_all_expected_columns': has_all_columns,
            'non_empty_rows': non_empty_rows,
            'completeness_ratio': completeness_ratio,
            'empty_ratios': empty_ratios,
            'unique_deviations': unique_deviations,
            'avg_safeguard_length': avg_safeguard_length,

            # 품질 점수
            'structure_score': 100 if has_all_columns else 60,
            'completeness_score': completeness_ratio * 100,
            'diversity_score': min(100, unique_deviations * 5),  # 20개 이상이면 만점
            'detail_score': min(100, avg_safeguard_length / 2),  # 평균 200자 이상이면 만점
        }

        evaluation['total_score'] = (
            evaluation['structure_score'] * 0.2 +
            evaluation['completeness_score'] * 0.3 +
            evaluation['diversity_score'] * 0.2 +
            evaluation['detail_score'] * 0.3
        )

        return evaluation

    # ========== 전체 평가 ==========
    def evaluate_all(self):
        """전체 Agent 평가 실행"""
        print(f"\n{'='*60}")
        print(f"  HAZOP 분석 품질 평가: {self.result_dir}")
        print(f"{'='*60}\n")

        evaluations = {
            'Agent1_공정요소': self.evaluate_agent1_process_elements(),
            'Agent2_노드분리': self.evaluate_agent2_node_separation(),
            'Agent3_공정변수': self.evaluate_agent3_process_parameters(),
            'Agent4_이탈시나리오': self.evaluate_agent4_deviations(),
            'Agent5_안전장치': self.evaluate_agent5_safeguards(),
            'Agent6_최종테이블': self.evaluate_agent6_final_table(),
        }

        # 전체 점수 계산 (각 Agent 가중 평균)
        total_score = sum(e.get('total_score', 0) for e in evaluations.values()) / len(evaluations)

        evaluations['overall'] = {
            'total_score': total_score,
            'grade': self.get_grade(total_score),
            'timestamp': datetime.now().isoformat()
        }

        self.evaluation_results = evaluations
        return evaluations

    def get_grade(self, score):
        """점수에 따른 등급 반환"""
        if score >= 90:
            return 'A (우수)'
        elif score >= 80:
            return 'B (양호)'
        elif score >= 70:
            return 'C (보통)'
        elif score >= 60:
            return 'D (미흡)'
        else:
            return 'F (불량)'

    def print_summary(self):
        """평가 결과 요약 출력"""
        if not self.evaluation_results:
            return

        print(f"\n{'#'*60}")
        print(f"  평가 요약")
        print(f"{'#'*60}\n")

        for agent_name, result in self.evaluation_results.items():
            if agent_name == 'overall':
                continue

            if 'error' in result:
                print(f"❌ {agent_name}: {result['error']}")
                continue

            score = result.get('total_score', 0)
            grade = self.get_grade(score)
            print(f"📊 {agent_name}: {score:.1f}점 [{grade}]")

        overall = self.evaluation_results.get('overall', {})
        print(f"\n{'='*60}")
        print(f"🏆 전체 평가: {overall.get('total_score', 0):.1f}점 [{overall.get('grade', 'N/A')}]")
        print(f"{'='*60}\n")

    def save_report(self, output_path=None):
        """평가 보고서 저장"""
        if not self.evaluation_results:
            return

        output_path = output_path or os.path.join(
            self.result_dir,
            f'quality_evaluation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.evaluation_results, f, ensure_ascii=False, indent=2)
            print(f"📝 평가 보고서 저장: {output_path}")
        except Exception as e:
            print(f"보고서 저장 실패: {e}")


def compare_two_results(dir1, dir2):
    """두 결과의 품질 비교"""
    print("\n" + "="*60)
    print("  두 결과 품질 비교")
    print("="*60)

    evaluator1 = HAZOPQualityEvaluator(dir1)
    results1 = evaluator1.evaluate_all()
    evaluator1.print_summary()

    print("\n" + "-"*60 + "\n")

    evaluator2 = HAZOPQualityEvaluator(dir2)
    results2 = evaluator2.evaluate_all()
    evaluator2.print_summary()

    # 비교 테이블
    print("\n" + "="*60)
    print("  상세 비교")
    print("="*60 + "\n")

    comparison = []
    for agent_name in results1.keys():
        if agent_name == 'overall':
            continue

        score1 = results1[agent_name].get('total_score', 0)
        score2 = results2[agent_name].get('total_score', 0)
        diff = score2 - score1

        comparison.append({
            'Agent': agent_name,
            '개별실행': f"{score1:.1f}",
            '통합실행': f"{score2:.1f}",
            '차이': f"{diff:+.1f}",
            '판정': '🟢 통합우세' if diff > 5 else ('🔴 개별우세' if diff < -5 else '⚪ 동등')
        })

    df_comparison = pd.DataFrame(comparison)
    print(df_comparison.to_string(index=False))

    overall_diff = results2['overall']['total_score'] - results1['overall']['total_score']
    print(f"\n{'='*60}")
    print(f"전체 차이: {overall_diff:+.1f}점")
    if abs(overall_diff) < 5:
        print("✅ 두 방식의 품질이 유사합니다.")
    elif overall_diff > 0:
        print("✅ 통합 실행이 더 나은 품질을 보입니다.")
    else:
        print("✅ 개별 실행이 더 나은 품질을 보입니다.")
    print(f"{'='*60}\n")

    return results1, results2


def main():
    """메인 실행 함수"""
    print("HAZOP 분석 품질 평가 도구 v1.0")
    print("="*60)

    mode = input("\n평가 모드 선택:\n1. 단일 결과 평가\n2. 두 결과 비교\n선택 (1/2): ").strip()

    if mode == '1':
        result_dir = input("평가할 결과 디렉토리 (Enter=기본값): ").strip() or config.BASE_DIRECTORY
        evaluator = HAZOPQualityEvaluator(result_dir)
        evaluator.evaluate_all()
        evaluator.print_summary()
        evaluator.save_report()
    elif mode == '2':
        dir1 = input("디렉토리 1 (개별 실행): ").strip() or config.BASE_DIRECTORY + "_individual"
        dir2 = input("디렉토리 2 (통합 실행): ").strip() or config.BASE_DIRECTORY + "_integrated"
        compare_two_results(dir1, dir2)
    else:
        print("잘못된 선택입니다.")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
