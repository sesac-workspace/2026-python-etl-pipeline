import uuid
import json
import hashlib
from pathlib import Path
from typing import Any, List, Dict, Generator
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logger import logger
from app.core.config import settings

class Transformer:
    '''
    # 데이터 구조화 및 청킹을 담당하는 클래스

    Attributes:
        _markdown_splitter (MarkdownHeaderTextSplitter)    : 제목을 기준으로 문맥을 보존하는 분할기
        _parent_splitter   (RecursiveCharacterTextSplitter): 문맥을 물리적 크기 제한하는 분할기
        _child_splitter    (RecursiveCharacterTextSplitter): 벡터 검색 정확도 향상을 위한 작은 단위의 분할기
    '''
    def __init__(self) -> None:
        '''
        Raises:
            RuntimeError: Transformer 초기화 중 오류 발생
        '''
        try:
            # 1. 헤더 분할기 (문맥 보존)
            self._markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[('#', 'h1'), ('##', 'h2'), ('###', 'h3')],
                strip_headers=False
            )
            # 2. Parent 분할기 (물리적 길이 제한)
            self._parent_splitter = RecursiveCharacterTextSplitter(
                separators=['\n\n', '\n', ' ', ''],
                chunk_size=2000,
                chunk_overlap=200,
            )
            # 3. Child 분할기 (검색용 정밀 분할)
            self._child_splitter = RecursiveCharacterTextSplitter(
                separators=['\n\n', '\n', ' ', ''],
                chunk_size=400,
                chunk_overlap=50,
            )

            logger.info('Transformer 초기화를 완료했습니다.')
        
        except Exception as error:
            raise RuntimeError(f'Transformer 초기화 중 알 수 없는 오류가 발생했습니다: {error}')

    def run(self, input_path: Path) -> Path:
        '''
        # Transform 단계의 전체 로직을 순차적으로 실행하는 함수

        Args:
            input_path (Path): Extractor가 생성한 최종 JSON 파일의 경로

        Returns:
            Path: 청킹이 완료된 JSON 파일의 경로
        '''
        if not input_path.exists():
            raise FileNotFoundError(f'파일을 찾을 수 없습니다: {input_path}')

        # 출력 경로 설정
        output_path = settings.MODIFY_PATH / f'chunked_{input_path.stem}.json'

        # 데이터 로드
        with open(file=input_path, mode='r', encoding='utf-8') as file:
            json_data = json.load(file)

        # 스트리밍 처리 및 저장
        chunk_generator = self._process_stream(json_data)
        saved_count = self._save_chunks_stream(output_path, chunk_generator)

        logger.info(f'Transformation 완료했습니다: {output_path}')
        return output_path
    
    def _create_chunk_id(self, index: int, source: str, content: str, suffix: str = '') -> str:
        '''
        # 데이터 기반의 고유 식별자를 생성하는 함수

        Args:
            index   (str): 청크 순서
            source  (str): 원본 소스
            content (str): 청크 본문
            suffix  (str): 식별자 충돌을 방지하기 위한 접미사
        '''
        seed = f'{index}_{source}_{hashlib.md5(content.encode()).hexdigest()}_{suffix}'
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))

    def _process_stream(self, json_data: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        '''
        # 대용량 데이터를 순차적으로 처리하여 반환하는 제너레이터 함수

        Args:
            json_data (List[Dict[str, Any]])
        Returns:
            Generator[Dict[str, Any], None, None]
        '''
        for item in json_data:
            chunks = self._split_markdown_to_chunk(item)

            for chunk in chunks:
                yield chunk

    def _split_markdown_to_chunk(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        '''
        # 단일 문서를 상위 문서 검색 전략으로 청킹하는 함수

        Args:
            item (Dict[str, Any]): 마크다운 문서와 메타 데이터가 표함된 딕셔너리
        Returns:
            List[Dict[str, Any]]: 전략에 맞추어 생성된 Parent, Child Chunk 딕셔너리 리스트
        '''
        contents = item.get('contents')
        if not contents:
            return []

        # 메타데이터 준비
        base_metadata = {
            k: v for k, v in item.items() if k != 'contents'
        }
        
        # 1. Parent Chunking
        header_splits = self._markdown_splitter.split_text(contents)
        parent_docs = self._parent_splitter.split_documents(header_splits)

        serialized_chunks = []

        for parent_index, parent_doc in enumerate(parent_docs):
            # Parent ID 생성
            parent_id = self._create_chunk_id(
                index=parent_index,
                content=parent_doc.page_content,
                source=str(base_metadata.get('pdf_filename', 'unknown')),
                suffix='parent'
            )

            # Parent 메타데이터 병합
            parent_meta = {**base_metadata, **parent_doc.metadata}

            # Parent 추가
            serialized_chunks.append({
                'id': parent_id,
                'doc_type': 'parent',
                'parent_id': None,
                'page_content': parent_doc.page_content,
                'metadata': parent_meta,
            })

            # 2. Child Chunking
            child_docs = self._child_splitter.split_text(parent_doc.page_content)
            
            for child_index, child_doc in enumerate(child_docs):
                child_id = self._create_chunk_id(
                    index=child_index,
                    content=child_doc,
                    source=parent_id,
                    suffix='child'
                )

                # Child 추가 (Parent 메타데이터 상속)
                serialized_chunks.append({
                    'id': child_id,
                    'doc_type': 'child',
                    'parent_id': parent_id,
                    'page_content': child_doc,
                    'metadata': parent_meta,
                })

        return serialized_chunks

    def _save_chunks_stream(self, save_path: Path, chunk_generator: Generator) -> int:
        '''
        # 스트리밍 방식으로 제너레이터에서 청크를 하나씩 전달 받아 저장하는 함수

        Args:
            save_path       (Path)     : 전달 받은 청크를 저장할 파일의 경로
            chunk_generator (Generator): 청크를 생성하는 이터레이터

        Returns:
            int: 저장된 청크의 총 개수
        '''
        count = 0

        try:
            with open(file=save_path, mode='w', encoding='utf-8') as file:
                file.write('[\n')
                first = True

                for chunk in chunk_generator:
                    if not first:
                        file.write(',\n')

                    json.dump(chunk, file, ensure_ascii=False, indent=4)
                    first = False
                    count += 1

                file.write('\n]')

            return count

        except Exception as error:
            logger.error(f'청크 저장 중 알 수 없는 오류가 발생했습니다: {error}')
            if save_path.exists():
                save_path.unlink() # 불완전 파일 삭제 (Rollback)

            raise