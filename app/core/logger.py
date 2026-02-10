import sys
import logging
from logging import Formatter, StreamHandler
from logging.handlers import RotatingFileHandler

from app.core.config import settings

class Logger:
    '''
    # 애플리케이션 전역에서 사용하는 로깅 인스턴스를 설정하는 클래스

    Attributes:
        _logger (Logger): 실제 로깅 작업을 수행하는 Looger 인스턴스
        _name   (str)   : 생성되는 로그 파일의 이름
        _level  (int)   : 로그를 출력하는 레벨 설정
        _date   (str)   : 로그에 출력되는 날짜와 시간 형식
        _format (str)   : 로그에 출력되는 항목과 표시 형식
    '''
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger('app')
        self._name: str = 'etl-pipeline.log'
        self._level: int = logging.INFO
        self._date: str = '%Y-%m-%d %H:%M:%S'
        self._format: str = '[%(asctime)s : %(levelname)s] [%(filename)s : %(lineno)d] %(message)s'

        # 1. 로그 미시지의 출력 레벨 설정
        self._logger.setLevel(self._level)

        # 2. 상위 logger로 전파 방지 (중복 방지)
        self._logger.propagate = False

        # 3. 로그 최종 형식 설정
        self._log_formatter: Formatter = Formatter(
            fmt=self._format,
            datefmt=self._date,
        )

        # 4. 핸들러가 존재하지 않으면 생성
        if not self._logger.hasHandlers():
            self._add_stream_handler()
            self._add_file_handler()

    def _add_stream_handler(self) -> None:
        '''
        # 표준 출력을 위한 StreamHandler 생성하는 함수
        '''
        stream_handler = StreamHandler(sys.stdout)
        stream_handler.setLevel(self._level)
        stream_handler.setFormatter(self._log_formatter)

        self._logger.addHandler(stream_handler)
    
    def _add_file_handler(self) -> None:
        '''
        # 파일 저장을 위한 RotatingFileHandler 생성하는 함수
        '''
        file_handler = RotatingFileHandler(
            filename=settings.LOG_PATH / self._name,
            maxBytes=settings.LOG_MAX_BYTE,
            backupCount=settings.BACKUP_FILES,
            encoding='utf-8',
        )
        file_handler.setLevel(self._level)
        file_handler.setFormatter(self._log_formatter)

        self._logger.addHandler(file_handler)

# 전역 객체로 생성
logger = Logger()._logger