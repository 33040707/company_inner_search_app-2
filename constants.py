"""
このファイルは、固定の文字列や数値などのデータを変数として一括管理するファイルです。
"""

import os
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader

# ==========================================
# 画面表示系
# ==========================================
APP_NAME = "社内情報特化型生成AI検索アプリ"
ANSWER_MODE_1 = "社内文書検索"
ANSWER_MODE_2 = "社内問い合わせ"
CHAT_INPUT_HELPER_TEXT = "こちらからメッセージを送信してください。"
DOC_SOURCE_ICON = ":material/description: "
LINK_SOURCE_ICON = ":material/link: "
WARNING_ICON = ":material/warning:"
ERROR_ICON = ":material/error:"
SPINNER_TEXT = "回答生成中..."

# ==========================================
# ログ出力系
# ==========================================
LOG_DIR_PATH = os.path.join(os.getcwd(), "logs")
LOGGER_NAME = "ApplicationLog"
LOG_FILE = "application.log"
APP_BOOT_MESSAGE = "アプリが起動されました。"

# ==========================================
# LLM設定系
# ==========================================
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.5
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5

# ==========================================
# RAG参照用のデータソース系
# ==========================================
RAG_TOP_FOLDER_PATH = os.path.join(os.getcwd(), "data")
SUPPORTED_EXTENSIONS = {
    ".pdf": PyMuPDFLoader,
    ".docx": Docx2txtLoader,
    ".csv": lambda path: CSVLoader(path, encoding="utf-8"),
    ".txt": lambda path: TextLoader(path, encoding="utf-8")
}
CSV_INTEGRATION_TARGETS = [
    "社員名簿.csv"
]
WEB_URL_LOAD_TARGETS = [
    "https://generative-ai.web-camp.io/"
]

# ==========================================
# プロンプトテンプレート
# ==========================================
SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT = "会話履歴と最新の入力をもとに、会話履歴なしでも理解できる独立した入力テキストを生成してください。"

# 元通りの社内文書検索用プロンプト
SYSTEM_PROMPT_DOC_SEARCH = """
    あなたは社内の文書検索アシスタントです。
    以下の条件に基づき、ユーザー入力に対して回答してください。

    【条件】
    1. ユーザー入力内容と以下の文脈との間に関連性がある場合、資料の内容を簡潔に要約して回答してください。
    2. ユーザー入力内容と以下の文脈との関連性が明らかに低い場合、「該当資料なし」と回答してください。

    【文脈】
    {context}
"""

# 社内問い合わせ用プロンプト：提供されたドキュメント本文からしっかりと回答させる調整
SYSTEM_PROMPT_INQUIRY = """
    あなたは社内情報特化型のアシスタントです。
    提供された【参照ドキュメントの内容】（PDFや社内資料のテキスト）を分析し、ユーザーの質問に対して具体的かつ分かりやすく回答してください。

    【条件】
    1. 提供されたドキュメントの内容に記載されている情報をベースに、質問に対する回答文章を作成してください。
    2. 提供されたドキュメントの内容に全く関連情報が含まれていない場合のみ、「回答に必要な情報が見つかりませんでした。」と回答してください。
    3. 憶測で回答せず、できる限り提供されたドキュメントの内容に基づいて回答してください。
    4. マークダウン記法（箇条書きや強調表示）を活用して、読みやすく回答してください。
"""

# ==========================================
# LLMレスポンスの一致判定用
# ==========================================
INQUIRY_NO_MATCH_ANSWER = "回答に必要な情報が見つかりませんでした。"
NO_DOC_MATCH_ANSWER = "該当資料なし"

# ==========================================
# エラー・警告メッセージ
# ==========================================
COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
NO_DOC_MATCH_MESSAGE = """
    入力内容と関連する社内文書が見つかりませんでした。\n
    入力内容を変更してください。
"""
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"
GET_LLM_RESPONSE_ERROR_MESSAGE = "回答生成に失敗しました。"
DISP_ANSWER_ERROR_MESSAGE = "回答表示に失敗しました。"