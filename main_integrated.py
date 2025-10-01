# -*- coding: utf-8 -*-
"""
HAZOP 자동화 통합 실행 스크립트
전체 Agent 1~6을 순차적으로 실행하고 결과를 기록합니다.
"""

import os
import sys
import time
import json
from datetime import datetime
import subprocess

# 설정 파일 import
from config import config


class HAZOPPipeline:
    """HAZOP 분석 통합 파이프라인"""

    def __init__(self, log_dir=None):
        self.log_dir = log_dir or os.path.join(config.BASE_DIRECTORY, 'logs')
        self.execution_log = []
        self.start_time = None

        # 로그 디렉토리 생성
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log_event(self, agent_name, status, message, elapsed_time=None):
        """이벤트 로깅"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'status': status,
            'message': message,
            'elapsed_time': elapsed_time
        }
        self.execution_log.append(event)

        # 콘솔 출력
        print(f"[{event['timestamp']}] {agent_name}: {status} - {message}")
        if elapsed_time:
            print(f"  → 소요 시간: {elapsed_time:.2f}초")

    def run_agent(self, agent_num, script_name):
        """개별 Agent 실행"""
        agent_name = f"Agent{agent_num}"
        print(f"\n{'='*60}")
        print(f"  {agent_name} 실행 중...")
        print(f"{'='*60}")

        start = time.time()

        try:
            # 서브프로세스로 Agent 실행
            result = subprocess.run(
                [sys.executable, script_name],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # 인코딩 오류 처리
                timeout=120  # 2분 타임아웃
            )

            elapsed = time.time() - start

            if result.returncode == 0:
                self.log_event(agent_name, 'SUCCESS', '정상 완료', elapsed)
                return True, result.stdout
            else:
                error_msg = result.stderr or result.stdout
                self.log_event(agent_name, 'FAILED', f'실행 실패: {error_msg}', elapsed)
                return False, error_msg

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            self.log_event(agent_name, 'TIMEOUT', '타임아웃 발생 (5분 초과)', elapsed)
            return False, "타임아웃"
        except Exception as e:
            elapsed = time.time() - start
            self.log_event(agent_name, 'ERROR', f'예외 발생: {str(e)}', elapsed)
            return False, str(e)

    def check_output_file(self, file_path):
        """출력 파일 존재 및 크기 확인"""
        if not os.path.exists(file_path):
            return False, "파일 없음"

        size = os.path.getsize(file_path)
        if size == 0:
            return False, "빈 파일"

        return True, f"파일 크기: {size} bytes"

    def run_pipeline(self):
        """전체 파이프라인 실행"""
        self.start_time = datetime.now()
        print(f"\n{'#'*60}")
        print(f"  HAZOP 자동화 통합 실행 시작")
        print(f"  시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")

        # Agent 정의
        agents = [
            (1, "gpt4o_P&ID_input(Agent1).py", "공정요소.txt"),
            (2, "GPT4o Node (Agent2).py", "Agent2.txt"),
            (3, "GPT4o Parameter_Guideword (Agent3).py", "Agent3.txt"),
            (4, "GPT4o CreateDeviation (Agent4).py", "Agent4.txt"),
            (5, "GPT4o Safeguard (Agent5).py", "Agent5.txt"),
            (6, "GPT4o HAZOP Table (Agent6).py", "HAZOP_table.xlsx"),
        ]

        total_success = 0

        for agent_num, script_name, output_file in agents:
            success, output = self.run_agent(agent_num, script_name)

            if not success:
                print(f"\n[ERROR] Agent{agent_num} 실행 실패. 파이프라인 중단.")
                break

            # 출력 파일 확인
            output_path = os.path.join(config.BASE_DIRECTORY, output_file)
            file_exists, file_info = self.check_output_file(output_path)

            if file_exists:
                print(f"[OK] 출력 파일 생성 확인: {output_file} ({file_info})")
                total_success += 1
            else:
                print(f"[WARN] 출력 파일 생성 실패: {output_file} ({file_info})")

        # 실행 요약
        end_time = datetime.now()
        total_elapsed = (end_time - self.start_time).total_seconds()

        print(f"\n{'#'*60}")
        print(f"  실행 완료")
        print(f"  종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  총 소요 시간: {total_elapsed:.2f}초")
        print(f"  성공: {total_success}/{len(agents)}")
        print(f"{'#'*60}\n")

        # 로그 저장
        self.save_log()

        return total_success == len(agents)

    def save_log(self):
        """실행 로그를 JSON 파일로 저장"""
        log_filename = f"execution_log_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        log_path = os.path.join(self.log_dir, log_filename)

        log_data = {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_elapsed': (datetime.now() - self.start_time).total_seconds(),
            'events': self.execution_log
        }

        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            print(f"[LOG] 실행 로그 저장: {log_path}")
        except Exception as e:
            print(f"[WARN] 로그 저장 실패: {e}")


def main():
    """메인 실행 함수"""
    print("HAZOP 자동화 시스템 v1.0")
    print("=" * 60)

    try:
        pipeline = HAZOPPipeline()
        success = pipeline.run_pipeline()

        if success:
            print("\n[SUCCESS] 모든 Agent가 정상적으로 완료되었습니다.")
            return 0
        else:
            print("\n[FAILED] 일부 Agent 실행이 실패했습니다.")
            return 1

    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] 사용자에 의해 중단되었습니다.")
        return 2
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류 발생: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
