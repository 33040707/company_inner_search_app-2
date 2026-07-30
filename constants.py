"""
定数およびプロンプト定義ファイル
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
DOC_SOURCE_ICON = ":material/description:"
LINK_SOURCE_ICON = ":material/link:"
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
# LLM・RAG設定系
# ==========================================
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.2
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 10  # 検索候補数を増やして拾い漏れを防止

# ==========================================
# データソース系
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
# プロンプトテンプレート（ヒット率向上調整版）
# ==========================================
SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT = (
    "これまでの会話履歴と最新のユーザー入力を参照し、"
    "会話履歴がなくても単体で文脈が理解できる検索クエリ（独立した文）を作成してください。"
    "余計な挨拶や解説は含めず、クエリのみを出力してください。"
)

SYSTEM_PROMPT_DOC_SEARCH = """あなたは社内の文書検索アシスタントです。
以下の【文脈】を参照し、ユーザーの質問に対して回答してください。

【条件】
1. 【文脈】の中に少しでもユーザーの質問やキーワードに関連する記述がある場合、関連する箇所の要約や該当部分を丁寧に回答してください。
2. 【文脈】の中にまったく関連する情報が含まれていない場合のみ、「該当資料なし」と回答してください。

【文脈】
{context}"""

SYSTEM_PROMPT_INQUIRY = """あなたは社内情報特化型のアシスタントです。
以下の【文脈】を参照し、ユーザーの質問・要望に回答してください。

【条件】
1. 【文脈】の中に含まれている情報や数値を最大限に活用し、わかりやすく丁寧に回答してください。
2. 断片的な情報しか見つからない場合でも、見つかった情報の範囲内で可能な限り回答してください。
3. 【文脈】の中にまったく回答のヒントがない場合のみ、「回答に必要な情報が見つかりませんでした。」と回答してください。
4. マークダウン形式（見出しはh3以下）で見やすく整えて出力してください。

【文脈】
{context}"""

# ==========================================
# 判定用定数・メッセージ
# ==========================================
INQUIRY_NO_MATCH_ANSWER = "回答に必要な情報が見つかりませんでした。"
NO_DOC_MATCH_ANSWER = "該当資料なし"

COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
NO_DOC_MATCH_MESSAGE = "入力内容と関連する社内文書が見つかりませんでした。\n条件やキーワードを変更して再度お試しください。"
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"
GET_LLM_RESPONSE_ERROR_MESSAGE = "回答生成に失敗しました。"
DISP_ANSWER_ERROR_MESSAGE = "回答表示に失敗しました。"