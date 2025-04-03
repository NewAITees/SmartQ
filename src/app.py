"""SmartQ FastAPIアプリケーション"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from typing import List, Optional, Union, Annotated
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import json
import os
import uuid
import asyncio

# OllamaClientとJSONスキーマをインポート
from ollama.ollama_client import OllamaClient
from ollama.json_schemas import QUIZ_SCHEMA, EVALUATION_SCHEMA

# 環境変数から設定を読み込み
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:27b")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "60"))

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="SmartQ API",
    description="Ollama AIを活用したインテリジェントなクイズアプリケーションのAPI",
    version="0.2.0",
    docs_url="/api/docs",  # Swagger UIのURL
    redoc_url="/api/redoc",  # ReDocのURL
    openapi_tags=[
        {
            "name": "クイズ",
            "description": "クイズの生成と回答評価に関連するエンドポイント"
        }
    ]
)

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")

# 共通の制約条件付き型を定義
NonEmptyStr = Annotated[str, Field(min_length=1)]

# データモデルの定義
class OptionType(str, Enum):
    """選択肢のタイプを表す列挙型"""
    RADIO = "radio"
    CHECKBOX = "checkbox"

class Option(BaseModel):
    """選択肢のモデル"""
    text: NonEmptyStr = Field(..., description="選択肢のテキスト")
    isCorrect: bool = Field(..., description="この選択肢が正解かどうか")
    type: OptionType = Field(default=OptionType.RADIO, description="選択肢のタイプ（radio/checkbox）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Pythonは動的型付け言語である",
                "isCorrect": True,
                "type": "radio"
            }
        }
    }

class QuizQuestion(BaseModel):
    """問題のモデル"""
    id: str = Field(..., description="問題の一意の識別子")
    question: NonEmptyStr = Field(..., description="問題文")
    options: List[Option] = Field(..., description="選択肢のリスト", min_length=2)
    explanation: str = Field(..., description="問題の解説文（回答後に表示）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "q123e4567-e89b-12d3-a456-426614174000",
                "question": "Pythonの特徴として正しいものはどれですか？",
                "options": [
                    {"text": "コンパイル言語である", "isCorrect": False, "type": "radio"},
                    {"text": "動的型付け言語である", "isCorrect": True, "type": "radio"},
                    {"text": "メモリ管理を手動で行う必要がある", "isCorrect": False, "type": "radio"},
                    {"text": "C言語の派生言語である", "isCorrect": False, "type": "radio"}
                ],
                "explanation": "Pythonは動的型付け言語で、実行時に型チェックが行われます。また、ガベージコレクションによって自動的にメモリ管理が行われます。"
            }
        }
    }
    
    @model_validator(mode='after')
    def validate_options(self):
        """少なくとも1つの正解選択肢があることを確認"""
        if not any(opt.isCorrect for opt in self.options):
            raise ValueError("少なくとも1つの選択肢は正解としてマークされている必要があります")
        
        # ラジオボタンの場合は正解が1つだけであることを確認
        if all(opt.type == OptionType.RADIO for opt in self.options):
            correct_count = sum(1 for opt in self.options if opt.isCorrect)
            if correct_count != 1:
                raise ValueError("ラジオボタン選択式の場合、正解は1つだけである必要があります")
        
        return self

class GenerateQuizRequest(BaseModel):
    """問題生成リクエストのモデル"""
    topic: NonEmptyStr = Field(..., description="問題のトピック（例: 'programming', 'science'）")
    system_prompt: str = Field(..., description="問題生成のためのシステムプロンプト")
    knowledge_base: Optional[str] = Field(None, description="追加の知識ベース情報（オプション）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "topic": "programming",
                "system_prompt": "初心者向けのPythonプログラミングに関する問題を作成してください。",
                "knowledge_base": "Pythonはインタープリタ型の高水準プログラミング言語です。"
            }
        }
    }

class SelectedOption(BaseModel):
    """選択された選択肢のモデル"""
    index: int = Field(..., description="選択肢のインデックス", ge=0)
    text: NonEmptyStr = Field(..., description="選択肢のテキスト")

class EvaluateAnswerRequest(BaseModel):
    """回答評価リクエストのモデル"""
    question_id: str = Field(..., description="問題の識別子")
    selected_options: List[SelectedOption] = Field(..., description="選択された選択肢のリスト")
    additional_answer: Optional[str] = Field(None, description="追加の回答や説明（オプション）")
    question: NonEmptyStr = Field(..., description="問題文")
    options: List[Option] = Field(..., description="問題の全選択肢")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "q123e4567-e89b-12d3-a456-426614174000",
                "selected_options": [
                    {"index": 1, "text": "動的型付け言語である"}
                ],
                "additional_answer": "動的型付けとは、変数の型が実行時に決定されることです。",
                "question": "Pythonの特徴として正しいものはどれですか？",
                "options": [
                    {"text": "コンパイル言語である", "isCorrect": False, "type": "radio"},
                    {"text": "動的型付け言語である", "isCorrect": True, "type": "radio"},
                    {"text": "メモリ管理を手動で行う必要がある", "isCorrect": False, "type": "radio"},
                    {"text": "C言語の派生言語である", "isCorrect": False, "type": "radio"}
                ]
            }
        }
    }
    
    @field_validator('selected_options')
    @classmethod
    def validate_selected_options(cls, v):
        """少なくとも1つの選択肢が選択されていることを確認"""
        if not v:
            raise ValueError("少なくとも1つの選択肢を選択してください")
        return v

class AdditionalResource(BaseModel):
    """追加リソースのモデル"""
    title: NonEmptyStr = Field(..., description="リソースのタイトル")
    description: str = Field(..., description="リソースの説明")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Python公式ドキュメント",
                "description": "Pythonの詳細な仕様や使い方を学ぶことができます。"
            }
        }
    }

class FeedbackResponse(BaseModel):
    """フィードバックのモデル"""
    isCorrect: bool = Field(..., description="回答が正解かどうか")
    feedback: str = Field(..., description="フィードバックメッセージ")
    detailedExplanation: str = Field(..., description="詳細な解説")
    additionalResources: Optional[List[AdditionalResource]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "isCorrect": True,
                "feedback": "正解です！Pythonは動的型付け言語です。",
                "detailedExplanation": "Pythonでは変数の型が実行時に決定され、同じ変数に異なる型の値を代入することができます。これにより柔軟なコーディングが可能になりますが、型関連のエラーが実行時まで検出されない場合もあります。",
                "additionalResources": [
                    {
                        "title": "Python公式ドキュメント",
                        "description": "Pythonの詳細な仕様や使い方を学ぶことができます。"
                    }
                ]
            }
        }
    }

# OllamaClientのインスタンスを取得する依存関係
def get_ollama_client():
    """OllamaClientのインスタンスを取得する"""
    return OllamaClient(
        model_name=OLLAMA_MODEL,
        api_url=OLLAMA_HOST,
        temperature=1.0
    )

# ルート
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """メインページを表示"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/generate", response_model=QuizQuestion, tags=["クイズ"])
async def generate_quiz(
    request: GenerateQuizRequest,
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

問題はシングルチョイス（ラジオボタン選択式）で作成してください。
選択肢の1つだけを正解としてマークしてください。
すべての選択肢のタイプは "radio" としてください。

出力は以下の形式に厳密に従ってください:
- question: 問題文
- options: 選択肢のリスト（各選択肢はtextとisCorrectとtypeを持つ）
- explanation: 問題の詳細な解説
"""

    try:
        # Ollamaから応答を取得
        response_json = await ollama_client.generate_json(
            prompt=prompt,
            json_schema=QUIZ_SCHEMA,  # スキーマを明示的に指定
            timeout=API_TIMEOUT
        )

        # JSONデータの検証
        if not response_json:
            raise ValueError("Empty response from AI")

        # 必要なフィールドの存在チェック
        if not all(key in response_json for key in ["question", "options", "explanation"]):
            raise ValueError("Required fields missing in response")
            
        # 選択肢のチェック
        if len(response_json["options"]) < 2:
            raise ValueError("At least 2 options are required")
            
        # 少なくとも1つの正解が必要
        correct_options = [opt for opt in response_json["options"] if opt.get("isCorrect", False)]
        if not correct_options:
            raise ValueError("At least one option must be marked as correct")

        # uniqueなID生成
        question_id = str(uuid.uuid4())
        
        # QuizQuestionモデルに変換して返す
        return QuizQuestion(
            id=question_id,
            question=response_json["question"],
            options=response_json["options"],
            explanation=response_json["explanation"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid response format from AI: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/evaluate", response_model=FeedbackResponse, tags=["クイズ"])
async def evaluate_answer(
    request: EvaluateAnswerRequest,
    ollama_client: OllamaClient = Depends(get_ollama_client)
):
    """
    回答を評価する

    ユーザーの回答を受け取り、Ollama AIを使用して評価と解説を生成します。
    """
    try:
        # 正解の選択肢と選択された選択肢を抽出
        correct_options = [i for i, opt in enumerate(request.options) if opt.isCorrect]
        selected_indices = [opt.index for opt in request.selected_options]
        
        # 単一選択問題の場合の簡易判定
        single_choice = all(opt.type == "radio" for opt in request.options)
        if single_choice:
            is_correct = len(selected_indices) == 1 and selected_indices[0] in correct_options
        else:
            # 複数選択問題の場合
            is_correct = set(selected_indices) == set(correct_options)

        # 評価用プロンプトの構築
        prompt = f"""あなたは教育目的のクイズ評価AIです。
ユーザーの回答を評価し、詳細なフィードバックを提供してください。

問題:
{request.question}

選択肢:
{json.dumps([opt.model_dump() for opt in request.options], ensure_ascii=False)}

ユーザーの選択:
{json.dumps([opt.model_dump() for opt in request.selected_options], ensure_ascii=False)}

ユーザーの追加回答/質問:
{request.additional_answer or "なし"}

正解かどうか:
{is_correct}

以下の形式で回答を評価してください:
- isCorrect: ユーザーの回答が正解かどうか（boolean）
- feedback: 簡潔なフィードバックメッセージ
- detailedExplanation: 詳細な解説（概念の説明、関連する知識など）
- additionalResources: 追加リソース（オプション）
"""

        # Ollamaから応答を取得
        response_json = await ollama_client.generate_json(
            prompt=prompt,
            json_schema=EVALUATION_SCHEMA,
            timeout=API_TIMEOUT
        )

        # JSONデータの検証
        if not response_json:
            raise ValueError("Empty response from AI")

        # 必要なフィールドの存在チェック
        required_fields = ["isCorrect", "feedback", "detailedExplanation"]
        if not all(key in response_json for key in required_fields):
            raise ValueError(f"Required fields missing in response. Expected: {required_fields}, got: {list(response_json.keys())}")

        # FeedbackResponseモデルに変換して返す
        return FeedbackResponse(
            isCorrect=response_json["isCorrect"],
            feedback=response_json["feedback"],
            detailedExplanation=response_json["detailedExplanation"],
            additionalResources=response_json.get("additionalResources")
        )
        
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
