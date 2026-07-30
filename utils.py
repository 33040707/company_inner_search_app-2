"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

import os
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import constants as ct

def get_source_icon(source):
    """メッセージと一緒に表示するアイコンの種類を取得"""
    if source.startswith("http"):
        icon = ct.LINK_SOURCE_ICON
    else:
        icon = ct.DOC_SOURCE_ICON
    
    return icon


def build_error_message(message):
    """エラーメッセージと管理者問い合わせテンプレートの連結"""
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def get_llm_response(chat_message):
    """LLMからの回答取得（バージョン依存をなくした直接記述版）"""
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    # ==========================================
    # 1. 検索クエリの生成（会話履歴を踏まえる）
    # ==========================================
    if st.session_state.chat_history:
        question_generator_prompt = ChatPromptTemplate.from_messages([
            ("system", ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        # 履歴がある場合はLLMに文脈を理解させた独立クエリを作らせる
        search_query_msg = (question_generator_prompt | llm).invoke({
            "input": chat_message,
            "chat_history": st.session_state.chat_history
        })
        search_query = search_query_msg.content
    else:
        # 履歴がなければ入力値をそのまま検索クエリとする
        search_query = chat_message

    # ==========================================
    # 2. ドキュメントの検索
    # ==========================================
    docs = st.session_state.retriever.invoke(search_query)
    
    # 検索したドキュメント群のテキストを結合
    context_text = "\n\n".join([doc.page_content for doc in docs])

    # ==========================================
    # 3. モードに応じた回答の生成
    # ==========================================
    if st.session_state.mode == ct.ANSWER_MODE_1:
        question_answer_template = ct.SYSTEM_PROMPT_DOC_SEARCH
    else:
        question_answer_template = ct.SYSTEM_PROMPT_INQUIRY

    question_answer_prompt = ChatPromptTemplate.from_messages([
        ("system", question_answer_template),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    # LLMから最終的な回答を取得
    answer_msg = (question_answer_prompt | llm).invoke({
        "context": context_text,
        "input": chat_message,
        "chat_history": st.session_state.chat_history
    })

    # 画面表示用のレスポンス辞書を作成
    llm_response = {
        "answer": answer_msg.content,
        "context": docs
    }

    # LLMレスポンスを会話履歴に追加（次回以降の文脈考慮のため）
    st.session_state.chat_history.extend([
        HumanMessage(content=chat_message), 
        AIMessage(content=answer_msg.content)
    ])

    return llm_response