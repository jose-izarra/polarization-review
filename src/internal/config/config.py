import os

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_POLARIZATION_MODEL = "gemini-3.1-flash-lite-preview"


class Config:
    @property
    def env(self) -> str:
        return os.getenv("ENV", "local")

    @property
    def _is_local(self) -> bool:
        return self.env == "local"

    # LLM
    @property
    def gemini_api_key(self) -> str | None:
        return os.getenv("GEMINI_API_KEY")

    @property
    def openai_api_key(self) -> str | None:
        return os.getenv("OPENAI_API_KEY")

    @property
    def qwen_api_key(self) -> str | None:
        return os.getenv("QWEN_API_KEY")

    @property
    def qwen_base_url(self) -> str:
        # International (non-China) accounts use the -intl subdomain.
        # Override with QWEN_BASE_URL if needed.
        return os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )

    @property
    def mistral_api_key(self) -> str | None:
        return os.getenv("MISTRAL_API_KEY")

    @property
    def deepseek_api_key(self) -> str | None:
        return os.getenv("DEEPSEEK_API_KEY")

    @property
    def ollama_host(self) -> str:
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    @property
    def polarization_model(self) -> str:
        return os.getenv("POLARIZATION_MODEL", _DEFAULT_POLARIZATION_MODEL)

    # Scrapers
    @property
    def reddit_client_id(self) -> str | None:
        return None if self._is_local else os.getenv("REDDIT_CLIENT_ID")

    @property
    def reddit_client_secret(self) -> str | None:
        return None if self._is_local else os.getenv("REDDIT_CLIENT_SECRET")

    @property
    def reddit_user_agent(self) -> str:
        return os.getenv("REDDIT_USER_AGENT")

    @property
    def youtube_api_key(self) -> str | None:
        return None if self._is_local else os.getenv("YOUTUBE_API_KEY")

    @property
    def gnews_api_key(self) -> str | None:
        return None if self._is_local else os.getenv("GNEWS_API_KEY")


config = Config()
