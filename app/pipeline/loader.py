import json
import pickle
import shutil
from tqdm import tqdm
from pathlib import Path
from typing import List, Dict, Any
from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings as HFembeddings

from app.core.logger import logger
from app.core.config import settings

class Loader:
    '''
    # 데이터 인덱싱 및 적재를 담당하는 클래스

    Attributes:
        _kiwi         (Kiwi)        : BM25 토큰화를 위한 한국어 형태소 분석기
        _embedding    (HFembeddings): 텍스트 임베딩 모델
    '''
    def __init__(self) -> None:
        '''
        Raises:
            RuntimeError: Transformer 초기화 중 오류 발생
        '''
        try:
            self._kiwi = Kiwi()
            self._embedding = HFembeddings(
                model_name='BAAI/bge-m3',
                model_kwargs={'device': 'cuda'},
                encode_kwargs={'normalize_embeddings': True}
            )

            logger.info('Loader 초기화를 완료했습니다.')
            
        except Exception as error:
            raise RuntimeError(f'Loader 초기화 실패: {error}')

    def run(self, input_path: Path) -> None:
        '''
        # Load 단계의 전체 로직을 순차적으로 실행하는 함수

        Args:
            input_path (Path): Transformer가 생성한 최종 JSON 파일의 경로
        '''
        if not input_path.exists():
            logger.error(f'적재할 데이터 파일이 없습니다: {input_path}')
            return

        # 1. 데이터 로드 (역직렬화)
        with open(input_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        logger.info(f'청크 데이터를 전부 로드했습니다. (총{len(chunks)}개)')

        # 2. 데이터 분류 (In-Memory Routing)
        parent_store: Dict[str, Any] = {}
        vector_docs: List[Document] = []
        bm25_texts: List[str] = []
        bm25_ids: List[str] = []

        for chunk in tqdm(chunks, desc='Classifying Data'):
            doc_type = chunk.get('doc_type')
            
            # Parent Store
            if doc_type == 'parent':
                parent_store[chunk['id']] = chunk
            
            # Vector DB & BM25
            elif doc_type == 'child':
                metadata = chunk.get('metadata', {}).copy()
                metadata['parent_id'] = chunk.get('parent_id')
                metadata['chunk_id'] = chunk.get('id')
                
                # Vector Doc 생성
                doc = Document(page_content=chunk.get('page_content', ''), metadata=metadata)
                vector_docs.append(doc)
                
                # BM25 Text 준비
                bm25_texts.append(chunk.get('page_content', ''))
                bm25_ids.append(chunk.get('id'))

        # 3. 인젝션 (Injection)
        self._inject_document_store(parent_store)
        self._inject_vector_db(vector_docs)
        self._inject_bm25_index(bm25_texts, bm25_ids)

        logger.info('모든 데이터 적재에 성공했습니다.')

    def _inject_document_store(self, data: Dict[str, Any]) -> None:
        '''
        # Parent Chunk를 Key-Value 형태로 구성해 JSON 파일로 저장하는 함수

        Args:
            data: Dict[str, Any]: 최종 JSON 데이터
        '''
        store_path = settings.EXPORT_PATH / 'document_store.json'

        try:
            with open(file=store_path, mode='w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            logger.info(f'Document Store 저장에 성공했습니다. ({store_path})')

        except Exception as error:
            logger.error(f'Document Store 저장에 실패했습니다. ({store_path}): {error}')

    def _inject_vector_db(self, docs: List[Document]) -> None:
        '''
        # Child Chunk를 ChromaDB에 적재하는 함수

        Args:
            docs (List[Document]): 마크다운 문서와 메타 데이터를 포함한 데이터 리스트
        '''
        if not docs:
            return
        
        vector_path: Path = settings.EXPORT_PATH / 'chromadb'

        try:
            # 기존 DB 초기화
            if vector_path.exists():
                shutil.rmtree(vector_path)
            
            Chroma.from_documents(
                documents=docs,
                embedding=self._embedding,
                persist_directory=str(vector_path),
                collection_name='rag_collection'
            )

            logger.info(f'ChromaDB 구축에 성공했습니다. ({vector_path})')

        except Exception as error:
            logger.critical(f'ChromaDB 구축에 실패했습니다. ({vector_path}): {error}')

    def _inject_bm25_index(self, ids: List[str], texts: List[str]) -> None:
        '''
        # Child Chunk의 본문을 기반으로 BM25 통계 모델을 학습시키고 Pickle 파일로 저장하는 함수

        Args:
            ids   (List[str]): Child Chunk의 고유 식별자 리스트
            texts (List[str]): BM25 통계 모델을 학습시킬 Child Chunk 본문 리스트
        '''
        if not texts:
            return

        index_path: Path = settings.EXPORT_PATH / 'bm25_index.pkl'

        try:
            tokenized_corpus = [
                self._tokenize_korean(text) 
                for text in tqdm(texts, desc='Tokenizing for BM25')
            ]

            bm25 = BM25Okapi(tokenized_corpus)
            bm25_data = {'model': bm25, 'doc_ids': ids}

            with open(file=index_path, mode='wb') as file:
                pickle.dump(bm25_data, file)

            logger.info(f'BM25 Index 저장에 성공했습니다. ({index_path})')

        except Exception as error:
            logger.critical(f'BM25 Index 저장에 실패했습니다. ({index_path}): {error}')

    def _tokenize_korean(self, text: str) -> List[str]:
        '''
        # 형태소 분석기를 이용해 한국어를 토큰화하는 함수

        Args:
            text (str): 분석하여 토큰화할 텍스트

        Returns:
            List[str]: 한국어 형태소로 분리되어 토큰화된 데이터 리스트
        '''
        tokens = []

        try:
            results = self._kiwi.tokenize(text)

            for token in results:
                if token.tag in ['NNG', 'NNP', 'SL', 'SN']:
                    tokens.append(token.form)

        except Exception:
            pass

        return tokens