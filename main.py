"""
メインアプリケーションスクリプト
"""

import logging
import streamlit as st
import utils
from initialize import initialize
import components as cn
import constants as ct

# ページ基本設定
st.set_page_config(page_title=ct.APP_NAME)
logger = logging.getLogger(ct.LOGGER_NAME)

# アプリ起動時の初期化処理
try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

# 初期化ログ出力
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)

# UI要素の描画
cn.display_app_title()
cn.display_sidebar()
cn.display_initial_ai_message()

# 過去の会話ログ表示
try:
    cn.display_conversation_log()
except Exception as e:
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

# ユーザー入力フォーム
chat_message = st.chat_input(ct.CHAT_INPUT_HELPER_TEXT)

# メッセージ送信時の処理
if chat_message:
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    # ユーザーメッセージの表示
    with st.chat_message("user"):
        st.markdown(chat_message)

    # LLMからのレスポンス取得
    with st.spinner(ct.SPINNER_TEXT):
        try:
            llm_response = utils.get_llm_response(chat_message)
        except Exception as e:
            logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()
    
    # モードに応じたアシスタント回答の描画処理
    with st.chat_message("assistant"):
        try:
            if st.session_state.mode == ct.ANSWER_MODE_1:
                content = cn.display_search_llm_response(llm_response)
            else:
                content = cn.display_contact_llm_response(llm_response)
            
            logger.info({"message": content, "application_mode": st.session_state.mode})
        except Exception as e:
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()

    # 会話履歴をセッションに格納
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": content})