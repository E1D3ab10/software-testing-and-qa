"""Runtime configuration, independent of test data and HTTP transport."""
import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    base_url: str
    timeout: float

    @classmethod
    def from_env(cls):
        url = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")
        if urlparse(url).scheme not in {"http", "https"} or not urlparse(url).netloc:
            raise ValueError("BASE_URL must be an absolute HTTP(S) URL")
        timeout = float(os.getenv("API_TIMEOUT", "10"))
        if timeout <= 0:
            raise ValueError("API_TIMEOUT must be positive")
        return cls(url, timeout)
