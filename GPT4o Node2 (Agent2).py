# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 16:48:10 2024

@author: B
"""

import base64
import requests
import os
from PIL import Image
import matplotlib.pyplot as plt
from datetime import datetime
import json

# 설정 파일 import
from config import config

# OpenAI API 설정 (환경변수에서 로드)
api_key = config.OPENAI_API_KEY
 
# 이미지를 base64로 인코딩하는 함수
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
 
# 파일 읽기
def read_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

# 이미지 경로 (config에서 가져오기)
image_path = os.path.join(config.IMAGE_DIRECTORY, 'P&ID_수소혼입.png')

answer_path = os.path.join(config.BASE_DIRECTORY, '공정요소.txt')
answer_before = read_txt(answer_path)

# base64 문자열 얻기 (중복 호출 제거)
base64_image = encode_image(image_path)

# API 헤더와 공정 개요 (config에서 가져오기)
headers = config.API_HEADERS
HAZOP_object = config.HAZOP_OBJECT
input_ = """
현재 입력된 전체 도면이 공정의 어느 부분인지 설명하고, HAZOP에 사용될 수 있게 노드를 나눠줘. 그리고 노드에 속하는 구성 요소와 설계 의도를 설명해줘. 각 노드에 포함되는  Node는 HAZOP 보고서 작성을 위한 분리단위야
**Answer example**

example 1.
#### Node 1: 바이오가스 저장 및 이송
**구성요소:**
- 바이오가스 저장조
- B-1101 Blower
- PC-1101 Pressure Controller

**설명:**
바이오가스를 저장하고, B-1101 Blower를 통해 가스 정제 전처리 설비로 이송합니다. PC-1101 Pressure Controller는 시스템 압력을 모니터링하고 제어합니다.

#### Node 2: 1차 제습
**구성요소:**
- D-1101 1차 제습장치
- TC-1101 Temperature Controller

**설명:**
D-1101 1차 제습장치는 바이오가스의 수분 함량을 제거하며, TC-1101 Temperature Controller는 온도를 모니터링하고 제어합니다.

#### Node 3: 가스 압축
**구성요소:**
- 압축기
- PC-1102 Pressure Controller

**설명:**
압축기를 통해 바이오가스를 압축하여 가스 밀도를 높이며, PC-1102 Pressure Controller는 압축 과정의 압력을 측정하고 제어합니다.

#### Node 4: 2차 제습 및 실록산 제거
**구성요소:**
- R-1101 Siloxane Removal Tower
- TT-1105 Temperature Transmitter
- PT-1105 Pressure Transmitter

**설명:**
R-1101 Siloxane Removal Tower는 바이오가스에서 실록산을 제거하고 2차 제습을 실시합니다. TT-1105와 PT-1105는 각각 온도와 압력을 모니터링합니다.

#### Node 5: 가스 필터링
**구성요소:**
- Particular Filter
- PC-1103 Pressure Controller

**설명:**
Particular Filter를 통해 바이오가스의 미세 입자를 제거합니다. PC-1103 Pressure Controller는 필터링된 가스의 압력을 측정하고 조정합니다.

#### Node 6: 가스 분석 및 흐름 제어
**구성요소:**
- AI-1101 Analyzer
- FCV-1101 Flow Control Valve
- FC-1102 Flow Controller
- FI-1101 Flow Indicator

**설명:**
AI-1101 Analyzer는 가스의 특정 성분을 분석하며, FCV-1101 Flow Control Valve와 FC-1102 Flow Controller는 가스의 흐름을 조절합니다. FI-1101 Flow Indicator는 가스의 유량을 측정합니다.

#### Node 7: 전처리 설비 이송
**구성요소:**
- FCV-1102 Flow Control Valve
- FT-1102 Flow Transmitter
- 전처리 설비-2 M-012

**설명:**
FCV-1102 Flow Control Valve는 가스의 흐름을 조절하여 전처리 설비-2(M-012)로 가스를 이송합니다. FT-1102 Flow Transmitter는 가스의 유량을 측정합니다.

example 2.
Node 1: 바이오가스 압축 시작

설명:
- 바이오가스 저장조에서 시작하여 B-1101 Blower까지 가스를 이송합니다.
- 바이오가스 저장조에서 배출된 가스를 B-1101 Blower로 이송해 가스의 압력을 높입니다.

Node 2: 1차 제습 및 압력 제어

설명:
- B-1101 Blower에서 D-1101 1차 제습장치까지의 바이오가스를 제습 및 압력 제어합니다.
- D-1101 1차 제습장치에서 바이오가스를 제습하여 수분을 제거합니다.
- 다양한 압력 트랜스미터 및 컨트롤러 (PC-1102)를 통해 압력을 제어합니다.
- PT-1102 Pressure Transmitter와 TI-1102 Temperature Indicator를 통해 가스의 압력과 온도를 모니터링합니다.

Node 3: 가스 분석 및 품질 관리

설명:
- AI-1101 Analyzer를 통해 가스의 특정 성분을 분석합니다.
- 가스 흐름 측정기 (FI-1101 Flow Indicator)와 연결되어 있어 가스의 유량을 체크합니다.
  
Node 4: 실록산 제거 및 미세 입자 필터링

설명:
- R-1101 Siloxane Removal Tower에서 가스에서 실록산을 제거해 가스의 품질을 높입니다.
- Particular Filter를 통해 바이오가스의 미세 입자를 제거합니다.
- 추가적으로 PC-1103 Pressure Controller 및 TI-1103 Temperature Indicator를 사용해 가스의 온도와 압력 관리.

Node 5: 유량 및 흐름 제어를 통한 가스의 저장

설명:
- FCV-1101 Flow Control Valve를 사용해 가스의 흐름을 조절합니다.
- 전처리 설비-2 (M-012)로 가스를 이송하여 PRODUCT TANK로 저장합니다.
"""


payload = {
    "model": "gpt-4o",
    "messages": [
      {
        "role": "system", "content": "너는 P&ID 도면을 보고 HAZOP 분석을 위해 노드를 분리하는 에이전트야",
        "role": "user", "content":
            [
          {
            "type": "text",
            "text": f"질문: {input_}, 이전 답변: {answer_before}, 공정개요:{HAZOP_object}"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}"
            }
          }
        ]
      }
    ],
    "max_tokens": 1000
}
 
response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
# 'content' 부분만 추출하여 출력
content = response.json()['choices'][0]['message']['content']
 
# 이미지 표시
img = Image.open(image_path)
plt.imshow(img)
plt.axis('off')  # 축 정보 숨기기
plt.show()
 
# 응답 출력
print(content)


# 파일을 저장할 경로 설정 (config에서 가져오기)
base_directory = config.BASE_DIRECTORY

if not os.path.exists(base_directory):
    os.makedirs(base_directory)

# 현재 날짜와 시간을 포함한 파일 이름 생성
file_name = "Agent2" + ".txt"
file_path = os.path.join(base_directory, file_name)

# 대화 히스토리
conversation_history = [
    {"role": "assistant", "content": f'{content}'}
]

# 대화 히스토리를 텍스트 파일로 저장
with open(file_path, 'w', encoding='utf-8') as f:
    for message in conversation_history:
        f.write(json.dumps(message, ensure_ascii=False) + '\n')
        
print(f"파일이 저장되었습니다: {file_path}")