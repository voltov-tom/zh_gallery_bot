"""Конфигурация бота из переменных окружения (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_URL = "https://zh-gallery.ru"


@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_url: str
    api_token: str
    request_timeout: float = 10.0


def load_settings() -> Settings:
    bot_token = os.getenv("ZH_GALLERY_BOT_API_KEY", "").strip()
    api_token = os.getenv("ZH_GALLERY_API_TOKEN", "").strip()
    api_url = os.getenv("ZH_GALLERY_API_URL", DEFAULT_API_URL).strip().rstrip("/")

    if not bot_token:
        raise SystemExit(
            "Не задан ZH_GALLERY_BOT_API_KEY — токен от @BotFather (см. .env.example)."
        )
    if not api_token:
        raise SystemExit(
            "Не задан ZH_GALLERY_API_TOKEN — это TELEGRAM_BOT_TOKEN с сайта, бот шлёт его в X-Bot-Token."
        )
    return Settings(bot_token=bot_token, api_url=api_url, api_token=api_token)
