import os

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_POLARIZATION_MODEL = "gemini-2.5-flash"

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
        return None if self._is_local else os.getenv("GEMINI_API_KEY")

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
