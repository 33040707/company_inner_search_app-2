import os
import glob
import base64
import io
import pypdfium2 as pdfium
from openai import OpenAI
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # 端末実行時のフォールバック処理
    api_key = input("OpenAIのAPIキー（sk-...）を入力してください: ").strip()

client = OpenAI(api_key=api_key)

DATA_FOLDER = "data"

def process_pdf_with_vision(pdf_path):
    """
    提示コードと同様に PDF を pypdfium2 で高精度画像化し、
    GPT-4o Vision で文字化け・表崩れゼロの Markdown テキストに書き起こす関数
    """
    doc = pdfium.PdfDocument(pdf_path)
    full_markdown_text = f"# 書類名: {os.path.basename(pdf_path)}\n\n"
    
    for page_num, page in enumerate(doc):
        print(f"   ... ページ {page_num + 1}/{len(doc)} を高解像度画像化＆Vision解析中 ...")
        
        # 提示コードと同様に scale=2 で高画質化
        bitmap = page.render(scale=2)
        pil_img = bitmap.to_pil()
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG")
        img_bytes = buffer.getvalue()
        base64_str = base64.b64encode(img_bytes).decode("utf-8")

        prompt = """
        あなたは社内資料の転記を行うプロフェッショナルです。
        提供された画像は価格表、単価表、仕様書、または通知書などの社内PDF資料です。
        画像に含まれる全てのテキスト、数値、および表構造を、1文字の漏れもなく正確に書き起こしてください。
        
        【条件】
        1. 表データは必ずマークダウン形式（| 列名1 | 列名2 |）で再現してください。
        2. 見出しやタイトル、注記なども記載されている通りに出力してください。
        3. 挨拶や解説などの余計な文章は一切含めず、書き起こしたテキストのみを出力してください。
        """

        response = client.chat.completions.create(
            model="gpt-4o",  # 高精度な視覚・構造認識のため GPT-4o を使用
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}
                        }
                    ]
                }
            ],
            temperature=0.0  # 揺らぎをゼロにして正確に転記
        )

        full_markdown_text += f"## ページ {page_num + 1}\n\n"
        full_markdown_text += response.choices[0].message.content + "\n\n"

    return full_markdown_text


def convert_all_pdf_to_markdown_text():
    pdf_files = glob.glob(os.path.join(DATA_FOLDER, "*.pdf"))
    
    if not pdf_files:
        print(f"⚠️ '{DATA_FOLDER}' フォルダ内に PDF ファイルが見つかりません。")
        return

    print(f"📄 {len(pdf_files)} 件の PDF が見つかりました。Vision AI によるテキスト化を開始します...\n")

    for file_path in pdf_files:
        file_name = os.path.basename(file_path)
        base_name = os.path.splitext(file_name)[0]
        output_txt_path = os.path.join(DATA_FOLDER, f"{base_name}.txt")

        print(f"🔄 変換処理中: {file_name}")
        try:
            markdown_text = process_pdf_with_vision(file_path)

            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)

            print(f"✅ 完了！ {output_txt_path} に完璧なテキストデータを保存しました。\n")

        except Exception as e:
            print(f"❌ エラーが発生しました ({file_name}): {e}\n")

    print("🎉 すべての PDF の視覚テキスト化が完了しました！")


if __name__ == "__main__":
    convert_all_pdf_to_markdown_text()