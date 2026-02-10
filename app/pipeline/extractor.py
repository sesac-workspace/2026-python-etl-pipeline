import json
import shutil
import traceback
from pathlib import Path
from typing import Any, List, Dict
from docling.document_converter import DocumentConverter

from app.core.logger import logger
from app.core.config import settings

class Extractor:
    '''
    # 데이터 추출 및 전처리를 담당하는 클래스

    Attributes:
        _original_json_path     (Path): 메타 데이터 JSON 파일의 경로
        _original_json_filename (str) : 메타 데이터 JSON 파일의 이름
        _converter (DocumentConverter): Docling 기반의 문서 변환기 객체
    '''
    def __init__(self, original_json_path: Path) -> None:
        '''
        Raises:
            RuntimeError: Extractor 초기화 중 오류 발생
        '''
        self._original_json_path: Path = original_json_path
        self._original_json_filename: str = self._original_json_path.name

        try:
            self._converter = DocumentConverter()
            logger.info('Extractor 초기화를 완료했습니다.')

        except Exception as error:
            crit_msg: str = f'Extractor 초기화 중 알 수 없는 오류가 발생했습니다: {error}'
            logger.critical(msg=crit_msg)
            raise RuntimeError(crit_msg)

    def run(self) -> Path:
        '''
        # Extract 단계의 전체 로직을 순차적으로 실행하는 함수

        Returns:
            Path: 최종 병합되어 Transform 단계로 전달할 JSON 파일의 경로
        '''
        # 1. 메타데이터 평탄화
        rawdata = self._load_json(load_path=self._original_json_path)
        flattened_data = self._flatten_metadata(rawdata=rawdata)
        flattened_path = self._save_flattened_json(save_data=flattened_data)

        # 2. PDF 파일을 마크다운 문서로 변환 (Docling 활용)
        self._convert_pdfs_to_markdown()

        # 4. 마크다운 문서와 메타 데이터를 병합
        final_path = self._merge_metadata_and_markdown(flattened_path)

        logger.info(f'Extract 단계를 완료했습니다: {final_path}')
        return final_path

    def _load_json(self, load_path: Path) -> List[Dict[str, Any]]:
        '''
        # JSON 파일을 로드하여 딕셔너리 리스트로 변환하는 함수

        Args:
            load_path (Path): 로드할 JSON 파일의 경로

        Returns:
            List[Dict[str, Any]]: 로드된 JSON 데이터
        '''
        try:
            with open(file=load_path, mode='r', encoding='utf-8') as file:
                return json.load(file)

        except Exception as error:
            logger.error(f'JSON 파일 로드 중 알 수 없는 오류가 발생했습니다. ({load_path}): {error}')
            return []

    def _save_json(self, save_data: List[Dict[str, Any]], save_path: Path) -> None:
        '''
        # 딕셔너리 리스트를 JSON 파일로 저장하는 함수

        Args:
            save_data (List[DIct[str, Any]]): JSON 파일로 저장할 딕셔너리 리스트
            save_path (Path)                : JSON 파일로 저장할 경로
        '''
        try:
            with open(file=save_path, mode='w', encoding='utf-8') as file:
                json.dump(obj=save_data, fp=file, ensure_ascii=False, indent=4)

        except Exception as error:
            logger.error(f'JSON 파일 저장 중 알 수 없는 오류가 발생했습니다. ({save_path}): {error}')

    def _flatten_metadata(self, rawdata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''
        # PDF 파일 단위로 객체를 1:1로 평탄화하는 함수

        Args:
            rawdata (List[Dict[str, Any]]): 메타 데이터 딕셔너리 리스트

        Returns:
            List[Dict[str, Any]]: 평탄화된 메타 데이터 딕셔너리 리스트
        '''
        flattened_metadata = []

        for item in rawdata:
            pdf_names = item.get('pdf_filenames')
            pdf_links = item.get('pdf_files')

            if not pdf_names:
                continue

            for index, pdf_name in enumerate(pdf_names):
                new_item = item.copy()
                new_item.pop('pdf_filenames', None)
                new_item.pop('pdf_files', None)
                new_item['pdf_filename'] = pdf_name
                new_item['pdf_file'] = pdf_links[index] if index < len(pdf_links) else None

                flattened_metadata.append(new_item)

        logger.info(f'메타데이터 평탄화를 완료했습니다. (총 {len(flattened_metadata)}건)')

        return flattened_metadata

    def _save_flattened_json(self, save_data: List[Dict[str, Any]]) -> Path:
        '''
        # 평탄화된 메타 데이터를 JSON 파일로 저장하는 함수

        Args:
            save_data (List[Dict[str, Any]]): JSON 파일로 저장할 평탄화된 메타 데이터

        Returns:
            Path: 평탄화된 메타 데이터가 저장된 JSON 파일의 경로
        '''
        save_path = settings.METADATA_PATH / f'flattened_{self._original_json_filename}'
        self._save_json(save_data=save_data, save_path=save_path)

        return save_path

    def _convert_pdfs_to_markdown(self) -> None:
        '''
        # 모든 PDF 파일을 Docling을 통해 마크다운 문서로 변환하는 함수
        '''
        pdf_files = list(settings.RAWDATA_PATH.glob('*.pdf'))

        if not pdf_files:
            logger.warning('처리할 PDF 파일이 없습니다.')
            return

        logger.info(f'PDF 파일을 마크다운 문서로 변환합니다. (총 {len(pdf_files)}개)')

        for index, pdf_path in enumerate(pdf_files, 1):
            md_path = settings.MARKDOWN_PATH / f'{pdf_path.stem}.md'

            # 이미 변환된 파일 건너뛰기
            if md_path.exists():
                logger.debug(f'[{index}/{len(pdf_files)}] 이미 마크다운 문서로 변환된 PDF 파일입니다: {pdf_path.name}')
                continue

            try:
                # 1. 문서 변환 실행
                result = self._converter.convert(pdf_path)

                # 2. Markdown 포맷으로 추출
                contents = result.document.export_to_markdown()

                # 3. 파일 저장
                with open(file=md_path, mode='w', encoding='utf-8') as file:
                    file.write(contents)

                logger.debug(f'[{index}/{len(pdf_files)}] 마크다운 문서 변환에 성공했습니다. ({pdf_path.name})')

            except Exception as error:
                # 변환 실패 시 로그만 남기고 다음 파일 진행 (파이프라인 중단 방지)
                logger.error(f'[{index}/{len(pdf_files)}] 마크다운 문서 변환에 실패했습니다: ({pdf_path.name}): {error}')
                logger.debug(traceback.format_exc())

    def _merge_metadata_and_markdown(self, flattened_path: Path) -> Path:
        '''
        # 변환된 마크다운 문서와 평탄화된 메타 데이터를 병합하는 함수

        Args:
            flattened_path (Path): 평탄화된 JSON 파일의 경로

        Returns:
            Path: 마크다운 문서와 메타 데이터가 병합된 최종 JSON 파일의 경로
        '''
        metadatas = self._load_json(flattened_path)

        for item in metadatas:
            pdf_filename = item.get('pdf_filename')

            if not pdf_filename:
                item['contents'] = None
                continue

            md_path = settings.MARKDOWN_PATH / f'{Path(pdf_filename).stem}.md'

            if md_path.exists():
                with open(md_path, 'r', encoding='utf-8') as f:
                    item['contents'] = f.read()

            else:
                item['contents'] = None
                logger.debug(f'매칭되는 마크다운 문서가 없습니다: {pdf_filename}')

        final_path = settings.IMPORT_PATH / f'final_{self._original_json_filename}'
        self._save_json(save_data=metadatas, save_path=final_path)

        return final_path