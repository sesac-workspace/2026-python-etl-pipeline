from pathlib import Path

from app.core.logger import logger
from app.pipeline.extractor import Extractor
from app.pipeline.transformer import Transformer
from app.pipeline.loader import Loader

class Orchestrator:
    '''
    # ETL 파이프라인의 전체 흐름을 제어하는 클래스

    Attributes:
        json_path   (Path)       : 메타 데이터 JSON 파일의 경로
        extractor   (Extractor)  : 데이터 추출 및 전처리를 담당하는 인스턴스
        transformer (Transformer): 데이터 구조화 및 청킹을 담당하는 인스턴스
        loader      (Loader)     : 데이터 인덱싱 및 적재를 담당하는 인스턴스
        
    '''
    def __init__(self, input_json_path: str):
        '''
        Args:
            input_json_path (str): 명령줄에서 파싱한 메타 데이터 JSON 파일의 경로
        '''
        self.json_path = Path(input_json_path) # 문자열로 받아 Path로 변환
        
        # 각 단계(Step)별 처리기 인스턴스화
        self.extractor = Extractor(self.json_path)
        self.transformer = Transformer()
        self.loader = Loader()

    def execute(self):
        '''
        # ETL 파이프라인을 순차적으로 실행하는 함수

        Raises:
            Exception: 파이프라인 실행 중 알 수 없는 오류 발생
        '''
        try:
            # Step 1. Extract
            extracted_path = self.extractor.run()

            # Step 2. Transform
            transformed_path = self.transformer.run(extracted_path)

            # Step 3. Load
            self.loader.run(transformed_path)
        
        except Exception as error:
            logger.critical(f'ETL 파이프라인 실행 중 알 수 없는 오류가 발생했습니다: {error}', exc_info=True)
            raise