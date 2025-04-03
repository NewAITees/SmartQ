"""Ollama APIクライアントを実装するモジュール。"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, NoReturn, Union

import httpx
from httpx import AsyncClient, HTTPError

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ログディレクトリの作成
os.makedirs('logs', exist_ok=True)

# ファイルハンドラーの設定
fh = logging.FileHandler(
    f'logs/ollama_client_{datetime.now().strftime("%Y%m%d")}.log',
    encoding="utf-8"
)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)


class OllamaClient:
    """Ollama APIクライアントクラス。"""

    def __init__(
        self,
        model_name: str = "gemma3:27b",
        api_url: str = "http://localhost:11434",
        temperature: float = 0.7,
    ) -> None:
        """
        OllamaClientを初期化する。

        Args:
            model_name (str): 使用するモデル名
            api_url (str): Ollama APIのベースURL
            temperature (float): 生成時の温度パラメータ
        """
        self.model_name = model_name
        self.base_url = api_url.rstrip('/')  # 末尾のスラッシュを削除
        self.temperature = temperature
        logger.info(
            "OllamaClient initialized",
            extra={
                "model": model_name,
                "temperature": temperature,
                "base_url": self.base_url
            }
        )

    def _prepare_request_data(
        self,
        prompt: str,
        additional_options: Optional[Dict[str, Any]] = None,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        APIリクエストのデータを準備する。

        Args:
            prompt (str): 入力プロンプト
            additional_options (Optional[Dict[str, Any]]): 追加のオプション
            json_schema (Optional[Dict[str, Any]]): JSONスキーマ。Noneの場合は通常のテキスト形式。

        Returns:
            Dict[str, Any]: リクエストデータ
        """
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False,
        }

        # JSON形式の出力を要求する場合
        if json_schema:
            data["format"] = json_schema if isinstance(json_schema, dict) else "json"
        else:
            # デフォルトでJSONを要求
            data["format"] = "json"

        if additional_options:
            data.update(additional_options)

        return data

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """
        APIエラーを処理する。

        Args:
            error (Exception): 発生したエラー

        Raises:
            Exception: 元のエラーを再送出
        """
        if isinstance(error, HTTPError):
            logger.error("API request failed", exc_info=error)
        elif isinstance(error, json.JSONDecodeError):
            logger.error("Failed to decode API response", exc_info=error)
        else:
            logger.error("Unexpected error occurred", exc_info=error)
        raise error

    async def generate_text(
        self,
        prompt: str,
        additional_options: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> str:
        """
        テキストを非同期で生成する。

        Args:
            prompt (str): 入力プロンプト
            additional_options (Optional[Dict[str, Any]]): 追加のオプション
            timeout (float): リクエストのタイムアウト秒数

        Returns:
            str: 生成されたテキスト。エラー時は空文字列を返す。
        """
        try:
            data = self._prepare_request_data(prompt, additional_options)
            logger.debug("Sending async request to Ollama API", extra={"request_data": data})

            async with AsyncClient(timeout=timeout) as client:
                api_url = f"{self.base_url}/api/generate"
                response = await client.post(api_url, json=data)
                response.raise_for_status()

                result = response.json()
                generated_text = result.get("response", "")

            logger.debug(
                "Async text generation completed",
                extra={"text_length": len(generated_text)}
            )
            return generated_text

        except Exception as e:
            self._handle_api_error(e)
            return ""

    async def generate_json(
        self,
        prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
        additional_options: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        JSON形式のデータを非同期で生成する。

        Args:
            prompt (str): 入力プロンプト
            json_schema (Optional[Dict[str, Any]]): JSONスキーマ。Noneの場合は単純なJSON形式を指定。
            additional_options (Optional[Dict[str, Any]]): 追加のオプション
            timeout (float): リクエストのタイムアウト秒数

        Returns:
            Dict[str, Any]: 生成されたJSON。エラー時は空の辞書を返す。
        """
        try:
            data = self._prepare_request_data(prompt, additional_options, json_schema)
            logger.debug("Sending async JSON request to Ollama API", extra={"request_data": data})

            async with AsyncClient(timeout=timeout) as client:
                api_url = f"{self.base_url}/api/generate"
                response = await client.post(api_url, json=data)
                response.raise_for_status()

                result = response.json()
                generated_text = result.get("response", "{}")

            # レスポンスがJSON文字列の場合はパースする
            try:
                if isinstance(generated_text, str):
                    return json.loads(generated_text)
                return generated_text
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response", extra={"response": generated_text})
                return {}

        except Exception as e:
            self._handle_api_error(e)
            return {}
