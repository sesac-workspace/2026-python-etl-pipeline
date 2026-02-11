from typing import Final, List
from pathlib import Path

class Config:
    '''
    # 프로젝트에 사용되는 상수 및 경로를 관리하는 설정 클래스

    Attributes:
        LOG_MAX_BYTE  (str) : 로그 파일 하나의 최대 용량
        BACKUP_FILES  (str) : 유지할 백업 로그 파일 개수
        ROOT_PATH     (Path): 프로젝트의 최상위 디렉토리 경로
        LOG_PATH      (Path): 로그 파일이 저장되는 디렉토리 경로
        DATA_PATH     (Path): 데이터를 관리하는 디렉토리 경로
        RAWDATA_PATH  (Path): 원천 데이터를 관리하는 디렉토리 경로
        METADATA_PATH (Path): 메타 데이터를 관리하는 디렉토리 경로
        PIPELINE_PATH (Path): 파이프라인 중간 산출물을 관리하는 디렉토리 경로
        IMPORT_PATH   (Path): Extract 단계를 관리하는 디렉토리 경로
        MODIFY_PATH   (Path): Transform 단계를 관리하는 디렉토리 경로
        EXPORT_PATH   (Path): Load 단계를 관리하는 디렉토리 경로
        MARKDOWN_PATH (Path): Extract 단계에서 변환된 마크다운 문서를 관리하는 디렉토리 경로
    '''
    # 로그 설정
    LOG_MAX_BYTE: Final[int] = 10 * 1024 * 1024  # 10MB
    BACKUP_FILES: Final[int] = 5

    # 경로 설정
    ROOT_PATH: Final[Path] = Path(__file__).parents[2]

    # 시스템 경로 설정
    LOG_PATH: Final[Path] = ROOT_PATH / 'log'
    DATA_PATH: Final[Path] = ROOT_PATH / 'data'

    # 산출물 경로 설정
    RAWDATA_PATH: Final[Path] = DATA_PATH / 'rawdata'
    METADATA_PATH: Final[Path] = DATA_PATH / 'metadata'
    PIPELINE_PATH: Final[Path] = DATA_PATH / 'pipeline'

    # 파이프라인 경로 설정
    IMPORT_PATH: Final[Path] = PIPELINE_PATH / 'import'
    MODIFY_PATH: Final[Path] = PIPELINE_PATH / 'modify'
    EXPORT_PATH: Final[Path] = PIPELINE_PATH / 'export'
    MARKDOWN_PATH: Final[Path] = IMPORT_PATH / 'markdown'

    # 디렉토리가 존재하지 않으면 생성, 존재하면 건너뛰기
    @classmethod
    def setup_directories(cls) -> None:
        directories: List[Path] = [
            cls.LOG_PATH, cls.DATA_PATH,
            cls.RAWDATA_PATH, cls.METADATA_PATH, cls.PIPELINE_PATH,
            cls.IMPORT_PATH, cls.MODIFY_PATH, cls.EXPORT_PATH, cls.MARKDOWN_PATH,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# 전역 설정 객체 생성 및 디렉토리 초기화
settings = Config()
settings.setup_directories()