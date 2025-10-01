# -*- coding: utf-8 -*-

import sys
import os
import re
import pandas as pd

# 상위 폴더 경로

root_folder = 'C:/Users/B/Desktop/2025/마이크로원/데이터/Daily Report'  # 예: 'C:/data'
print('a')

date_pattern = re.compile(r'20\d{2}_[01]\d_[0-3]\d')  # 예: 2024_11_01

# 결과 저장 리스트
all_dfs = []

for dirpath, dirnames, filenames in os.walk(root_folder):
    for filename in filenames:
        if filename.endswith('.xlsx') and date_pattern.search(filename):
            file_path = os.path.join(dirpath, filename)
            try:
                # 엑셀 파일 읽기 (5행 메타 정보 제거)
                df = pd.read_excel(file_path, sheet_name=0, skiprows=5)

                # 첫 열 → timestamp
                df[df.columns[0]] = pd.to_datetime(df[df.columns[0]], errors='coerce')
                df.rename(columns={df.columns[0]: 'timestamp'}, inplace=True)
                df.dropna(subset=['timestamp'], inplace=True)
                df.set_index('timestamp', inplace=True)

                # 숫자형 변환 및 보간
                df = df.apply(pd.to_numeric, errors='coerce')
                df = df.interpolate(method='time')

                all_dfs.append(df)
            except Exception as e:
                print(f"오류 발생: {filename} - {e}")

# 전체 병합
merged_df = pd.concat(all_dfs).sort_index()

# 병합된 데이터 개요 확인
print("✅ 병합된 데이터 개수:", len(merged_df))
print("📆 타임스탬프 범위:", merged_df.index.min(), "→", merged_df.index.max())
print("🧱 컬럼 개수:", len(merged_df.columns))
print("📊 컬럼 목록:", merged_df.columns.tolist())

# 앞뒤 데이터 일부 출력
print("\n[상위 5개 행]")
print(merged_df.head())

# 결측치 많은 컬럼 탐색
missing_counts = merged_df.isnull().sum()
print("\n❓ 결측치가 많은 상위 컬럼:")
print(missing_counts[missing_counts > 0].sort_values(ascending=False).head())

# 6. 병합된 데이터를 엑셀로 저장
output_path = os.path.join(root_folder, 'merged_timeseries_preview.xlsx')
merged_df.to_excel(output_path, index=True)
print(f"📁 병합된 데이터가 다음 경로에 저장되었습니다:\n{output_path}")