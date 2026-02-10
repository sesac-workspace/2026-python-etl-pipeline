import os
import sys
import argparse

from app.core.logger import logger
from app.orchestrator import Orchestrator

def parse_args() -> argparse.Namespace:
    '''
    # 명령줄에서 인자를 파싱하는 함수

    Returns:
        argparse.Namespace: 명령줄에서 파싱된 인자 객체
    '''
    parser = argparse.ArgumentParser(
        description='ETL 파이프라인'
    )
    parser.add_argument(
        '--input_json',
        type=str,
        required=True,
        help='메타데이터가 담긴 JSON 파일의 경로'
    )
    return parser.parse_args()

def main():
    '''
    # ELT 파이프라인 및 명령줄 인자 파서 실행 함수
    '''
    try:
        args = parse_args()

        if not os.path.exists(args.input_json):
            raise FileNotFoundError(f'입력 파일을 찾을 수 없습니다: {args.input_json}')
        
        # 파이프라인 생성 및 실행
        pipeline = Orchestrator(input_json_path=args.input_json)
        pipeline.execute()

    except Exception as error:
        logger.critical(f'프로그램 실행 중 알 수 없는 오류가 발생했습니다: {error}')
        sys.exit(1)

if __name__ == '__main__':
    main()