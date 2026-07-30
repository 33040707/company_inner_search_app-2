"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")


def display_sidebar():
    """
    サイドバーの表示
    """
    with st.sidebar:
        st.markdown("## 利用目的")

        col1, col2 = st.columns([100, 1])
        with col1:
            st.session_state.mode = st.radio(
                label="利用目的の選択",
                options=[ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
                label_visibility="collapsed"
            )
        st.divider()

        st.markdown("**【「社内文書検索」を選択した場合】**")
        st.info("入力内容と関連性が高い社内文書のありかを検索できます。")
        st.code("【入力例】\n社員の育成方針に関するMTGの議事録", wrap_lines=True, language=None)

        st.markdown("**【「社内問い合わせ」を選択した場合】**")
        st.info("質問・要望に対して、社内文書の情報をもとに回答を得られます。")
        st.code("【入力例】\n人事部に所属している従業員情報を一覧化して", wrap_lines=True, language=None)


def display_initial_ai_message():
    """
    AIメッセージの初期表示
    """
    with st.chat_message("assistant"):
        st.success("こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。サイドバーで利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。")
        st.warning("具体的に入力したほうが期待通りの回答を得やすいです。", icon=ct.WARNING_ICON)


def display_conversation_log():
    """
    会話ログの一覧表示
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                if message["content"]["mode"] == ct.ANSWER_MODE_1:
                    if not "no_file_path_flg" in message["content"]:
                        if "answer" in message["content"] and message["content"]["answer"]:
                            st.markdown(message["content"]["answer"])

                        st.markdown(message["content"]["main_message"])

                        icon = utils.get_source_icon(message['content']['main_file_path'])
                        st.success(f"📌 **保存場所:** `{message['content']['main_file_path']}`", icon=icon)
                        
                        if "main_content" in message["content"]:
                            with st.expander("📄 抽出されたデータ内容を確認"):
                                st.markdown(message["content"]["main_content"])

                        if "sub_message" in message["content"]:
                            st.markdown(message["content"]["sub_message"])

                            for sub_choice in message["content"]["sub_choices"]:
                                icon = utils.get_source_icon(sub_choice['source'])
                                st.info(f"📌 **保存場所:** `{sub_choice['source']}`", icon=icon)
                                if "content" in sub_choice:
                                    with st.expander(f"📄 {sub_choice['source']} の内容を確認"):
                                        st.markdown(sub_choice["content"])
                    else:
                        st.markdown(message["content"]["answer"])
                else:
                    st.markdown(message["content"]["answer"])

                    if "file_info_list" in message["content"]:
                        st.divider()
                        st.markdown(f"##### {message['content']['message']}")
                        for file_item in message["content"]["file_info_list"]:
                            icon = utils.get_source_icon(file_item["path"])
                            st.info(f"📌 **保存場所:** `{file_item['path']}`", icon=icon)
                            if file_item.get("content"):
                                with st.expander("📄 参照したデータ内容を表示"):
                                    st.markdown(file_item["content"])


def display_search_llm_response(llm_response):
    """
    「社内文書検索」モードにおけるLLMレスポンスを表示
    """
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:
        if llm_response["answer"]:
            st.markdown(llm_response["answer"])

        main_doc = llm_response["context"][0]
        main_file_path = main_doc.metadata["source"]
        main_file_content = main_doc.page_content

        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)
        
        icon = utils.get_source_icon(main_file_path)
        st.success(f"📌 **保存場所:** `{main_file_path}`", icon=icon)
        with st.expander("📄 抽出されたデータ内容を確認"):
            st.markdown(main_file_content)

        sub_choices = []
        duplicate_check_list = [main_file_path]

        for document in llm_response["context"][1:]:
            sub_file_path = document.metadata["source"]

            if sub_file_path in duplicate_check_list:
                continue

            duplicate_check_list.append(sub_file_path)
            sub_choices.append({
                "source": sub_file_path,
                "content": document.page_content
            })
        
        if sub_choices:
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)

            for sub_choice in sub_choices:
                icon = utils.get_source_icon(sub_choice['source'])
                st.info(f"📌 **保存場所:** `{sub_choice['source']}`", icon=icon)
                with st.expander(f"📄 {sub_choice['source']} の内容を確認"):
                    st.markdown(sub_choice["content"])
        
        content = {
            "mode": ct.ANSWER_MODE_1,
            "answer": llm_response["answer"],
            "main_message": main_message,
            "main_file_path": main_file_path,
            "main_content": main_file_content
        }
        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices
    else:
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)

        content = {
            "mode": ct.ANSWER_MODE_1,
            "answer": ct.NO_DOC_MATCH_MESSAGE,
            "no_file_path_flg": True
        }
    
    return content


def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを表示
    """
    st.markdown(llm_response["answer"])

    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        st.divider()

        message = "情報源（参照データ）"
        st.markdown(f"##### {message}")

        file_path_list = []
        file_info_list = []

        for document in llm_response["context"]:
            file_path = document.metadata["source"]
            if file_path in file_path_list:
                continue

            file_path_list.append(file_path)
            icon = utils.get_source_icon(file_path)
            
            st.info(f"📌 **保存場所:** `{file_path}`", icon=icon)
            with st.expander("📄 参照したデータ内容を表示"):
                st.markdown(document.page_content)

            file_info_list.append({
                "path": file_path,
                "content": document.page_content
            })

    content = {
        "mode": ct.ANSWER_MODE_2,
        "answer": llm_response["answer"]
    }
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content