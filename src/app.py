from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel, Field
import json
import os
from typing import List, Optional, Dict, Any
import asyncio

# OllamaClientをインポート
from ollama.ollama_client import OllamaClient

# 環境変数から設定を読み込み
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))

app = FastAPI(
    title="SmartQ",
    description="Ollama AIを活用したクイズアプリケーション",
    version="0.1.0",
    docs_url="/api/docs",  # Swagger UIのURL
    redoc_url="/api/redoc",  # ReDocのURL
)

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# リクエスト/レスポンスモデル
class GenerateRequest(BaseModel):
    """問題生成リクエストのモデル"""
    topic: str = Field(..., description="問題のトピック（例: 'programming', 'science'）")
    system_prompt: str = Field(..., description="問題生成のためのシステムプロンプト")
    knowledge_base: Optional[str] = Field(None, description="追加の知識ベース情報（オプション）")

class Question(BaseModel):
    """問題のモデル"""
    id: str = Field(..., description="問題の識別子")
    question: str = Field(..., description="問題文")
    options: List[str] = Field(..., description="選択肢のリスト")
    correct_answer: int = Field(..., description="正解の選択肢のインデックス（0-3）")

class EvaluateRequest(BaseModel):
    """回答評価リクエストのモデル"""
    question_id: str = Field(..., description="問題の識別子")
    selected_answer: int = Field(..., description="選択された回答のインデックス（0-3）")
    additional_answer: Optional[str] = Field(None, description="追加の回答や説明（オプション）")
    question: str = Field(..., description="問題文")
    options: List[str] = Field(..., description="選択肢のリスト")
    correct_answer: int = Field(..., description="正解のインデックス")

class Feedback(BaseModel):
    """フィードバックのモデル"""
    is_correct: bool = Field(..., description="回答が正解かどうか")
    message: str = Field(..., description="フィードバックメッセージ")

# OllamaClientのインスタンスを取得する依存関係
def get_ollama_client():
    """OllamaClientのインスタンスを取得する"""
    return OllamaClient(
        model_name=OLLAMA_MODEL,
        api_url=f"{OLLAMA_HOST}/api/generate",
        temperature=0.7
    )

# ルート
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """メインページを表示"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/generate", response_model=Question)
async def generate_question(
    request: GenerateRequest,
    ollama_client: OllamaClient = Depends(get_ollama_client)
):
    """
    問題を生成する

    トピックとシステムプロンプトを受け取り、Ollama AIを使用して問題を生成します。
    """
    # システムプロンプトの構築
    prompt = f"""あなたは教育目的のクイズ作成AIです。
トピック「{request.topic}」に関する問題を1つ作成してください。

{request.system_prompt}

知識ベース:
{request.knowledge_base or '特になし'}

出力は以下のJSON形式で行ってください:
{{
    "question": "問題文をここに記述",
    "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
    "correct_answer": 0  // 0-3の整数で、正解の選択肢のインデックスを指定
}}

注意:
- 問題文は明確で理解しやすいものにしてください
- 選択肢は4つ必要です
- correct_answerは0から3の整数である必要があります
- 純粋なJSONのみを出力してください
"""

    try:
        # Ollamaから応答を取得
        response_json = await ollama_client.generate_json(
            prompt=prompt,
            timeout=API_TIMEOUT
        )

        # JSONデータの検証
        if not response_json:
            raise ValueError("Empty response from AI")

        # 必要なフィールドの存在チェック
        if not all(key in response_json for key in ["question", "options", "correct_answer"]):
            raise ValueError("Required fields missing in response")
        if len(response_json["options"]) != 4:
            raise ValueError("Exactly 4 options required")
        if not isinstance(response_json["correct_answer"], int) or not 0 <= response_json["correct_answer"] <= 3:
            raise ValueError("correct_answer must be an integer between 0 and 3")

        # QuestionモデルにIDを追加して返す
        return Question(
            id=str(hash(response_json["question"])),  # 簡易的なID生成
            question=response_json["question"],
            options=response_json["options"],
            correct_answer=response_json["correct_answer"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid response format from AI: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/evaluate", response_model=Feedback)
async def evaluate_answer(
    request: EvaluateRequest,
    ollama_client: OllamaClient = Depends(get_ollama_client)
):
    """
    回答を評価する

    ユーザーの回答を受け取り、Ollama AIを使用して評価と解説を生成します。
    """
    # 正解かどうかを判定
    is_correct = request.selected_answer == request.correct_answer

    # 評価用プロンプトの構築
    prompt = f"""あなたは教育目的のクイズ評価AIです。
ユーザーの回答を評価し、フィードバックを提供してください。

問題:
{request.question}

選択肢:
{', '.join([f"{i+1}. {opt}" for i, opt in enumerate(request.options)])}

正解:
{request.correct_answer + 1}. {request.options[request.correct_answer]}

ユーザーの選択:
{request.selected_answer + 1}. {request.options[request.selected_answer]}

ユーザーの回答は{'正解' if is_correct else '不正解'}です。

ユーザーの追加回答/質問:
{request.additional_answer or "なし"}

出力は以下のJSON形式で行ってください:
{{
    "is_correct": {str(is_correct).lower()},
    "message": "フィードバックメッセージ"  // 評価コメント、解説、アドバイスなど
}}

注意:
- フィードバックは建設的で学習意欲を高めるものにしてください
- 誤りがあった場合は、正しい理解に導くような説明を含めてください
- 追加の回答/質問があれば、それに対する応答も含めてください
- 純粋なJSONのみを出力してください
"""

    try:
        # Ollamaから応答を取得
        response_json = await ollama_client.generate_json(
            prompt=prompt,
            timeout=API_TIMEOUT
        )

        # JSONデータの検証
        if not response_json:
            raise ValueError("Empty response from AI")

        # 必要なフィールドの存在チェック
        if not all(key in response_json for key in ["is_correct", "message"]):
            raise ValueError("Required fields missing in response")

        return Feedback(**response_json)
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid response format from AI: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
