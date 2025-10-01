# -*- coding: utf-8 -*-
"""
HAZOP 자동화 통합 실행 스크립트 (모든 노드 자동 처리)
Agent2에서 노드를 추출하고, 각 노드별로 Agent3~5를 반복 실행합니다.
"""

import os
import sys
import time
import json
import re
from datetime import datetime
import subprocess

# 설정 파일 import
from config import config
from hazop_utils import read_txt, write_txt, get_output_path


class HAZOPPipelineAllNodes:
    """HAZOP 분석 통합 파이프라인 (모든 노드 자동 처리)"""

    def __init__(self, log_dir=None, agents_to_run=None):
        self.log_dir = log_dir or os.path.join(config.BASE_DIRECTORY, 'logs')
        self.execution_log = []
        self.start_time = None
        self.nodes = []
        # agents_to_run: 실행할 Agent 번호 리스트 (예: [1,2] 또는 [3,4,5] 또는 [6])
        self.agents_to_run = agents_to_run if agents_to_run else [3,4,5,6]

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

    def extract_nodes(self, agent2_output):
        """Agent2 출력에서 노드 목록 추출 (JSON 파싱)"""
        nodes = []

        try:
            # ```json``` 블록 제거
            if "```json" in agent2_output:
                json_str = agent2_output.split("```json")[1].split("```")[0].strip()
            elif "```" in agent2_output:
                json_str = agent2_output.split("```")[1].split("```")[0].strip()
            else:
                json_str = agent2_output

            # JSON 파싱
            agent2_data = json.loads(json_str)
            node_list = agent2_data.get('nodes', [])

            for node in node_list:
                nodes.append({
                    'number': node.get('node_id'),
                    'name': node.get('node_name', '')
                })

            print(f"\n[INFO] 추출된 노드 수: {len(nodes)}")
            for node in nodes:
                print(f"  - Node {node['number']}: {node['name']}")

        except json.JSONDecodeError as e:
            print(f"[ERROR] Agent2 JSON 파싱 실패: {e}")
            print("[ERROR] 텍스트 패턴 매칭으로 폴백...")

            # 폴백: 텍스트 패턴 매칭 (레거시)
            pattern = r'###\s*Node\s+(\d+):\s*(.+)'
            matches = re.findall(pattern, agent2_output, re.MULTILINE)

            for node_num, node_name in matches:
                nodes.append({
                    'number': int(node_num),
                    'name': node_name.strip()
                })

            print(f"\n[INFO] (폴백) 추출된 노드 수: {len(nodes)}")

        except Exception as e:
            print(f"[ERROR] 노드 추출 중 오류 발생: {e}")

        return nodes

    def run_agent(self, agent_num, script_name, node_num=None):
        """개별 Agent 실행"""
        if node_num:
            agent_name = f"Agent{agent_num} (Node {node_num})"
        else:
            agent_name = f"Agent{agent_num}"

        print(f"\n{'='*60}")
        print(f"  {agent_name} 실행 중...")
        print(f"{'='*60}")

        start = time.time()

        try:
            # 환경변수로 노드 번호 전달
            env = os.environ.copy()
            if node_num:
                env['TARGET_NODE'] = str(node_num)

            # 서브프로세스로 Agent 실행
            result = subprocess.run(
                [sys.executable, script_name],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=False,  # 바이너리 모드로 변경
                env=env
            )

            elapsed = time.time() - start

            # 바이트를 문자열로 안전하게 변환
            try:
                stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
                stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
            except:
                stdout = str(result.stdout)
                stderr = str(result.stderr)

            if result.returncode == 0:
                self.log_event(agent_name, 'SUCCESS', '정상 완료', elapsed)
                return True, stdout
            else:
                error_msg = stderr or stdout
                self.log_event(agent_name, 'FAILED', f'실행 실패: {error_msg[:200]}', elapsed)
                return False, error_msg

        except Exception as e:
            elapsed = time.time() - start
            self.log_event(agent_name, 'ERROR', f'예외 발생: {str(e)}', elapsed)
            return False, str(e)

    def run_pipeline(self):
        """전체 파이프라인 실행"""
        self.start_time = datetime.now()
        print(f"\n{'#'*60}")
        print(f"  HAZOP 자동화 통합 실행 시작")
        print(f"  실행할 Agent: {self.agents_to_run}")
        print(f"  시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")

        # Step 1: Agent1 - P&ID 분석
        if 1 in self.agents_to_run:
            success, output = self.run_agent(1, "gpt4o_P&ID_input(Agent1).py")
            if not success:
                print("[ERROR] Agent1 실패. 파이프라인 중단.")
                return False
        else:
            print("[SKIP] Agent1 건너뜀")

        # Step 2: Agent2 - 노드 분리
        if 2 in self.agents_to_run:
            success, output = self.run_agent(2, "GPT4o Node (Agent2).py")
            if not success:
                print("[ERROR] Agent2 실패. 파이프라인 중단.")
                return False
        else:
            print("[SKIP] Agent2 건너뜀")

        # Agent2 결과에서 노드 추출 (Agent 3,4,5 실행 시 필요)
        if any(agent in self.agents_to_run for agent in [3, 4, 5]):
            agent2_output = read_txt(get_output_path('Agent2.txt'))
            self.nodes = self.extract_nodes(agent2_output)

            if not self.nodes:
                print("[ERROR] 노드가 추출되지 않았습니다.")
                return False

        # Step 3-5: 각 노드별로 Agent3~5 실행
        all_agent3_results = []
        all_agent4_results = []
        all_agent5_results = []

        if any(agent in self.agents_to_run for agent in [3, 4, 5]):
            for node in self.nodes:
                node_num = node['number']
                node_name = node['name']

                print(f"\n{'#'*60}")
                print(f"  Node {node_num}: {node_name} 처리 시작")
                print(f"{'#'*60}")

                # Agent3: 공정 변수 식별
                if 3 in self.agents_to_run:
                    success, _ = self.run_agent(3, "GPT4o Parameter_Guideword (Agent3).py", node_num)
                    if success:
                        # 파일에서 결과 읽기
                        try:
                            output = read_txt(get_output_path('Agent3.txt'))
                            all_agent3_results.append(output)
                        except:
                            print(f"[WARNING] Node {node_num} Agent3 파일 읽기 실패")
                    else:
                        print(f"[WARNING] Node {node_num} Agent3 실패")
                else:
                    print(f"[SKIP] Node {node_num} Agent3 건너뜀")

                # Agent4: 이탈 생성
                if 4 in self.agents_to_run:
                    success, _ = self.run_agent(4, "GPT4o CreateDeviation (Agent4).py", node_num)
                    if success:
                        # 파일에서 결과 읽기
                        try:
                            output = read_txt(get_output_path('Agent4.txt'))
                            all_agent4_results.append(output)
                        except:
                            print(f"[WARNING] Node {node_num} Agent4 파일 읽기 실패")
                    else:
                        print(f"[WARNING] Node {node_num} Agent4 실패")
                else:
                    print(f"[SKIP] Node {node_num} Agent4 건너뜀")

                # Agent5: 안전장치 분석
                if 5 in self.agents_to_run:
                    success, _ = self.run_agent(5, "GPT4o Safeguard (Agent5).py", node_num)
                    if success:
                        # 파일에서 결과 읽기
                        try:
                            output = read_txt(get_output_path('Agent5.txt'))
                            all_agent5_results.append(output)
                        except:
                            print(f"[WARNING] Node {node_num} Agent5 파일 읽기 실패")
                    else:
                        print(f"[WARNING] Node {node_num} Agent5 실패")
                else:
                    print(f"[SKIP] Node {node_num} Agent5 건너뜀")

        # 통합 결과 저장
        if any(agent in self.agents_to_run for agent in [3, 4, 5]):
            print(f"\n{'='*60}")
            print("  모든 노드 결과 통합 중...")
            print(f"{'='*60}")

            # Agent3 통합 결과
            if 3 in self.agents_to_run and all_agent3_results:
                agent3_combined = '\n\n'.join(all_agent3_results)
                write_txt(get_output_path('Agent3_all_nodes.txt'), agent3_combined)
                print(f"[OK] Agent3 통합 결과 저장")

            # Agent4 통합 결과
            if 4 in self.agents_to_run and all_agent4_results:
                agent4_combined = '\n\n'.join(all_agent4_results)
                write_txt(get_output_path('Agent4_all_nodes.txt'), agent4_combined)
                print(f"[OK] Agent4 통합 결과 저장")

            # Agent5 통합 결과
            if 5 in self.agents_to_run and all_agent5_results:
                agent5_combined = '\n\n'.join(all_agent5_results)
                write_txt(get_output_path('Agent5_all_nodes.txt'), agent5_combined)
                print(f"[OK] Agent5 통합 결과 저장")

        # Step 6: Agent6 - 최종 테이블 생성
        if 6 in self.agents_to_run:
            print(f"\n{'='*60}")
            print("  최종 HAZOP 테이블 생성 중...")
            print(f"{'='*60}")

            success, output = self.run_agent(6, "GPT4o HAZOP Table (Agent6).py")
            if not success:
                print("[WARNING] Agent6 실행 실패")
        else:
            print("\n[SKIP] Agent6 건너뜀")

        # 실행 요약
        end_time = datetime.now()
        total_elapsed = (end_time - self.start_time).total_seconds()

        print(f"\n{'#'*60}")
        print(f"  실행 완료")
        print(f"  종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  총 소요 시간: {total_elapsed:.2f}초")
        print(f"  처리된 노드 수: {len(self.nodes)}")
        print(f"{'#'*60}\n")

        # 로그 저장
        self.save_log()

        return True

    def save_log(self):
        """실행 로그를 JSON 파일로 저장"""
        log_filename = f"execution_log_all_nodes_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        log_path = os.path.join(self.log_dir, log_filename)

        log_data = {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_elapsed': (datetime.now() - self.start_time).total_seconds(),
            'nodes_processed': [{'number': n['number'], 'name': n['name']} for n in self.nodes],
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
    import argparse

    parser = argparse.ArgumentParser(
        description='HAZOP 자동화 시스템',
        epilog='예시: python main_integrated_all_nodes.py --agents 1 2  (Agent 1,2만 실행)'
    )
    parser.add_argument(
        '--agents',
        type=int,
        nargs='+',
        choices=[1, 2, 3, 4, 5, 6],
        help='실행할 Agent 번호들 (예: --agents 1 2 또는 --agents 6)'
    )
    args = parser.parse_args()

    print("HAZOP 자동화 시스템 v2.0")
    print("=" * 60)

    # 실행할 Agent 목록
    agents_to_run = args.agents if args.agents else [1, 2, 3, 4, 5, 6]
    print(f"실행할 Agent: {agents_to_run}")
    print("=" * 60)

    try:
        pipeline = HAZOPPipelineAllNodes(agents_to_run=agents_to_run)
        success = pipeline.run_pipeline()

        if success:
            print("\n[SUCCESS] 선택한 Agent 처리가 완료되었습니다.")
            return 0
        else:
            print("\n[FAILED] 일부 처리가 실패했습니다.")
            return 1

    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] 사용자에 의해 중단되었습니다.")
        return 2
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
