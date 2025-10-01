# -*- coding: utf-8 -*-
import pandas as pd

# 파일 경로 설정
dist_file = "C:/Users/B/Downloads/유통량조사 서식(지역_업체명) (2).xlsx"
biz_file = "C:/Users/B/Desktop/2025/소방청/2024/final_centerlog/1.전체 업체리스트(21,574).xlsx"

# 유통량조사 서식에서 반입/반출 업체명 가져오기
dist_df = pd.read_excel(dist_file, skiprows=2)
company_names = dist_df.iloc[:, 20].dropna().astype(str).unique()  # 보통 21번째 열이 업체명

# 전체 업체리스트 불러오기
biz_df = pd.read_excel(biz_file)

# 업체명 기준으로 필터링
matched_df = biz_df[biz_df['업체명'].astype(str).isin(company_names)]

# 추출할 컬럼 리스트 (실제 컬럼명에 맞게 수정됨)
output_columns = [
    '업체명',
    '사업자 등록번호',
    '법인등록번호\nor 생년월일(개인)',
    '시도',
    '시군구',
    '세부주소',
    '대표자'
]

# 중복 제거 및 정렬
filtered_df = matched_df[output_columns].drop_duplicates()

# 결과 저장 (선택)
output_path = 'C:/Users/B/Desktop/2025/소방청/반입반출업체_정보_추출결과.xlsx'
filtered_df.to_excel(output_path, index=False)
print(f"✅ 저장 완료: {output_path}")
