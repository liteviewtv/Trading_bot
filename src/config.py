"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_paper: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        key = os.getenv("ALPACA_API_KEY", "").strip()
        secret = os.getenv("ALPACA_SECRET_KEY", "").strip()
        paper = os.getenv("ALPACA_PAPER", "true").strip().lower() == "true"

        if not key or not secret:
            raise RuntimeError(
                "Missing ALPACA_API_KEY or ALPACA_SECRET_KEY. "
                "Copy .env.example to .env and add Alpaca paper-trading credentials."
            )
        if not paper:
            raise RuntimeError("Live trading is disabled in Phase 1. Set ALPACA_PAPER=true.")

        return cls(key, secret, paper)
