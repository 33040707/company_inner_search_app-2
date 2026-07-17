"""
このファイルは、最初の画面読み込み時にのみ実行される初期化処理が記述されたファイルです。
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4
import sys
import unicodedata
import base64          # 👇追加: 画像変換用
import fitz            # 👇追加: PDF読み取り用(PyMuPDF)
import openai          # 👇追加: Vision OCR用
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
        for key in doc.metadata:
            doc.metadata[key] = adjust_string(doc.metadata[key])
    for doc in integrated_docs_all:
        doc.page_content = adjust_string(doc.page_content)
        for key in doc.metadata:
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
    file_extension = os.path.splitext(path)[1]
    file_name = os.path.basename(path)

    if file_extension in ct.SUPPORTED_EXTENSIONS:
        try:
            # ==========================================
            # PDFの場合は画像OCR（Vision）を利用する特別処理
            # ==========================================
            if file_extension == ".pdf":
                doc = fitz.open(path)
                text = ""
                for page_num, page in enumerate(doc):
                    extracted_text = page.get_text()
                    
                    # 50文字未満なら「画像化されたPDF」と判定し、GPT-4oでOCR読み取りを行う
                    if len(extracted_text.strip()) < 50:
                        logging.getLogger(ct.LOGGER_NAME).info(f"OCR実行中: {file_name} (ページ {page_num+1})")
                        
                        pix = page.get_pixmap(dpi=200)
                        img_bytes = pix.tobytes("jpeg")
                        base64_image = base64.b64encode(img_bytes).decode('utf-8')
                        
                        client = openai.Client() # Streamlit SecretsのAPIキーを自動利用
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "この画像は社内資料です。書かれている文字、数値、表の内容をすべて正確にテキストとして書き起こしてください。"},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}",
                                                "detail": "high"
                                            },
                                        },
                                    ],
                                }
                            ],
                            max_tokens=2000,
                        )
                        text += response.choices[0].message.content + "\n"
                    else:
                        text += extracted_text + "\n"
                
                # 読み取った全テキストをLangChainのDocumentとして保存
                new_doc = Document(page_content=text, metadata={"source": path})
                docs_all.append(new_doc)

            # ==========================================
            # PDF以外のファイル（Word, CSV, Text等）の処理
            # ==========================================
            else:
                loader = ct.SUPPORTED_EXTENSIONS[file_extension](path)
                docs = loader.load()
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
    """Windows環境でRAGが正常動作するよう調整"""
    if type(s) is not str:
        return s
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        s = s.encode("cp932", "ignore").decode("cp932")
        return s
    return s