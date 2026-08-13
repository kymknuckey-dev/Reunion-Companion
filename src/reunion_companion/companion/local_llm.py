from __future__ import annotations

"""Local Ollama provider for FFD 1.7 Build 3.

Only loopback Ollama endpoints are accepted. Reunion data therefore remains on
this Mac unless a later build explicitly introduces and enables another provider.
"""

from dataclasses import dataclass
import json
import os
import socket
from typing import Any
from pathlib import Path
from urllib import request, error, parse


class LocalLLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LocalLLMConfig:
    base_url: str = "http://127.0.0.1:11434"
    model: str | None = None
    timeout: float = 120.0
    temperature: float = 0.2
    num_ctx: int = 8192

    @classmethod
    def from_env(cls) -> "LocalLLMConfig":
        saved={}
        cfg=Path.home()/".reunion-companion"/"config.json"
        try:
            if cfg.exists(): saved=json.loads(cfg.read_text())
        except Exception: saved={}
        return cls(
            base_url=os.environ.get("REUNION_OLLAMA_URL", saved.get("ollama_url","http://127.0.0.1:11434")).rstrip("/"),
            model=(os.environ.get("REUNION_LLM_MODEL") or saved.get("llm_model") or "").strip() or None,
            timeout=float(os.environ.get("REUNION_LLM_TIMEOUT", saved.get("llm_timeout",120))),
            temperature=float(os.environ.get("REUNION_LLM_TEMPERATURE", saved.get("llm_temperature",0.2))),
            num_ctx=int(os.environ.get("REUNION_LLM_CONTEXT", saved.get("llm_context",8192))),
        )


def _assert_loopback(url: str) -> None:
    parsed = parse.urlparse(url)
    host = (parsed.hostname or "").casefold()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return
    try:
        infos = socket.getaddrinfo(host, parsed.port or 80)
        if infos and all(info[4][0].startswith("127.") or info[4][0] == "::1" for info in infos):
            return
    except Exception:
        pass
    raise LocalLLMError(
        "FFD 1.7 Build 3 only permits a local Ollama endpoint. "
        "Set REUNION_OLLAMA_URL to localhost or 127.0.0.1."
    )


class OllamaClient:
    def __init__(self, config: LocalLLMConfig | None = None):
        self.config = config or LocalLLMConfig.from_env()
        _assert_loopback(self.config.base_url)
        self._resolved_model: str | None = None

    def _json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.config.base_url + path
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=self.config.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise LocalLLMError(f"Local Ollama request failed: {exc}") from exc

    def installed_models(self) -> list[str]:
        data = self._json("/api/tags")
        names = []
        for item in data.get("models", []):
            name = str(item.get("name") or item.get("model") or "").strip()
            if name:
                names.append(name)
        return names

    def resolve_model(self) -> str:
        if self._resolved_model:
            return self._resolved_model
        installed = self.installed_models()
        if self.config.model:
            if self.config.model not in installed:
                raise LocalLLMError(
                    f"Configured Ollama model '{self.config.model}' is not installed. "
                    f"Installed models: {', '.join(installed) if installed else 'none'}."
                )
            self._resolved_model = self.config.model
            return self._resolved_model
        preferred = ("gemma3:4b", "qwen3:4b", "llama3.2:3b", "gemma3:1b")
        for wanted in preferred:
            if wanted in installed:
                self._resolved_model = wanted
                return wanted
        if installed:
            self._resolved_model = installed[0]
            return installed[0]
        raise LocalLLMError(
            "Ollama is running but no local model is installed. "
            "Install a model such as gemma3:4b, or set REUNION_LLM_MODEL to an installed model."
        )

    def generate(self, prompt: str) -> str:
        model = self.resolve_model()
        data = self._json(
            "/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_ctx": self.config.num_ctx,
                },
            },
        )
        text = str(data.get("response") or "").strip()
        if not text:
            raise LocalLLMError("Local Ollama returned an empty response.")
        return text


def local_llm_status() -> dict[str, Any]:
    try:
        client = OllamaClient()
        model = client.resolve_model()
        return {"available": True, "provider": "Ollama", "model": model, "local": True}
    except LocalLLMError as exc:
        return {"available": False, "provider": "Ollama", "model": None, "local": True, "error": str(exc)}
