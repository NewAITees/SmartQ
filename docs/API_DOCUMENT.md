# SmartQ API ドキュメント

SmartQ APIは、Ollama AIを活用したクイズアプリケーションのためのインターフェースを提供します。このドキュメントでは、利用可能なエンドポイントとその使用方法について説明します。

## 基本情報

* **ベースURL**: `http://localhost:8000`
* **APIドキュメント**: `/api/docs` (Swagger UI), `/api/redoc` (ReDoc)
* **コンテンツタイプ**: `application/json`

## 認証

現在のバージョンでは認証は必要ありません。

## エンドポイント

### 1. 問題生成 API

AI が指定されたトピックに関する問題を生成します。

* **URL**: `/api/generate`
* **メソッド**: `POST`
* **リクエスト本文**:

```json
{
  "topic": "string",         // 問題のトピック（例: 'programming', 'science'）
  "system_prompt": "string", // 問題生成のためのシステムプロンプト
  "knowledge_base": "string" // 追加の知識ベース情報（オプション）
}
```

* **レスポンス**:

```json
{
  "id": "string",                 // 問題の識別子
  "question": "string",           // 問題文
  "options": ["string", ...],     // 選択肢のリスト（4つの項目）
  "correct_answer": 0             // 正解の選択肢のインデックス（0-3）
}
```

* **例**:

リクエスト:
```json
{
  "topic": "programming",
  "system_prompt": "初心者向けのPythonプログラミングに関する問題を作成してください。",
  "knowledge_base": "Pythonはインタープリタ型の高水準プログラミング言語です。"
}
```

レスポンス:
```json
{
  "id": "12345",
  "question": "Pythonで変数に値を代入するために使用する演算子は何ですか？",
  "options": ["==", "=", "+=", "=>"],
  "correct_answer": 1
}
```

* **エラーコード**:
  * `502`: AIからの応答が無効な形式の場合
  * `500`: 内部サーバーエラー

## レスポンスの共通形式

### エラーレスポンス

エラーが発生した場合、APIは以下の形式でレスポンスを返します：

```json
{
  "detail": "エラーの詳細メッセージ"
}
```

## 環境変数

APIの動作は以下の環境変数によってカスタマイズできます：

* `OLLAMA_HOST`: Ollama APIのホスト (デフォルト: `http://localhost:11434`)
* `OLLAMA_MODEL`: 使用するAIモデル (デフォルト: `llama3`)
* `API_TIMEOUT`: APIリクエストのタイムアウト秒数 (デフォルト: `30`)
* `APP_PORT`: アプリケーションポート (デフォルト: `8000`)

## 使用例

### cURLを使用した問題生成

```bash
curl -X 'POST' \
  'http://localhost:8000/api/generate' \
  -H 'Content-Type: application/json' \
  -d '{
  "topic": "science",
  "system_prompt": "中学生向けの科学の問題を作成してください。",
  "knowledge_base": "光の速さは秒速約30万キロメートルです。"
}'
```

### JavaScriptを使用した例

```javascript
// 問題生成
async function generateQuestion() {
  const response = await fetch('http://localhost:8000/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      topic: 'history',
      system_prompt: '世界史に関する問題を作成してください。',
      knowledge_base: '第二次世界大戦は1939年から1945年まで続きました。'
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `API error: ${response.status}`);
  }
  
  return await response.json();
}

// 回答評価
async function evaluateAnswer(question, selectedAnswer, additionalAnswer) {
  const response = await fetch('http://localhost:8000/api/evaluate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question_id: question.id,
      selected_answer: selectedAnswer,
      additional_answer: additionalAnswer,
      question: question.question,
      options: question.options,
      correct_answer: question.correct_answer
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `API error: ${response.status}`);
  }
  
  return await response.json();
}
```

## エラーハンドリング

APIにリクエストを送信する際は、以下のエラーケースを処理することを推奨します：

1. ネットワークエラー (APIサーバーに接続できない)
2. タイムアウトエラー (応答が返ってくるまでに時間がかかりすぎる)
3. バリデーションエラー (リクエストボディが不正)
4. AIレスポンスが無効 (AIが期待する形式で応答しない)
5. サーバー内部エラー

例：

```javascript
try {
  const result = await callApi('/api/generate', data);
  // 結果を処理
} catch (error) {
  console.error('API呼び出しエラー:', error.message);
  // ユーザーにエラーを通知
}
```

## API変更履歴

### v0.1.0 (現在のバージョン)
- 初期バージョンリリース
- 問題生成と回答評価の基本機能を実装
  * `502`: AIからの応答が無効な形式の場合
  * `500`: 内部サーバーエラー

### 2. 回答評価 API

ユーザーの回答を評価し、フィードバックを提供します。

* **URL**: `/api/evaluate`
* **メソッド**: `POST`
* **リクエスト本文**:

```json
{
  "question_id": "string",           // 問題の識別子
  "selected_answer": 0,              // 選択された回答のインデックス（0-3）
  "additional_answer": "string",     // 追加の回答や説明（オプション）
  "question": "string",              // 問題文
  "options": ["string", ...],        // 選択肢のリスト
  "correct_answer": 0                // 正解のインデックス
}
```

* **レスポンス**:

```json
{
  "is_correct": true,                // 回答が正解かどうか
  "message": "string"                // フィードバックメッセージ
}
```

* **例**:

リクエスト:
```json
{
  "question_id": "12345",
  "selected_answer": 1,
  "additional_answer": "代入演算子は値を変数に格納するために使います。",
  "question": "Pythonで変数に値を代入するために使用する演算子は何ですか？",
  "options": ["==", "=", "+=", "=>"],
  "correct_answer": 1
}
```

レスポンス:
```json
{
  "is_correct": true,
  "message": "正解です！「=」はPythonで変数に値を代入するために使用される演算子です。例えば「x = 10」のように使います。等価演算子（==）と混同しないようにしましょう。これは値が等しいかどうかを比較するためのものです。"
}
```

* **エラーコード**: