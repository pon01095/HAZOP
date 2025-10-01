# -*- coding: utf-8 -*-
"""
HAZOP 자동화 시스템 설정 파일
환경변수를 통한 보안 설정 관리
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """설정 클래스"""

    # OpenAI API 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # 파일 경로 설정
    BASE_DIRECTORY = os.getenv('BASE_DIRECTORY', '')
    IMAGE_DIRECTORY = os.getenv('IMAGE_DIRECTORY', '')
    DEFAULT_IMAGE = os.getenv('DEFAULT_IMAGE', '')

    # 공정 개요
    HAZOP_OBJECT = os.getenv('HAZOP_OBJECT',
        '검토대상은 바이오가스 고질화 시스템 공정으로 가스정제 전처리 설비에서 1차 제습, '
        '바이오가스 압축, 2차 제습 및 실록산 제거후 MEMBRANE 통과후 수소 분리하여 PRODUCT TANK까지의 공정')

    # API 요청 설정
    API_HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    # OpenAI 모델 설정
    MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o')  # 기본값: gpt-4o, .env에서 변경 가능 (gpt-4o 또는 gpt-5)
    MAX_TOKENS = 16000  # 응답 토큰 증가 (GPT-5는 추론 토큰 + 출력 토큰 포함)
    API_TIMEOUT = 300  # API 타임아웃 5분 (GPT-5는 더 오래 걸림)

    @classmethod
    def validate(cls):
        """설정 검증 및 초기화"""
        # API 키 검증
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY.strip() == '':
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

        # API 키 형식 검증 (sk-로 시작하는지 확인)
        if not cls.OPENAI_API_KEY.startswith('sk-'):
            raise ValueError("OPENAI_API_KEY 형식이 올바르지 않습니다. 'sk-'로 시작해야 합니다.")

        # 경로 검증
        if not os.path.exists(cls.DEFAULT_IMAGE):
            raise FileNotFoundError(f"기본 이미지 파일을 찾을 수 없습니다: {cls.DEFAULT_IMAGE}")

        # BASE_DIRECTORY가 없으면 생성
        if not os.path.exists(cls.BASE_DIRECTORY):
            try:
                os.makedirs(cls.BASE_DIRECTORY)
                print(f"출력 디렉토리 생성: {cls.BASE_DIRECTORY}")
            except Exception as e:
                raise Exception(f"BASE_DIRECTORY 생성 실패: {e}")

# 전역 설정 객체
config = Config()

# 설정 검증 실행
try:
    Config.validate()
except Exception as e:
    print(f"설정 검증 오류: {e}")
    exit(1)
