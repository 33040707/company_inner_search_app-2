"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

import os
import streamlit as st

# 👇 LangChain関連のインポートを、最新バージョンの構造に合わせて個別に直接指定しました
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

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
    """LLMからの回答取得"""
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    question_generator_template = ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT
    question_generator_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_generator_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    if st.session_state.mode == ct.ANSWER_MODE_1:
        question_answer_template = ct.SYSTEM_PROMPT_DOC_SEARCH
    else:
        question_answer_template = ct.SYSTEM_PROMPT_INQUIRY

    question_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_answer_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
        llm, st.session_state.retriever, question_generator_prompt
    )

    question_answer_chain = create_stuff_documents_chain(llm, question_answer_prompt)
    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    llm_response = chain.invoke({"input": chat_message, "chat_history": st.session_state.chat_history})
    st.session_state.chat_history.extend([HumanMessage(content=chat_message), llm_response["answer"]])

    return llm_response