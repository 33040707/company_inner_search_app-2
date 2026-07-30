"""
ロジック処理関数定義ファイル
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import constants as ct

def get_source_icon(source: str) -> str:
    """メッセージと一緒に表示するアイコンの種類を取得"""
    if str(source).startswith("http"):
        return ct.LINK_SOURCE_ICON
    return ct.DOC_SOURCE_ICON

def build_error_message(message: str) -> str:
    """エラーメッセージと管理者問い合わせテンプレートの連結"""
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])

def get_llm_response(chat_message: str) -> dict:
    """LLMからの回答および参照ドキュメントの取得処理"""
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    # 1. 検索用クエリの再構築（文脈考慮）
    if st.session_state.chat_history:
        rephrase_prompt = ChatPromptTemplate.from_messages([
            ("system", ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        search_query_msg = (rephrase_prompt | llm).invoke({
            "input": chat_message,
            "chat_history": st.session_state.chat_history
        })
        search_query = search_query_msg.content
    else:
        search_query = chat_message

    # 2. 関連ドキュメントの取得
    docs = st.session_state.retriever.invoke(search_query)
    context_text = "\n\n".join([doc.page_content for doc in docs]) if docs else ""

    # 3. モード別回答生成
    system_template = (
        ct.SYSTEM_PROMPT_DOC_SEARCH 
        if st.session_state.mode == ct.ANSWER_MODE_1 
        else ct.SYSTEM_PROMPT_INQUIRY
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    answer_msg = (qa_prompt | llm).invoke({
        "context": context_text,
        "input": chat_message,
        "chat_history": st.session_state.chat_history
    })

    # 会話履歴の更新
    st.session_state.chat_history.extend([
        HumanMessage(content=chat_message), 
        AIMessage(content=answer_msg.content)
    ])

    return {
        "answer": answer_msg.content,
        "context": docs
    }