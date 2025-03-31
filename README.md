# SmartQ

SmartQ は Ollama を活用したインテリジェントなクイズアプリケーションです。あらゆるトピックについて AI が生成する問題に挑戦し、知識を広げることができます。

![SmartQ Logo](https://via.placeholder.com/200x200?text=SmartQ)

## 機能

- **多様なトピック**: あらゆる学習分野に対応したクイズ生成
- **カスタマイズ可能**: システムプロンプトを編集して問題の出し方を調整可能
- **インタラクティブ**: 選択式の回答と自由記述による追加の質問が可能
- **詳細なフィードバック**: AI による回答の評価と解説
- **シンプルなインターフェース**: 直感的に使えるユーザーフレンドリーな UI

## スクリーンショット

![SmartQ Screenshot](https://via.placeholder.com/800x450?text=SmartQ+Screenshot)

## インストール方法

### 前提条件

- Python 3.8 以上
- [Ollama](https://ollama.ai/) がローカルにインストール済み

### セットアップ

1. リポジトリをクローン:

```bash
git clone https://github.com/yourusername/smartq.git
cd smartq
```

2. 依存パッケージをインストール:

```bash
pip install -r requirements.txt
```

3. Ollama サービスを起動:

```bash
ollama serve
```

4. アプリケーションを起動:

```bash
python app.py
```

5. ブラウザで以下の URL にアクセス:

```
http://localhost:8000
```

## 使い方

1. **トピックを選択**: ドロップダウンメニューから学習したいトピックを選択します
2. **問題を生成**: 「問題生成」ボタンをクリックして AI に問題を作成させます
3. **回答を選択**: 4 つの選択肢から答えを選びます
4. **補足回答を入力**: （オプション）テキストボックスに追加の回答や質問を入力できます
5. **回答を送信**: 「回答送信」ボタンをクリックしてフィードバックを受け取ります

必要に応じて、システムプロンプトを編集することで問題の出題方法をカスタマイズすることも可能です。

## カスタマイズ

### システムプロンプトの編集

システムプロンプトを編集することで、問題の難易度や形式を調整できます。例えば:

```
あなたは教育目的のクイズ作成AIです。
指定されたトピックに関する上級者向けの問題を作成してください。
問題は概念の応用力を問うもので、単なる暗記ではなく理解を問う内容にしてください。
```

### 環境変数

以下の環境変数を設定することで動作をカスタマイズできます:

```bash
# Ollama のエンドポイント（デフォルトは localhost:11434）
export OLLAMA_HOST=http://localhost:11434

# 使用するモデル（デフォルトは llama3）
export OLLAMA_MODEL=llama3

# アプリケーションのポート（デフォルトは 8000）
export APP_PORT=8000
```

## プロジェクト構成

```
/smartq
├── static/
│   ├── style.css            # CSS スタイルシート
│   └── script.js            # フロントエンド JavaScript
├── templates/
│   └── index.html           # メイン HTML テンプレート
├── app.py                   # FastAPI アプリケーション
├── requirements.txt         # 依存パッケージリスト
└── README.md                # プロジェクト説明
```

## 技術仕様

- **フロントエンド**: HTML, CSS, JavaScript
- **バックエンド**: FastAPI (Python)
- **AI 連携**: Ollama API
- **データ形式**: JSON

## 今後の拡張予定

- ユーザーセッション管理と履歴保存
- 難易度レベルの選択オプション
- 多言語対応
- モバイルアプリ対応
- クイズの結果をエクスポートする機能

## コントリビューション

バグ報告や機能リクエストは GitHub の Issue でお願いします。プルリクエストも歓迎です！

## ライセンス

MIT

## 作者

Your Name - [@yourusername](https://github.com/yourusername)

## 謝辞

- [Ollama](https://ollama.ai/) - ローカルで動作する AI モデルを提供
- [FastAPI](https://fastapi.tiangolo.com/) - 高速な Web API フレームワーク
- その他、このプロジェクトを支援してくれたすべてのツールとライブラリに感謝します

---

**SmartQ** - スマートにクイズで学ぶ、新しい学習体験。