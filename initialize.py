"""
初期化処理モジュール
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4
import sys
import unicodedata
import streamlit as st

from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import constants as ct

def initialize():
    """初期化エントリーポイント"""
    os.makedirs(ct.RAG_TOP_FOLDER_PATH, exist_ok=True)
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)
    
    initialize_session_id()
    initialize_logger()
    initialize_session_state()
    initialize_retriever()

def initialize_logger():
    """ログ設定"""
    logger = logging.getLogger(ct.LOGGER_NAME)
    if logger.hasHandlers():
        return

    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",
        encoding="utf8"
    )
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s, session_id={st.session_state.get('session_id', 'N/A')}: %(message)s"
    )
    log_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

def initialize_session_id():
    """セッションIDの発行"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid4().hex

def initialize_session_state():
    """セッション変数の保持"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def initialize_retriever():
    """Chroma VectorStoreおよびRetrieverの初期化"""
    if "retriever" in st.session_state:
        return

    docs_all, integrated_docs_all = load_data_sources()

    for doc in docs_all + integrated_docs_all:
        doc.page_content = adjust_string(doc.page_content)
        for k, v in list(doc.metadata.items()):
            doc.metadata[k] = adjust_string(v)

    embeddings = OpenAIEmbeddings()
    text_splitter = CharacterTextSplitter(
        chunk_size=ct.CHUNK_SIZE,
        chunk_overlap=ct.CHUNK_OVERLAP,
        separator="\n"
    )

    splitted_docs = text_splitter.split_documents(docs_all)
    splitted_docs.extend(integrated_docs_all)

    # 読み込み結果をログに出力（デバッグ用）
    logger = logging.getLogger(ct.LOGGER_NAME)
    logger.info(f"読み込まれたドキュメント分割数: {len(splitted_docs)}")

    if not splitted_docs:
        splitted_docs = [Document(page_content="社内情報データが見つかりませんでした。", metadata={"source": "system"})]

    # オンメモリで常に最新データをインデックス構築（古いキャッシュによる検索漏れを防止）
    db = Chroma.from_documents(
        documents=splitted_docs,
        embedding=embeddings
    )
    st.session_state.retriever = db.as_retriever(search_kwargs={"k": ct.TOP_K})

def load_data_sources():
    """各種データソースからのドキュメント読込"""
    docs_all = []
    integrated_docs_all = []
    
    if os.path.exists(ct.RAG_TOP_FOLDER_PATH):
        recursive_file_check(ct.RAG_TOP_FOLDER_PATH, docs_all, integrated_docs_all)

    for web_url in ct.WEB_URL_LOAD_TARGETS:
        try:
            loader = WebBaseLoader(web_url)
            docs_all.extend(loader.load())
        except Exception as e:
            logging.getLogger(ct.LOGGER_NAME).warning(f"Web Load Error ({web_url}): {e}")
            
    return docs_all, integrated_docs_all

def recursive_file_check(path, docs_all, integrated_docs_all):
    if os.path.isdir(path):
        for file in os.listdir(path):
            recursive_file_check(os.path.join(path, file), docs_all, integrated_docs_all)
    else:
        file_load(path, docs_all, integrated_docs_all)

def file_load(path, docs_all, integrated_docs_all):
    file_extension = os.path.splitext(path)[1].lower()
    file_name = os.path.basename(path)

    if file_extension in ct.SUPPORTED_EXTENSIONS:
        try:
            loader_func = ct.SUPPORTED_EXTENSIONS[file_extension]
            loader = loader_func(path)
            docs = loader.load()

            if file_name not in ct.CSV_INTEGRATION_TARGETS:
                docs_all.extend(docs)
            else:
                doc_content = "\n=================================\n".join(
                    [d.page_content for d in docs]
                )
                integrated_docs_all.append(Document(page_content=doc_content, metadata={"source": path}))
        except Exception as e:
            logging.getLogger(ct.LOGGER_NAME).warning(f"File Load Error ({file_name}): {e}")

def adjust_string(s):
    if not isinstance(s, str):
        return s
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        return s.encode("cp932", "ignore").decode("cp932")
    return s