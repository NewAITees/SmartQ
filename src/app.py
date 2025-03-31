from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel
import httpx
import json
import os
from typing import List, Optional

# 環境変数から設定を読み込み
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

app = FastAPI(title="SmartQ", description="Ollama AIを活用したクイズアプリケーション")

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# リクエスト/レスポンスモデル
class GenerateRequest(BaseModel):
    topic: str
    system_prompt: str
    knowledge_base: Optional[str] = None

class EvaluateRequest(BaseModel):
    question_id: str
    selected_answer: int
    additional_answer: Optional[str] = None

class Question(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: int

class Feedback(BaseModel):
    is_correct: bool
    message: str

# Ollamaとの通信用クライアント
async def call_ollama_api(prompt: str) -> str:
    """Ollama APIを呼び出し、応答を取得する"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Ollama API error: {str(e)}")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"Invalid JSON response from Ollama: {str(e)}")

# ルート
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """メインページを表示"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/generate", response_model=Question)
async def generate_question(request: GenerateRequest):
    """問題を生成する"""
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
        response = await call_ollama_api(prompt)
        
        # JSON応答をパース
        try:
            data = json.loads(response)
            # 必要なフィールドの存在チェック
            if not all(key in data for key in ["question", "options", "correct_answer"]):
                raise ValueError("Required fields missing in response")
            if len(data["options"]) != 4:
                raise ValueError("Exactly 4 options required")
            if not isinstance(data["correct_answer"], int) or not 0 <= data["correct_answer"] <= 3:
                raise ValueError("correct_answer must be an integer between 0 and 3")
            
            # QuestionモデルにIDを追加して返す
            return Question(
                id=str(hash(data["question"])),  # 簡易的なID生成
                question=data["question"],
                options=data["options"],
                correct_answer=data["correct_answer"]
            )
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=502,
                detail=f"Invalid response format from AI: {str(e)}\nResponse: {response[:200]}..."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/evaluate", response_model=Feedback)
async def evaluate_answer(request: EvaluateRequest):
    """回答を評価する"""
    # 評価用プロンプトの構築
    prompt = f"""あなたは教育目的のクイズ評価AIです。
ユーザーの回答を評価し、フィードバックを提供してください。

出力は以下のJSON形式で行ってください:
{{
    "is_correct": true/false,  // ユーザーの回答が正解かどうか
    "message": "フィードバックメッセージ"  // 評価コメント、解説、アドバイスなど
}}

注意:
- フィードバックは建設的で学習意欲を高めるものにしてください
- 誤りがあった場合は、正しい理解に導くような説明を含めてください
- 追加の回答/質問があれば、それに対する応答も含めてください
- 純粋なJSONのみを出力してください

ユーザーの追加回答/質問:
{request.additional_answer or "なし"}
"""

    try:
        # Ollamaから応答を取得
        response = await call_ollama_api(prompt)
        
        # JSON応答をパース
        try:
            data = json.loads(response)
            if not all(key in data for key in ["is_correct", "message"]):
                raise ValueError("Required fields missing in response")
            return Feedback(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=502,
                detail=f"Invalid response format from AI: {str(e)}\nResponse: {response[:200]}..."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
