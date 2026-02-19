import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

class ProviderError(Exception):
    """Custom exception for provider-related errors."""
    pass

class LLMProvider(ABC):
    def __init__(self):
        self.metrics_enabled = True
        self.metrics_path = Path.home() / ".local" / "heidi_engine" / "metrics" / "provider_requests.jsonl"

    def set_metrics_config(self, enabled: bool, path: Optional[str] = None):
        self.metrics_enabled = enabled
        if path:
            self.metrics_path = Path(path)

    def log_metrics(self, model: str, latency_ms: int, input_tokens: Optional[int], output_tokens: Optional[int], status: str, error_kind: Optional[str] = None):
        if not self.metrics_enabled:
            return
        
        record = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provider_id": self.get_name(),
            "model": model,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "status": status
        }
        if error_kind:
            record["error_kind"] = error_kind

        try:
            self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[WARN] Failed to write provider metrics: {e}", file=sys.stderr)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            raise ProviderError("openai package not installed. Run 'pip install openai'")

    def generate(self, prompt: str, **kwargs) -> str:
        start_time = time.time()
        input_tokens = None
        output_tokens = None
        status = "error"
        error_kind = None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
            
            status = "ok"
            self.log_metrics(self.model, latency_ms, input_tokens, output_tokens, status)
            return response.choices[0].message.content
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_kind = "exception"
            if "timeout" in str(e).lower():
                error_kind = "timeout"
            elif "rate limit" in str(e).lower():
                error_kind = "rate_limit"
            
            self.log_metrics(self.model, latency_ms, input_tokens, output_tokens, status, error_kind=error_kind)
            raise ProviderError(f"OpenAI generation failed: {e}")

    def get_name(self) -> str:
        return "openai"

class OpenRouterProvider(OpenAIProvider):
    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini"):
        super().__init__(api_key, model, base_url="https://openrouter.ai/api/v1")
        
    def get_name(self) -> str:
        return "openrouter"

class AzureProvider(OpenAIProvider):
    def __init__(self, api_key: str, endpoint: str, deployment_name: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        
        try:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-01",
                azure_endpoint=endpoint
            )
        except ImportError:
            raise ProviderError("openai package not installed. Run 'pip install openai'")

    def generate(self, prompt: str, **kwargs) -> str:
        start_time = time.time()
        input_tokens = None
        output_tokens = None
        status = "error"
        error_kind = None

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            latency_ms = int((time.time() - start_time) * 1000)

            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

            status = "ok"
            self.log_metrics(self.deployment_name, latency_ms, input_tokens, output_tokens, status)
            return response.choices[0].message.content
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_kind = "exception"
            if "timeout" in str(e).lower():
                error_kind = "timeout"
            
            self.log_metrics(self.deployment_name, latency_ms, input_tokens, output_tokens, status, error_kind=error_kind)
            raise ProviderError(f"Azure OpenAI generation failed: {e}")

    def get_name(self) -> str:
        return "azure"

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model_client = genai.GenerativeModel(model)
        except ImportError:
            raise ProviderError("google-generativeai package not installed. Run 'pip install google-generativeai'")

    def generate(self, prompt: str, **kwargs) -> str:
        start_time = time.time()
        input_tokens = None
        output_tokens = None
        status = "error"
        error_kind = None

        try:
            response = self.model_client.generate_content(
                prompt,
                generation_config={
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_output_tokens": kwargs.get("max_tokens", 4096),
                }
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Gemini usage metadata
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count

            status = "ok"
            self.log_metrics(self.model, latency_ms, input_tokens, output_tokens, status)
            return response.text
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_kind = "exception"
            if "timeout" in str(e).lower():
                error_kind = "timeout"
            
            self.log_metrics(self.model, latency_ms, input_tokens, output_tokens, status, error_kind=error_kind)
            raise ProviderError(f"Gemini generation failed: {e}")

    def get_name(self) -> str:
        return "gemini"

class ProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.metrics_enabled = True
        self.metrics_path = None
        self._initialize_from_env()

    def set_metrics_config(self, enabled: bool, path: Optional[str] = None):
        self.metrics_enabled = enabled
        self.metrics_path = path
        for provider in self.providers.values():
            provider.set_metrics_config(enabled, path)

    def _initialize_from_env(self):
        # OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            self.providers["openai"] = OpenAIProvider(
                os.environ["OPENAI_API_KEY"],
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            )
        
        # OpenRouter
        if os.environ.get("OPENROUTER_API_KEY"):
            self.providers["openrouter"] = OpenRouterProvider(
                os.environ["OPENROUTER_API_KEY"],
                model=os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
            )
            
        # Gemini
        if os.environ.get("GEMINI_API_KEY"):
            self.providers["gemini"] = GeminiProvider(
                os.environ["GEMINI_API_KEY"],
                model=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
            )
            
        # Azure (via openai_compat)
        if os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
            self.providers["azure"] = AzureProvider(
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            )

    def get_provider(self, name: str) -> LLMProvider:
        if name not in self.providers:
            # Fail-closed: raise error if provider not configured
            available = ", ".join(self.providers.keys()) if self.providers else "none"
            raise ProviderError(f"Provider '{name}' not found or not configured in environment. Available: {available}")
        return self.providers[name]

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {"name": name, "configured": True}
            for name in self.providers.keys()
        ]

# Global registry instance
registry = ProviderRegistry()
