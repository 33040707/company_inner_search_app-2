"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""

import os
import logging
import streamlit as st
from dotenv import load_dotenv

# .env があれば読み込む（ローカル実行時の環境変数設定用）
load_dotenv()

# Streamlit SecretsからAPIキーを環境変数に反映（優先）
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

import constants as ct
import utils
import components as cn
from initialize import initialize

st.set_page_config(
    page_title=ct.APP_NAME
)

logger = logging.getLogger(ct.LOGGER_NAME)

try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)

cn.display_app_title()
cn.display_sidebar()
cn.display_initial_ai_message()

try:
    cn.display_conversation_log()
except Exception as e:
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

chat_message = st.chat_input(ct.CHAT_INPUT_HELPER_TEXT)

if chat_message:
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    with st.chat_message("user"):
        st.markdown(chat_message)

    res_box = st.empty()
    with st.spinner(ct.SPINNER_TEXT):
        try:
            llm_response = utils.get_llm_response(chat_message)
        except Exception as e:
            logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()
    
    with st.chat_message("assistant"):
        try:
            if st.session_state.mode == ct.ANSWER_MODE_1:
                content = cn.display_search_llm_response(llm_response)
            elif st.session_state.mode == ct.ANSWER_MODE_2:
                content = cn.display_contact_llm_response(llm_response)
            
            logger.info({"message": content, "application_mode": st.session_state.mode})
        except Exception as e:
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()

    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": content})