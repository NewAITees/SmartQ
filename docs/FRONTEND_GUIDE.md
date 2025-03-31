# SmartQ フロントエンド開発ガイド

## 1. 概要

SmartQ は、Ollama を活用してユーザーが提供した知識ベースから動的にクイズを生成し、インタラクティブな学習体験を提供するシングルページアプリケーション（SPA）です。
このドキュメントは、SmartQ フロントエンド開発におけるコーディング規約、アーキテクチャ、主要な機能の実装方針について説明します。

**技術スタック:**

*   HTML5
*   CSS3 (カスタムプロパティ使用)
*   Vanilla JavaScript (ES6+)
*   Ollama API (バックエンドとして利用)

## 2. プロジェクト構造

プロジェクトは単一の `index.html` ファイルで構成されています。

*   **`<head>`**: メタ情報、タイトル、CSSスタイル定義 (`<style>`)
*   **`<body>`**:
    *   `.container`: アプリケーション全体のラッパー (Flexboxでフッターを下部に固定)
    *   `header`: アプリケーションタイトルとタグライン
    *   `.main-content`: 主要コンテンツエリア (Gridレイアウト)
        *   `#settingsPanel`: 左パネル (設定、知識入力、問題生成)
        *   `#quizPanel`: 右パネル (クイズ表示、回答、フィードバック)
    *   `footer`: コピーライト情報
*   **`<script>`**: JavaScriptコード (DOM操作、イベント処理、API連携)

## 3. コーディングスタイル

### 3.1. HTML

*   **セマンティック HTML**: 可能な限りセマンティックな要素 (`<header>`, `<main>`, `<section>`, `<footer>`, `<label>`, `<button>`, `<fieldset>`, `<legend>`) を使用します。
*   **アクセシビリティ (A11y)**:
    *   適切な `aria-*` 属性 (例: `aria-label`, `aria-labelledby`, `aria-live`, `role`) を使用し、スクリーンリーダー等の支援技術に対応します。
    *   フォーム要素には `<label>` を関連付けます (`for` 属性を使用)。
    *   インタラクティブ要素はキーボードで操作可能にします。
    *   選択肢は `<fieldset>` と `<legend>` でグループ化し、各選択肢は `<label>` でラップしてクリック/タップ領域を広げます。
*   **クラス命名**: 要素の役割や状態を示す、明確で一貫性のあるケバブケース (例: `panel-title`, `loading-spinner`, `option-label.selected`) を使用します。特定の命名規則 (BEMなど) は強制しませんが、予測可能な命名を心がけます。
*   **インデント**: 4スペースを使用します。

### 3.2. CSS

*   **カスタムプロパティ (Variables)**: 色、影、角丸などの共通の値は `:root` で定義されたCSSカスタムプロパティ (`--primary-color` など) を使用します。これにより、テーマ変更や一括変更が容易になります。
*   **命名規則**: HTMLクラス名と同様に、ケバブケースを使用します。
*   **セレクタ**: 詳細度を低く保つように心がけ、IDセレクタはJavaScriptからの参照や特定箇所のスタイル調整に限定的に使用します。クラスセレクタを主体とします。
*   **レスポンシビリティ**: モバイルファーストアプローチではありませんが、メディアクエリ (`@media`) を使用して、主要なブレークポイント (900px, 600px, 480px) でレイアウトを調整します。
*   **単位**: `rem`, `em`, `%`, `vh`, `vw` などの相対単位を優先的に使用し、固定ピクセル (`px`) はボーダーやアイコンサイズなど、スケーリングが不要な箇所に限定します。
*   **Flexbox/Grid**: レイアウトには Flexbox と Grid Layout を積極的に活用します。特に、全体レイアウト（ヘッダー、メイン、フッター）やパネル内部、ボタンコンテナなどで使用しています。
*   **トランジション/アニメーション**: UIの状態変化 (ホバー、フォーカス、表示/非表示) をスムーズに見せるために `transition` プロパティを使用します。ローディングスピナーや要素のフェードインには `@keyframes` を使用します。

### 3.3. JavaScript

*   **変数宣言**: `const` をデフォルトとし、再代入が必要な場合にのみ `let` を使用します。`var` は使用しません。
*   **関数**: `function` キーワードによる関数宣言を主に使用しています。一貫性を保つことを推奨します。
*   **DOM操作**:
    *   `getElementById`, `querySelector`, `querySelectorAll` を使用してDOM要素を取得します。頻繁にアクセスする要素は、スクリプトの先頭で定数にキャッシュします。
    *   DOMの更新は効率的に行い、不要な再描画を避けます。特に `updateUIState` 関数でUI要素の表示/非表示や属性変更を一元管理します。
    *   ユーザー生成コンテンツやAPI応答を表示する際は、XSSを防ぐために適切なサニタイズ処理 (`sanitizeText`, `safeRenderHTML`) を行います。
*   **イベント処理**:
    *   `addEventListener` を使用します。
    *   選択肢の選択にはイベントデリゲーションを使用せず、各ラジオボタンを含む `fieldset` に `change` イベントリスナーを設定しています (`handleOptionSelect`)。
*   **状態管理**:
    *   アプリケーションの状態は `appState` オブジェクトで一元管理します (詳細は「5. 状態管理」を参照)。
    *   UIの更新は `updateUIState` 関数を通じて行い、状態とUIの一貫性を保ちます。
*   **API通信**:
    *   `fetch` API を使用して Ollama API と通信します。
    *   非同期処理には `async/await` を使用します。
    *   `callOllamaAPI` 関数でAPI呼び出しロジックを共通化します。
    *   リクエストキャンセル機能のために `AbortController` を使用します。
    *   タイムアウト処理 (`Promise.race` と `setTimeout`) を実装します。
*   **エラーハンドリング**:
    *   `try...catch` ブロックを使用してAPI呼び出しや処理中のエラーを捕捉します。
    *   ユーザーにわかりやすいエラーメッセージを表示します (`#generateError`, `#submitError`)。エラー詳細 (`#generateErrorDetails`, `#submitErrorDetails`) も `code` タグ内に表示します。
    *   コンソールにも詳細なエラー情報を出力します (`console.error`)。
*   **コードコメント**: 主要な関数や複雑なロジック、状態の説明にコメントを追加しています。
*   **モジュール化**: 現状は単一ファイルですが、機能が複雑化する場合は、ファイルを分割し、ES Modules (`import`/`export`) の使用を検討します。

## 4. UIコンポーネント

主要なUI要素の実装方針です。

*   **パネル (`.panel`)**: 設定エリアとクイズエリアの基本コンテナ。Flexboxで内部要素を縦に配置し、可変コンテンツ（テキストエリア）が伸長するように設定。
*   **フォーム要素**: `<label>`, `<select>`, `<textarea>`, `<input type="radio">`, `<button>` を使用。一貫したスタイルを適用。`<fieldset>` と `<legend>` で選択肢グループをマークアップ。
*   **ボタン (`button`)**: `:disabled` 状態のスタイルを定義。ホバー、アクティブエフェクトを追加（無効状態では適用されない）。
*   **選択肢 (`.option-label`, `.option-radio`)**:
    *   `<label>` 要素でラジオボタンとテキスト（`.option-text`）をラップし、ラベル全体をクリック可能に。
    *   `role="radiogroup"` (`fieldset`) と `role="radio"` (未使用だが暗黙的) でアクセシビリティを確保。
    *   選択状態は `.selected` クラスで視覚的に示し、JavaScript (`handleOptionSelect`) で管理。
*   **ローディングインジケーター (`.loading`)**: スピナーアニメーションを表示し、`role="status"` と `aria-live="polite"` で状態変化を伝達。
*   **エラーメッセージ (`.error-message`)**: エラー発生時に表示。`role="alert"` と `aria-live="assertive"` で重要な情報を即時伝達。エラーの概要と詳細 (`<code>`) を分けて表示。
*   **フィードバック (`.feedback-container`)**: 回答送信後に表示。正解/不正解に応じてスタイル (`.feedback-correct`/`.feedback-incorrect`) と背景色を変更。内部は `.explanation`, `.user-response`, `.additional-resources` に分割され、それぞれにボーダーや背景色が適用される。

## 5. 状態管理

アプリケーションの状態はグローバルな `appState` オブジェクトで管理されます。

```javascript
const appState = {
    currentQuiz: { question: "", options: {}, correctAnswer: "" }, // 現在のクイズデータ
    userSelection: null, // ユーザーが選択した選択肢 (A, B, C, D)
    status: 'initial', // アプリケーションの現在の状態 (文字列)
    generateAbortController: null, // 問題生成APIリクエストのAbortController
    evaluateAbortController: null, // 評価APIリクエストのAbortController
};
```

appState.status は以下のいずれかの値を取ります:

initial: 初期状態、または「次の問題へ」が押された後

generating: 問題生成API呼び出し中

generated: 問題生成完了、ユーザーの回答待ち

submitting: 回答評価API呼び出し中

submitted: 回答評価完了、フィードバック表示中

error_generate: 問題生成中にエラー発生

error_submit: 回答評価中にエラー発生

UIの更新は updateUIState(newState) 関数に集約されています。この関数は新しい状態 (newState) を受け取り、appState.status を更新し、それに応じて以下の要素を制御します:

ボタン (generateBtn, submitBtn, nextQuestionBtn) の有効/無効 (disabled 属性)

ローディングインジケーター (#loadingGenerate, #loadingSubmit) の表示/非表示 (.visible クラス)

エラーメッセージ (#generateError, #submitError) の表示/非表示 (.visible クラス)

クイズコンテナ (#quizContainer) と初期メッセージ (#initialMessage) の表示/非表示 (display スタイル)

フィードバックコンテナ (#feedbackContainer) の表示/非表示 (.visible クラス)

選択肢ラジオボタンの有効/無効 (disabled 属性) とラベルのスタイル (opacity, cursor)

状態遷移に応じたフォーカス管理

これにより、状態の変更が一貫したUIの変更に反映されることを保証します。

6. API連携 (Ollama)
Ollama API との通信は callOllamaAPI(endpoint, prompt, abortSignal) 関数で行います。

エンドポイント: API_ENDPOINTS 定数で定義 (デフォルトは http://localhost:11434/api/generate)。ローカルOllamaを直接呼び出すことを想定。

モデル: OLLAMA_MODEL 定数で定義 (llama3 など)。

リクエスト: fetch API を使用したPOSTリクエスト。prompt と model をJSONボディに含めます。stream: false を指定し、完全な応答を一度に受け取ります。

プロンプト:

問題生成: systemPromptTextarea の内容、knowledgeInput の内容、選択された難易度を組み合わせてプロンプトを構築します。AIに出力形式（問題、A/B/C/D、正解: [ラベル]）を厳密に指示することが重要です。

回答評価: 現在の問題、選択肢、正解、ユーザーの選択、ユーザーの追加テキストを組み合わせて評価用のプロンプトを構築します。AIに期待する出力形式（判定、説明、追加回答について、追加情報）を詳細に指示します。

レスポンスパース:

APIからの応答 (JSONの response フィールドに含まれるテキスト) を受け取ります。

parseQuestionResponse 関数で問題生成レスポンス（テキスト）をパースし、{ question, options, correctAnswer } オブジェクトに変換します。応答形式が期待通りでない場合はエラーをスローします。

parseEvaluationResponse 関数で評価レスポンス（テキスト）をパースし、{ judgement, explanation, additionalInfo, userResponseFeedback } オブジェクトに変換します。こちらは多少柔軟なパースロジックになっています。

タイムアウトとキャンセル: Promise.race と setTimeout を使用して、設定時間 (API_TIMEOUT) 内に応答がない場合にタイムアウトエラーを発生させます。また、AbortController を使用して、進行中のAPIリクエストをキャンセル可能にしています（例：新しい問題を生成する際に前の生成リクエストをキャンセル）。

7. エラーハンドリング
API通信エラー: fetch 自体のエラー (ネットワーク接続不可など) や、APIサーバーからのエラー応答 (4xx, 5xxステータスコード) を callOllamaAPI 内の try...catch で捕捉します。

タイムアウトエラー: Promise.race を使用して実装されたタイムアウトを捕捉します。

レスポンスパースエラー: parseQuestionResponse, parseEvaluationResponse 内で期待した形式のデータが得られなかった場合にエラーをスローし、呼び出し元の catch ブロックで捕捉します。

リクエストキャンセル: AbortController.abort() によって発生する AbortError は捕捉しますが、これは通常の操作の一部であるため、ユーザーにエラー表示は行いません（コンソールログには記録）。

ユーザーへの通知: 捕捉したエラー（キャンセル以外）は、対応するエラーメッセージ領域 (#generateError, #submitError) に表示されます。エラーメッセージには、発生したエラーの種類と、可能であればAPIからの応答の一部をデバッグ情報として含めます (#generateErrorDetails, #submitErrorDetails)。

状態更新: エラー発生時は appState.status を error_generate または error_submit に設定し、updateUIState を呼び出してUIを適切な状態（ローディング解除、エラー表示など）にします。

コンソールログ: 開発者向けに、より詳細なエラー情報（エラーオブジェクト、受信した応答など）を console.error で出力します。

8. アクセシビリティ (A11y)
ランドマーク: <header>, <main>, <footer>, <section> などのランドマーク要素を使用してページ構造を明確にします。各パネルに aria-labelledby でタイトルを関連付けています。

ARIA属性:

role: radiogroup, status, alert などで要素の役割を明示します。

aria-label, aria-labelledby: ボタンや入力フィールドに適切なラベルを提供します。

aria-live: polite (ローディング、問題文表示) や assertive (エラー) で、動的に変化するコンテンツをスクリーンリーダーに通知します。

キーボードナビゲーション: 全てのインタラクティブ要素 (ボタン、リンク、フォーム要素) はタブキーでフォーカス可能にし、Enter/Spaceキーで操作可能です。選択肢の <label> もフォーカス可能で、Spaceキーで選択できます（ブラウザ標準動作）。

フォーカス管理: updateUIState 関数内で、状態遷移に応じて論理的な要素 (例: 問題生成後の最初の選択肢、回答送信後の「次の問題へ」ボタン、初期状態に戻った際の「問題を生成する」ボタン) にプログラム的にフォーカスを移動させ、ユーザーの操作フローを補助します。

コントラスト: テキストと背景のコントラスト比は WCAG の基準を満たすように、:root で定義されたCSSカスタムプロパティの値を設定します。

フォームの関連付け: <label> の for 属性と入力要素の id を使用して、ラベルと入力フィールドを明確に関連付けます。選択肢グループは <fieldset> と <legend> で構造化します。

9. レスポンシブデザイン
CSSメディアクエリ (@media) を使用して、異なる画面幅に対応します。

主なブレークポイントと変更点:

max-width: 900px: .main-content のGridレイアウトが2カラムから1カラムに変更されます。

max-width: 600px: パディングや一部要素の min-height が調整されます。

max-width: 480px: スマートフォン向けにさらに調整。ボタンコンテナ (.button-container) の flex-direction が column になり、ボタンが縦に積まれます。

flex-grow, flex-shrink やグリッドレイアウトの fr 単位を活用して、コンテンツが可変幅に適切に対応するようにします（例: .form-group.flex-grow 内の textarea）。

テキストの折り返し (word-break: break-all など）や要素の最小/最大幅にも配慮します。

10. ローカルでの実行
このアプリケーションはバックエンドサーバーを必要とせず、Ollamaがローカルで動作していれば、index.html ファイルを直接ウェブブラウザで開くことで実行できます。

注意点:

CORS (Cross-Origin Resource Sharing): ブラウザから直接ローカルの Ollama API (http://localhost:11434) にアクセスする場合、Ollama サーバー側で適切なCORSヘッダーを設定する必要があります。設定しない場合、ブラウザのセキュリティ制約によりAPI呼び出しがブロックされる可能性があります。

Ollamaの起動時に環境変数 OLLAMA_ORIGINS を設定することで対応できます。例えば、すべてのオリジンを許可する場合は OLLAMA_ORIGINS='*'、特定のオリジンのみ許可する場合は OLLAMA_ORIGINS='http://localhost,http://127.0.0.1,file://' のように設定します（file:// はローカルファイルからのアクセスを許可する場合）。セキュリティリスクを考慮し、必要最小限のオリジンを指定することが推奨されます。

APIエンドポイント: JavaScript内の API_ENDPOINTS 定数が、ローカルで動作しているOllama APIエンドポイントを正しく指していることを確認してください (デフォルトは http://localhost:11434/api/generate)。

11. 今後の改善点 (検討事項)
コンポーネント化: UI要素を再利用可能なJavaScript関数またはクラス (Web Componentsなど) に分割し、コードの見通しと再利用性を向上させる。

テスト: Jest や Vitest、Testing Library などを用いて単体テスト・結合テストを追加し、コードの品質と信頼性を高める。

ビルドツール: Vite や Webpack などのビルドツールを導入し、コードの最適化（Minify, Uglify）、モジュールバンドル、開発サーバー機能、ホットリロードなどを利用して開発効率を向上させる。

CSSプリプロセッサ/フレームワーク: Sass や Less を導入して CSS の記述を効率化したり、Tailwind CSS などのユーティリティファーストフレームワークの利用を検討する。

状態管理ライブラリ: アプリケーションがより複雑になった場合、Redux Toolkit, Zustand, Pinia などの状態管理ライブラリの導入を検討し、状態管理ロジックをより堅牢にする。

UIライブラリ/フレームワーク: より大規模な開発や高度なUIコンポーネントが必要な場合、React, Vue, Svelte などのフレームワークや、MUI, Chakra UI, Bootstrap などのUIライブラリの利用を検討する。

バックエンドプロキシ: CORS問題を恒久的に回避し、APIキー管理やレートリミットなどの機能を追加したい場合に、間に簡単なバックエンドプロキシサーバー（Node.js/Express, Python/Flask など）を構築する。

ストリーミング応答: Ollama API のストリーミング応答 (stream: true) に対応し、AIの応答を逐次表示することで、特に長い応答の場合の体感速度を向上させる。

永続化: 設定や過去のクイズ履歴などを localStorage や sessionStorage に保存する機能を追加する。