# -*- coding: utf-8 -*-
"""
HAZOP 결과 비교 스크립트
개별 실행과 통합 실행의 결과를 비교합니다.
"""

import os
import json
import hashlib
import pandas as pd
from datetime import datetime
from config import config


class ResultComparator:
    """결과 비교 클래스"""

    def __init__(self):
        self.comparison_results = []

    def get_file_hash(self, file_path):
        """파일의 MD5 해시값 계산"""
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"해시 계산 오류 ({file_path}): {e}")
            return None

    def compare_text_files(self, file1, file2):
        """텍스트 파일 비교"""
        if not os.path.exists(file1) or not os.path.exists(file2):
            return {
                'identical': False,
                'reason': '파일 누락',
                'file1_exists': os.path.exists(file1),
                'file2_exists': os.path.exists(file2)
            }

        try:
            with open(file1, 'r', encoding='utf-8') as f:
                content1 = f.read()
            with open(file2, 'r', encoding='utf-8') as f:
                content2 = f.read()

            identical = content1 == content2

            return {
                'identical': identical,
                'size1': len(content1),
                'size2': len(content2),
                'size_diff': abs(len(content1) - len(content2)),
                'similarity': self.calculate_similarity(content1, content2)
            }
        except Exception as e:
            return {
                'identical': False,
                'reason': f'읽기 오류: {str(e)}'
            }

    def calculate_similarity(self, text1, text2):
        """텍스트 유사도 계산 (간단한 문자 단위 비교)"""
        if not text1 or not text2:
            return 0.0

        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)
        min_len = min(len1, len2)

        # 공통 문자 개수 계산 (간단한 방식)
        matches = sum(1 for i in range(min_len) if text1[i] == text2[i])

        return (matches / max_len) * 100 if max_len > 0 else 0.0

    def compare_excel_files(self, file1, file2):
        """Excel 파일 비교"""
        if not os.path.exists(file1) or not os.path.exists(file2):
            return {
                'identical': False,
                'reason': '파일 누락',
                'file1_exists': os.path.exists(file1),
                'file2_exists': os.path.exists(file2)
            }

        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)

            # 형태 비교
            shape_match = df1.shape == df2.shape

            # 컬럼 비교
            columns_match = list(df1.columns) == list(df2.columns)

            # 데이터 비교
            data_match = df1.equals(df2) if shape_match and columns_match else False

            return {
                'identical': data_match,
                'shape1': df1.shape,
                'shape2': df2.shape,
                'shape_match': shape_match,
                'columns_match': columns_match,
                'row_count1': len(df1),
                'row_count2': len(df2),
                'col_count1': len(df1.columns),
                'col_count2': len(df2.columns)
            }
        except Exception as e:
            return {
                'identical': False,
                'reason': f'읽기 오류: {str(e)}'
            }

    def compare_directories(self, dir1, dir2):
        """두 디렉토리의 출력 파일 비교"""
        print(f"\n{'='*60}")
        print(f"  디렉토리 비교")
        print(f"{'='*60}")
        print(f"디렉토리 1 (개별 실행): {dir1}")
        print(f"디렉토리 2 (통합 실행): {dir2}")
        print()

        # 비교할 파일 목록
        files_to_compare = [
            ('공정요소.txt', 'text'),
            ('Agent2.txt', 'text'),
            ('Agent3.txt', 'text'),
            ('Agent4.txt', 'text'),
            ('Agent5.txt', 'text'),
            ('HAZOP_table.xlsx', 'excel')
        ]

        results = []

        for filename, file_type in files_to_compare:
            file1 = os.path.join(dir1, filename)
            file2 = os.path.join(dir2, filename)

            print(f"\n[{filename}] 비교 중...")

            if file_type == 'text':
                comparison = self.compare_text_files(file1, file2)
            elif file_type == 'excel':
                comparison = self.compare_excel_files(file1, file2)
            else:
                comparison = {'identical': False, 'reason': '알 수 없는 파일 형식'}

            comparison['filename'] = filename
            comparison['file_type'] = file_type
            results.append(comparison)

            # 결과 출력
            if comparison.get('identical'):
                print(f"  ✅ 동일함")
            else:
                print(f"  ❌ 차이 있음")
                if 'reason' in comparison:
                    print(f"     이유: {comparison['reason']}")
                elif 'similarity' in comparison:
                    print(f"     유사도: {comparison['similarity']:.2f}%")
                    print(f"     크기 차이: {comparison.get('size_diff', 0)} bytes")

        self.comparison_results = results
        return results

    def generate_report(self, output_path=None):
        """비교 결과 보고서 생성"""
        if not self.comparison_results:
            print("비교 결과가 없습니다.")
            return

        output_path = output_path or os.path.join(
            config.BASE_DIRECTORY,
            f'comparison_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': len(self.comparison_results),
                'identical_files': sum(1 for r in self.comparison_results if r.get('identical')),
                'different_files': sum(1 for r in self.comparison_results if not r.get('identical'))
            },
            'details': self.comparison_results
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n📝 비교 보고서 저장: {output_path}")

            # 요약 출력
            print(f"\n{'='*60}")
            print(f"  비교 요약")
            print(f"{'='*60}")
            print(f"총 파일 수: {report['summary']['total_files']}")
            print(f"동일한 파일: {report['summary']['identical_files']}")
            print(f"차이 있는 파일: {report['summary']['different_files']}")

            if report['summary']['identical_files'] == report['summary']['total_files']:
                print(f"\n✅ 모든 파일이 동일합니다!")
            else:
                print(f"\n⚠️  일부 파일에 차이가 있습니다.")

        except Exception as e:
            print(f"보고서 저장 실패: {e}")


def main():
    """메인 실행 함수"""
    print("HAZOP 결과 비교 도구 v1.0")
    print("=" * 60)

    # 사용자 입력 받기
    print("\n비교할 두 디렉토리를 입력하세요.")
    print("(기본값: BASE_DIRECTORY)")

    dir1 = input("디렉토리 1 (개별 실행 결과, Enter=기본값): ").strip()
    dir2 = input("디렉토리 2 (통합 실행 결과, Enter=기본값): ").strip()

    dir1 = dir1 or config.BASE_DIRECTORY
    dir2 = dir2 or config.BASE_DIRECTORY

    # 같은 디렉토리면 경고
    if dir1 == dir2:
        print("\n⚠️  경고: 동일한 디렉토리를 비교하려고 합니다.")
        print("개별 실행과 통합 실행의 결과를 다른 폴더에 저장한 후 비교하세요.")
        print("\n예시:")
        print("  1. 개별 실행 → 결과를 'GPT4o/individual'에 저장")
        print("  2. 통합 실행 → 결과를 'GPT4o/integrated'에 저장")
        print("  3. 두 폴더 경로를 입력하여 비교")
        return 1

    # 비교 실행
    comparator = ResultComparator()
    comparator.compare_directories(dir1, dir2)
    comparator.generate_report()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
