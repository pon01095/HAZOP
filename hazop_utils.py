# -*- coding: utf-8 -*-
"""
HAZOP 자동화 공통 유틸리티
모든 Agent에서 사용하는 공통 함수들
"""

import base64
import requests
import os
import json
from config import config


# ========== 파일 처리 함수 ==========

def encode_image(image_path):
    """이미지를 base64로 인코딩"""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"이미지 인코딩 오류: {e}")
        exit(1)


def read_txt(txt_path):
    """텍스트 파일 읽기"""
    try:
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"텍스트 파일을 찾을 수 없습니다: {txt_path}")
        with open(txt_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        exit(1)


def write_txt(file_path, content):
    """텍스트 파일 쓰기"""
    try:
        # 디렉토리가 없으면 생성
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"파일이 저장되었습니다: {file_path}")
        return True
    except IOError as e:
        print(f"파일 저장 오류: {e}")
        exit(1)


def write_json(file_path, data):
    """JSON 파일 쓰기"""
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON 파일이 저장되었습니다: {file_path}")
        return True
    except IOError as e:
        print(f"JSON 파일 저장 오류: {e}")
        exit(1)


def save_conversation_history(file_path, conversation_history):
    """대화 히스토리를 JSON 파일로 저장"""
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'w', encoding='utf-8') as f:
            for message in conversation_history:
                f.write(json.dumps(message, ensure_ascii=False) + '\n')
        print(f"대화 히스토리가 저장되었습니다: {file_path}")
        return True
    except IOError as e:
        print(f"대화 히스토리 저장 오류: {e}")
        exit(1)


# ========== OpenAI API 호출 함수 ==========

def call_openai_api(payload, timeout=None):
    """
    OpenAI API 호출 (에러 처리 포함)

    Args:
        payload: API 요청 페이로드
        timeout: 타임아웃 (초), None이면 config.API_TIMEOUT 사용

    Returns:
        API 응답 content 문자열
    """
    timeout = timeout or config.API_TIMEOUT
    headers = config.API_HEADERS

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        response_json = response.json()
        if 'choices' not in response_json or not response_json['choices']:
            print(f"[ERROR] API 응답 구조 이상: {response_json}")
            raise ValueError("API 응답에 예상된 데이터가 없습니다.")

        content = response_json['choices'][0]['message']['content']
        if not content:
            print(f"[WARNING] API returned empty content. Full response: {response_json}")
        return content

    except requests.exceptions.RequestException as e:
        print(f"API 요청 오류: {e}")
        exit(1)
    except (KeyError, ValueError) as e:
        print(f"응답 파싱 오류: {e}")
        exit(1)


def create_vision_payload(system_prompt, user_text, image_base64, model=None, max_tokens=None, image_format="png"):
    """
    Vision API용 페이로드 생성

    Args:
        system_prompt: 시스템 프롬프트
        user_text: 사용자 텍스트
        image_base64: base64 인코딩된 이미지
        model: 모델명 (None이면 config.MODEL_NAME 사용)
        max_tokens: 최대 토큰 (None이면 config.MAX_TOKENS 사용)
        image_format: 이미지 형식 (png, jpeg 등)

    Returns:
        API 페이로드 딕셔너리
    """
    model = model or config.MODEL_NAME
    max_tokens = max_tokens or config.MAX_TOKENS

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format};base64,{image_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        "max_completion_tokens": max_tokens
    }

    return payload


def create_text_payload(system_prompt, user_text, model=None, max_tokens=None):
    """
    텍스트 전용 API 페이로드 생성

    Args:
        system_prompt: 시스템 프롬프트
        user_text: 사용자 텍스트
        model: 모델명 (None이면 config.MODEL_NAME 사용)
        max_tokens: 최대 토큰 (None이면 config.MAX_TOKENS 사용)

    Returns:
        API 페이로드 딕셔너리
    """
    model = model or config.MODEL_NAME
    max_tokens = max_tokens or config.MAX_TOKENS

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        "max_completion_tokens": max_tokens
    }

    return payload


# ========== 디렉토리 관리 ==========

def ensure_directory_exists(directory):
    """디렉토리가 없으면 생성"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"디렉토리 생성: {directory}")
            return True
        except Exception as e:
            print(f"디렉토리 생성 실패: {e}")
            return False
    return True


def get_output_path(filename):
    """BASE_DIRECTORY 기준 출력 파일 경로 반환"""
    ensure_directory_exists(config.BASE_DIRECTORY)
    return os.path.join(config.BASE_DIRECTORY, filename)
