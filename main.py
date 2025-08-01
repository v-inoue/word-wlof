from google import genai
import dotenv
import os
import json
import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from collections import deque
from pprint import pprint
import random
from google.genai import types
from pydantic import BaseModel

# .env から APIキーを読み込み
dotenv.load_dotenv()

client = genai.Client()

class RequestData(BaseModel):
    minLevel: int
    maxLevel: int


app = fastapi.FastAPI()

# 履歴（最大10個）
generated_word_history = deque(maxlen=10)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# プロンプト作成関数
def create_prompt(difficulty_levels):
    # 難易度の選択肢
   
    print(f"選択された難易度: {difficulty_levels}")
    if generated_word_history:
        exclusion_words = ", ".join(generated_word_history)
        exclusion_prompt = f"次の単語は使わないでください：{exclusion_words}。"
    else:
        exclusion_prompt = ""

    prompt = (
        "# 指示\n"
        "情報工学分野から「web」や「ソフトウェア工学」、「AI」、「プログラミング言語」などの分野をランダムに選択し、用語を4つ生成してください。"
        "さらに、選択した分野のサブ分野もランダムに選んでください。"
        "また、英単語の場合は（）で日本語もつけてください。"
        "単語の難易度を五段階のうち、"
        f"{difficulty_levels}"
        "の単語を生成してください。"
        "# 出力用語の例\n"
        "['useState', 'useEffect', 'button', 'localstorage'],"
        "['ウォータフォール', 'アジャイル', 'スパイラル', 'XP'],"
        "['ロジスティック回帰', 'ランダムフォレスト', '交差検証', 'グリッドサーチ']"
        f"{exclusion_prompt}"
        "\n以下形式のみで出力してください：\n"
        "{\n"
        "  \"domain\": \"分野\",\n"
        "  \"sub_domain\": \"分野\",\n"
        "  \"difficulty_level\": \"難易度\",\n"
        "  \"words\": [\"単語1\", \"単語2\", \"単語3\", \"単語4\"],\n"
        "  \"explanations\": [\"説明1\", \"説明2\", \"説明3\", \"説明4\"]\n"
        "}"
    )
    return prompt


# 単語ペア生成関数
def generate_word_pair(min_level, max_level):
    send_data = {
        "citizen": [],
        "werewlof": [],
        "citizen-explanation": [],
        "werewlof-explanation": [],
        "domain": "",
        "level": int
    }
    difficulty_levels = random.randint(min_level, max_level)
    prompt = create_prompt(difficulty_levels)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "thinking_config": types.ThinkingConfig(
                thinking_budget=500
            ),
            "temperature": 2.0,
        }
    )
    output_text = response.text

    try:
        data = json.loads(output_text)
    except json.JSONDecodeError as e:
        print("JSONデコードエラー:", e)
        return {"error": "Invalid JSON format in response"}

    pprint(data)
    

    index1 = random.randint(0, 3)
    index2 = (index1 + random.randint(1, 3)) % 4


    generated_word_history.append(data["words"][index1])
    generated_word_history.append(data["words"][index2])

    send_data["citizen"] = data["words"][index1]
    send_data["werewlof"] = data["words"][index2]
    send_data["citizen-explanation"] = data["explanations"][index1]
    send_data["werewlof-explanation"] = data["explanations"][index2]
    send_data["domain"] = data["domain"]
    send_data["level"] = difficulty_levels


    return send_data

# API エンドポイント

@app.post("/generate-word-pair")

async def get_word_pair(request: RequestData):

    # リクエストデータから難易度を取得
    min_level = request.minLevel
    max_level = request.maxLevel
    result = generate_word_pair(min_level, max_level)
    if "error" not in result:
        return result
    else:
        return {"error": "Failed to generate word pair after multiple attempts"}

# FastAPI の起動
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8012)