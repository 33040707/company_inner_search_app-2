"""
このファイルは、最初の画面読み込み時にのみ実行される初期化処理が記述されたファイルです。
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
    """画面読み込み時に実行する初期化処理"""
    os.makedirs(ct.RAG_TOP_FOLDER_PATH, exist_ok=True)
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)
    
    initialize_session_state()
    initialize_session_id()
    initialize_logger()
    initialize_retriever()

def initialize_logger():
    """ログ出力の設定"""
    logger = logging.getLogger(ct.LOGGER_NAME)
    if logger.hasHandlers():
        return

    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",
        encoding="utf8"
    )
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s, session_id={st.session_state.session_id}: %(message)s"
    )
    log_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

def initialize_session_id():
    """セッションIDの作成"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid4().hex

def initialize_retriever():
    """画面読み込み時にRAGのRetrieverを作成"""
    logger = logging.getLogger(ct.LOGGER_NAME)
    if "retriever" in st.session_state:
        return
    
    docs_all, integrated_docs_all = load_data_sources()

    for doc in docs_all:
        doc.page_content = adjust_string(doc.page_content)
        for key in list(doc.metadata.keys()):
            doc.metadata[key] = adjust_string(doc.metadata[key])
    for doc in integrated_docs_all:
        doc.page_content = adjust_string(doc.page_content)
        for key in list(doc.metadata.keys()):
            doc.metadata[key] = adjust_string(doc.metadata[key])
    
    embeddings = OpenAIEmbeddings()
    text_splitter = CharacterTextSplitter(
        chunk_size=ct.CHUNK_SIZE,
        chunk_overlap=ct.CHUNK_OVERLAP,
        separator="\n"
    )

    splitted_docs = text_splitter.split_documents(docs_all)
    splitted_docs.extend(integrated_docs_all)

    if not splitted_docs:
        splitted_docs = [Document(page_content="初期データなし", metadata={"source": "dummy"})]

    db = Chroma.from_documents(splitted_docs, embedding=embeddings)
    st.session_state.retriever = db.as_retriever(search_kwargs={"k": ct.TOP_K})

def initialize_session_state():
    """初期化データの用意"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.chat_history = []

def load_data_sources():
    """RAGの参照先となるデータソースの読み込み"""
    docs_all = []
    integrated_docs_all = []
    
    if os.path.exists(ct.RAG_TOP_FOLDER_PATH):
        recursive_file_check(ct.RAG_TOP_FOLDER_PATH, docs_all, integrated_docs_all)

    web_docs_all = []
    for web_url in ct.WEB_URL_LOAD_TARGETS:
        try:
            loader = WebBaseLoader(web_url)
            web_docs = loader.load()
            web_docs_all.extend(web_docs)
        except Exception as e:
            logging.getLogger(ct.LOGGER_NAME).warning(f"Web Load Error: {e}")
            
    docs_all.extend(web_docs_all)
    return docs_all, integrated_docs_all

def recursive_file_check(path, docs_all, integrated_docs_all):
    """ファイル再帰チェック"""
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            full_path = os.path.join(path, file)
            recursive_file_check(full_path, docs_all, integrated_docs_all)
    else:
        file_load(path, docs_all, integrated_docs_all)

def file_load(path, docs_all, integrated_docs_all):
    """ファイル内のデータ読み込み"""
    file_extension = os.path.splitext(path)[1].lower()
    file_name = os.path.basename(path)

    # PDFファイルに対応する同名の .txt ファイルが既に存在する場合は、元のPDFの二重読み込みを防ぐ
    base_name = os.path.splitext(path)[0]
    txt_counterpart = f"{base_name}.txt"
    if file_extension == ".pdf" and os.path.exists(txt_counterpart):
        return

    if file_extension in ct.SUPPORTED_EXTENSIONS:
        try:
            loader_func = ct.SUPPORTED_EXTENSIONS[file_extension]
            # ラムダ式/関数/クラス呼び出しの差分を統一
            if callable(loader_func):
                loader = loader_func(path)
            else:
                loader = loader_func(path)
                
            docs = loader.load()
            
            # 元のファイルパス情報を保持
            for doc in docs:
                if "source" not in doc.metadata:
                    doc.metadata["source"] = path

            if not file_name in ct.CSV_INTEGRATION_TARGETS:
                docs_all.extend(docs)
            else:
                doc_content = ""
                for row in docs:
                    page_content = row.page_content
                    value_list = page_content.split("\n")
                    row_data = "\n".join(value_list)
                    doc_content += row_data + "\n=================================\n"
                
                new_doc = Document(page_content=doc_content, metadata={"source": path})
                integrated_docs_all.append(new_doc)
        except Exception as e:
            logging.getLogger(ct.LOGGER_NAME).warning(f"File Load Error ({file_name}): {e}")

def adjust_string(s):
    """Windows環境等でのUnicode正規化（文字欠落を防ぐためcp932変換は除去）"""
    if not isinstance(s, str):
        return s
    # cp932エンコードによる文字損失（ignore）を防ぐため、NFKC正規化のみ実施
    s = unicodedata.normalize('NFKC', s)
    return s