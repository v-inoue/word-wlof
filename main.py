import google.generativeai as genai
import dotenv
import os
import json
import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from collections import deque
from pprint import pprint
import random

# .env から APIキーを読み込み
dotenv.load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))

# モデルを指定
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    
    generation_config={"response_mime_type": "application/json"}
)

app = fastapi.FastAPI()

# 履歴（最大30個）
generated_word_history = deque(maxlen=30)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# プロンプト作成関数
def create_prompt():
    if generated_word_history:
        exclusion_words = ", ".join(generated_word_history)
        exclusion_prompt = f"次の単語は使わないでください：{exclusion_words}。"
    else:
        exclusion_prompt = ""

    prompt = (
        "「useState」と「useEffect」や「ウォータフォール」と「アジャイル」、「ランダムフォレスト」と「ロジスティック回帰」のように、まず似た単語を四つ生成してください。"
        "単語は情報工学分野の大学生レベルにしてください。"
        "また、英単語の場合は（）で日本語もつけてください。"
        f"{exclusion_prompt}"
        "\n以下形式のみで出力してください：\n"
        "{\n"
        "  \"domain\": \"分野\",\n"
        "  \"words\": [\"単語1\", \"単語2\", \"単語3\", \"単語4\"],\n"
        "  \"explanations\": [\"説明1\", \"説明2\", \"説明3\", \"説明4\"]\n"

        "}"
    )
    return prompt

def create_prompt_architecture():
    if generated_word_history:
        exclusion_words = ", ".join(generated_word_history)
        exclusion_prompt = f"次の単語は使わないでください：{exclusion_words}。"
    else:
        exclusion_prompt = ""

    prompt = (
        "あなたは日本建築史ワードウルフのゲームマスターです。"
        "「大仏様」と「折衷様」や「蟇股」と「組物」のように、似た意味を持つ市民側の単語と人狼側の単語を考えてください。ただし、２つの単語は、片方からもう片方が推測されない程度の関連性のものにしてください。"
        "単語は大学で日本建築について学んでいる人がわかるレベルにしてください。"
        f"{exclusion_prompt}"
        "\n以下形式のみで出力してください：\n"
        "{\n"
        "  \"citizen\": \"単語n\",\n"
        "  \"werewlof\": \"単語m\",\n"
        "  \"citizen-explanation\": \"説明n\",\n"
        "  \"werewlof-explanation\": \"説明m\"\n"
        "}"
    )
    return prompt

# 単語ペア生成関数
def generate_word_pair():
    send_data = {
        "citizen": [],
        "werewlof": [],
        "citizen-explanation": [],
        "werewlof-explanation": []
    }
    prompt = create_prompt()
    response = model.generate_content(prompt)
    output_text = response.text

    try:
        data = json.loads(output_text)
    except json.JSONDecodeError as e:
        print("JSONデコードエラー:", e)
        return {"error": "Invalid JSON format in response"}

    

    index1 = random.randint(0, 3)
    index2 = (index1 + random.randint(1, 3)) % 4


    generated_word_history.append(data["words"][index1])
    generated_word_history.append(data["words"][index2])

    send_data["citizen"] = data["words"][index1]
    send_data["werewlof"] = data["words"][index2]
    send_data["citizen-explanation"] = data["explanations"][index1]
    send_data["werewlof-explanation"] = data["explanations"][index2]

    pprint(send_data)

    return send_data

# API エンドポイント
@app.get("/generate-word-pair")
async def get_word_pair():
    result = generate_word_pair()
    if "error" not in result:
        return result
    else:
        return {"error": "Failed to generate word pair after multiple attempts"}

# FastAPI の起動
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8012)