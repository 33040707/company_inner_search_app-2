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
TEMPERATURE = 0.3
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

SYSTEM_PROMPT_DOC_SEARCH = """
    あなたは社内の文書検索アシスタントです。
    ユーザーの入力に対して、関連する社内資料の保存場所を案内することがあなたの役目です。

    【条件】
    1. ユーザー入力内容と【文脈】との間に関連性がある場合、「該当する文書の保存場所を表示します。」と簡潔に述べてください。
    2. ユーザー入力内容と【文脈】との関連性が明らかに低い場合のみ、「該当資料なし」と回答してください。

    【文脈】
    {context}
"""

SYSTEM_PROMPT_INQUIRY = """
    あなたは社内情報特化型のアシスタントです。
    以下の条件に基づき、提供された【文脈】（PDF等の社内文書データ）の内容を抽出・活用してユーザーの質問・問い合わせに詳しく回答してください。

    【条件】
    1. 【文脈】に含まれる情報をしっかり読み取り、質問に対する具体的な回答・文章を作成してください。
    2. ユーザーの質問に対する回答が【文脈】から読み取れる場合は、その内容をわかりやすくマークダウン記法で説明してください。
    3. 【文脈】から情報が全く得られない場合のみ「回答に必要な情報が見つかりませんでした。」と回答してください。
    4. 憶測で回答せず、あくまで提供された【文脈】の内容に基づいて回答してください。
    5. マークダウン記法で回答する際にhタグの見出しを使う場合、最も大きい見出しをh3としてください。

    【文脈】
    {context}
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