
# ARCHITECTURE.md

## 1. 概要

このドキュメントは、**Ollama AI クイズアプリケーション** のシステムアーキテクチャについて説明します。このアプリケーションは、ユーザーが指定したトピックに基づいて Ollama AI が生成するクイズにインタラクティブに回答できる Web アプリケーションです。主な目的は、AI との対話を通じて教育的な体験を提供することです。

## 2. アーキテクチャ概要図

システムの高レベルなアーキテクチャを以下に示します。基本的な構成は、ブラウザ上で動作するフロントエンド、APIを提供するバックエンド、そしてAIモデルを実行するOllamaサービスから成ります。

```mermaid
graph TD
    subgraph User Interaction Layer
        A[ユーザー] -->|Web Browser| B(Frontend - HTML/CSS/JS);
    end

    subgraph Application Layer
        C(Backend - FastAPI);
    end

    subgraph AI Service Layer
        D(Ollama API - Local);
    end

    B -->|1. API Requests (Generate/Evaluate)| C;
    C -->|2. Prompt Construction & Ollama Call| D;
    D -->|3. AI Response (JSON)| C;
    C -->|4. Response Processing & Validation| B;
    B -->|5. UI Update| A;

    style User Interaction Layer fill:#e6f7ff,stroke:#91d5ff,stroke-width:2px
    style Application Layer fill:#f6ffed,stroke:#b7eb8f,stroke-width:2px
    style AI Service Layer fill:#fffbe6,stroke:#ffe58f,stroke-width:2px

3. 主要コンポーネント

システムは以下の主要コンポーネントで構成されます。

Frontend (ブラウザ):

技術: HTML5, CSS3, Vanilla JavaScript (ES6+)

役割:

ユーザーインターフェース (UI) のレンダリングと表示。

ユーザー入力の受付（トピック選択、システムプロンプト編集、回答選択、自由記述）。

Backend API への非同期リクエスト送信（問題生成、回答評価）。

Backend から受け取ったデータの処理と UI への反映（問題表示、フィードバック表示）。

基本的なクライアントサイドの入力検証（例: 選択肢が選ばれているか）。

Backend (サーバー):

技術: Python 3.8+, FastAPI, Pydantic, Ollama Python Client

役割:

フロントエンドからの HTTP API リクエストの受付と処理。

リクエストデータの検証 (Pydantic モデルを使用)。

Ollama に送信するプロンプトの動的な構築（システムプロンプト、ユーザー入力、コンテキスト情報を含む）。

Ollama API との通信（問題生成、回答評価のリクエスト送信）。

Ollama からの応答 (JSON) の受信、パース、検証。

応答データの整形とフロントエンドへの返却 (JSON)。

静的ファイル (CSS, JS) および HTML テンプレートの配信。

Ollama API (ローカルAIサービス):

技術: Ollama (例: llama3 モデル)

役割:

バックエンドから受け取ったプロンプトに基づいて、大規模言語モデル (LLM) を実行。

指示された形式 (JSON) で、クイズ問題や回答評価のテキストを生成。

生成結果をバックエンドに返却。

4. 技術選定の理由 (主要なもの)

FastAPI (Backend):

パフォーマンス: ASGI に基づく高いパフォーマンスと非同期処理能力。

開発効率: Python の型ヒントを活用した自動データ検証 (Pydantic) と自動 API ドキュメント生成 (Swagger UI, ReDoc)。

エコシステム: Python の豊富なライブラリ（Ollamaクライアントなど）を活用可能。

Vanilla JavaScript (Frontend):

軽量性: フレームワークのオーバーヘッドがなく、シンプルなアプリケーションに適している。

依存性: ビルドツールや複雑な環境設定が不要で、迅速な開発が可能。

学習コスト: 標準的なウェブ技術であり、多くの開発者にとって馴染み深い。

Ollama:

ローカル実行: 外部 API への依存やコストを削減し、データプライバシーを確保しやすい。

柔軟性: 様々なオープンソース LLM を容易に切り替えて利用可能。

制御: プロンプトエンジニアリングによる出力のカスタマイズが容易。

JSON:

標準: Web API における事実上の標準データ交換フォーマット。

相互運用性: JavaScript (フロントエンド) と Python (バックエンド) の両方でネイティブに近い形で容易に扱える。

構造化: 複雑なデータ（問題、選択肢、説明など）を構造的に表現可能。

5. データフロー

主要なユースケースにおけるデータフローを示します。

5.1 問題生成フロー

ユーザーがトピックを選択し、問題生成をリクエストする際のデータフローです。

sequenceDiagram
    participant User
    participant Frontend (JS)
    participant Backend (FastAPI)
    participant Ollama API

    User->>Frontend: トピック選択、(オプション:プロンプト編集)、生成ボタン押下
    Frontend->>Backend: POST /generate_question\n(Request: {topic, system_prompt})
    activate Backend
    Backend->>Ollama API: ollama.generate()\n(Prompt: 問題生成指示, format: json)
    activate Ollama API
    Ollama API-->>Backend: AI Response\n(JSON: {question, options, correct_answer, explanation})
    deactivate Ollama API
    Backend-->>Frontend: HTTP 200 OK\n(Response: 検証済み問題JSON)
    deactivate Backend
    Frontend->>Frontend: 問題・選択肢をUIに表示
    Frontend->>User: 問題表示
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Mermaid
IGNORE_WHEN_COPYING_END
5.2 回答評価フロー

ユーザーがクイズに回答し、フィードバックを要求する際のデータフローです。

sequenceDiagram
    participant User
    participant Frontend (JS)
    participant Backend (FastAPI)
    participant Ollama API

    User->>Frontend: 回答選択、(オプション:自由記述入力)、送信ボタン押下
    Frontend->>Backend: POST /evaluate_answer\n(Request: {question, options, correct_answer, user_selection, user_free_text})
    activate Backend
    Backend->>Ollama API: ollama.generate()\n(Prompt: 回答評価指示, format: json)
    activate Ollama API
    Ollama API-->>Backend: AI Response\n(JSON: {is_correct, feedback, explanation, ...})
    deactivate Ollama API
    Backend-->>Frontend: HTTP 200 OK\n(Response: 検証済み評価JSON)
    deactivate Backend
    Frontend->>Frontend: フィードバックをUIに表示
    Frontend->>User: フィードバック表示
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Mermaid
IGNORE_WHEN_COPYING_END
6. フォルダ構成概要

プロジェクトの基本的なフォルダ構成を示します。

graph LR
    subgraph Project Root (ollama-quiz-app)
        A(app.py)
        B(requirements.txt)
        C(README.md)
        D(static/);
        E(templates/);
        F(DOCS/);
    end

    subgraph static
        direction LR
        D1(style.css)
        D2(script.js)
    end

    subgraph templates
        direction LR
        E1(index.html)
    end

    subgraph DOCS
        direction LR
        F1(ARCHITECTURE.md)
        F2(...)
    end

    D --- D1 & D2
    E --- E1
    F --- F1 & F2

    style Project Root fill:#f9f9f9,stroke:#333,stroke-width:2px
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Mermaid
IGNORE_WHEN_COPYING_END

app.py: FastAPIアプリケーションのエントリーポイントとAPIエンドポイント定義。

requirements.txt: Python依存関係リスト。

README.md: プロジェクトの概要と基本的な使用方法。

static/: CSS、JavaScript、画像などの静的ファイルを格納。

templates/: Jinja2などのHTMLテンプレートファイルを格納。

DOCS/: このドキュメントを含む、プロジェクト関連の設計・開発ドキュメントを格納。

IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END