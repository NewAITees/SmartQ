"""OllamaのJSON出力用スキーマ定義"""

# 問題生成用のスキーマ
QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "クイズの問題文"
        },
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "選択肢のテキスト"},
                    "isCorrect": {"type": "boolean", "description": "この選択肢が正解かどうか"},
                    "type": {"type": "string", "enum": ["radio", "checkbox"], "description": "選択肢のタイプ（ラジオボタンかチェックボックスか）", "default": "radio"}
                },
                "required": ["text", "isCorrect"]
            },
            "minItems": 2,
            "maxItems": 5,
            "description": "問題の選択肢リスト"
        },
        "explanation": {
            "type": "string",
            "description": "問題の解説文（回答後に表示）"
        }
    },
    "required": ["question", "options", "explanation"]
}

# 回答評価用のスキーマ
EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "isCorrect": {
            "type": "boolean",
            "description": "ユーザーの回答が正解かどうか"
        },
        "feedback": {
            "type": "string",
            "description": "回答に対するフィードバック"
        },
        "detailedExplanation": {
            "type": "string",
            "description": "詳細な解説や補足情報"
        },
        "additionalResources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["title", "description"]
            },
            "description": "追加の学習リソース（オプション）"
        }
    },
    "required": ["isCorrect", "feedback", "detailedExplanation"]
} 