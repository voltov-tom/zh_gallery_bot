"""Телеграм-бот zh-gallery.

Присылает случайную работу с сайта или работу по названию. Все запросы идут
в JSON-API сайта и подписаны заголовком X-Bot-Token — без него API отвечает 403.
"""

from __future__ import annotations

import html
import logging
import signal
from urllib.parse import quote

import requests
import telebot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import load_settings

settings = load_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("zh-gallery-bot")

bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML")

session = requests.Session()
session.headers.update({"X-Bot-Token": settings.api_token})
session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
    ),
)

CLIPBOARD = "\U0001f4cb"
HEART = "\U0001f497"
EYES = "\U0001f440"

CALLBACK_NOT_FOUND = "Не нашёл такую работу. Попробуй другое название или /stop."
CONTACT_MAX_LENGTH = 2000
CONTACT_PROMPT = "Напиши сообщение для Жени — я перешлю его на почту. Отмена — /stop."
CONTACT_SENT = "Спасибо! Сообщение отправлено."
CONTACT_TOO_LONG = f"Слишком длинно, максимум {CONTACT_MAX_LENGTH} символов."
CONTACT_RATE_LIMITED = "Слишком много сообщений подряд. Подожди минут десять."
CONTACT_FAILED = "Не получилось отправить сообщение, попробуй позже."
CALLBACK_ERROR = "Не получилось получить работу, попробуй ещё раз."
TITLE_PROMPT = "Напиши название работы, и я пришлю её. Если передумал — /stop."
ABOUT_TEXT = (
    "Я показываю работы с галереи zh-gallery.\n"
    "/random — случайная работа\n"
    "/image — работа по названию\n"
    "/contact — написать Жене (уйдёт на почту)\n"
    "/stop — прервать диалог"
)


class ApiError(Exception):
    """API вернуло ошибку или недоступно."""


class NotFound(ApiError):
    """Работы с таким названием нет."""


class RateLimited(ApiError):
    """Слишком много сообщений с одного аккаунта."""


def fetch_json(path: str) -> dict:
    """Запрос к API сайта. Ошибки — исключениями, чтобы их видно было в логах."""
    url = f"{settings.api_url}{path}"
    try:
        response = session.get(url, timeout=settings.request_timeout)
    except requests.RequestException as error:
        log.warning("API недоступно (%s): %s", url, error)
        raise ApiError from error

    if response.status_code == 404:
        raise NotFound
    if response.status_code != 200:
        log.warning("API вернуло %s (%s)", response.status_code, url)
        raise ApiError
    try:
        return response.json()
    except ValueError as error:
        log.warning("API вернуло не JSON (%s)", url)
        raise ApiError from error


def get_random_item() -> dict:
    return fetch_json("/api/telegram_bot/get_random_item/")


def get_item_by_title(title: str) -> dict:
    return fetch_json(f"/api/telegram_bot/get_media_item/{quote(title)}/")


def send_contact_message(text: str, telegram_id: int, username: str) -> None:
    """Отправляет сообщение «Напишите мне» в API сайта — оттуда оно уйдёт на почту."""
    url = f"{settings.api_url}/api/telegram_bot/send_message/"
    payload = {"text": text, "telegram_id": telegram_id, "username": username}
    try:
        response = session.post(url, json=payload, timeout=settings.request_timeout)
    except requests.RequestException as error:
        log.warning("API недоступно (%s): %s", url, error)
        raise ApiError from error

    if response.status_code == 429:
        raise RateLimited
    if response.status_code != 200:
        log.warning("API вернуло %s (%s)", response.status_code, url)
        raise ApiError


def format_caption(item: dict) -> str:
    """Подпись к фото. HTML — потому что в названиях бывают * и _."""
    title = html.escape(str(item.get("title") or "Без названия"))
    description = html.escape(str(item.get("description") or "").strip())
    likes = item.get("likes", 0)
    views = item.get("views", 0)

    lines = [f"<b>{title}</b>"]
    if description:
        lines.append(f"{CLIPBOARD} {description}")
    lines.append(f"{HEART} {likes}   {EYES} {views}")
    return "\n".join(lines)


def send_item(chat_id: int, item: dict) -> None:
    image_url = item.get("mediaItemUrl")
    if not image_url:
        raise ApiError
    bot.send_photo(chat_id, image_url, caption=format_caption(item))


@bot.message_handler(commands=["start", "help"])
def cmd_start(message: telebot.types.Message) -> None:
    bot.send_message(message.chat.id, ABOUT_TEXT)


@bot.message_handler(commands=["about"])
def cmd_about(message: telebot.types.Message) -> None:
    bot.send_message(message.chat.id, ABOUT_TEXT)


@bot.message_handler(commands=["stop", "cancel"])
def cmd_stop(message: telebot.types.Message) -> None:
    # именно так диалог действительно останавливается, а не «висит» дальше
    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.send_message(message.chat.id, "Хорошо, остановился.")


@bot.message_handler(commands=["random"])
def cmd_random(message: telebot.types.Message) -> None:
    try:
        send_item(message.chat.id, get_random_item())
    except ApiError:
        bot.send_message(message.chat.id, CALLBACK_ERROR)


def handle_title(message: telebot.types.Message) -> None:
    text = (message.text or "").strip()
    if text.lower() in {"stop", "/stop", "отмена"}:
        cmd_stop(message)
        return
    if not text:
        bot.send_message(message.chat.id, "Название пустое, напиши ещё раз или /stop.")
        bot.register_next_step_handler(message, handle_title)
        return

    try:
        send_item(message.chat.id, get_item_by_title(text))
    except NotFound:
        bot.send_message(message.chat.id, CALLBACK_NOT_FOUND)
        bot.register_next_step_handler(message, handle_title)
    except ApiError:
        bot.send_message(message.chat.id, CALLBACK_ERROR)


def handle_contact_message(message: telebot.types.Message) -> None:
    text = (message.text or "").strip()
    if text.lower() in {"stop", "/stop", "отмена"}:
        cmd_stop(message)
        return
    if not text:
        bot.send_message(message.chat.id, "Сообщение пустое, напиши ещё раз или /stop.")
        bot.register_next_step_handler(message, handle_contact_message)
        return
    if len(text) > CONTACT_MAX_LENGTH:
        bot.send_message(message.chat.id, CONTACT_TOO_LONG)
        bot.register_next_step_handler(message, handle_contact_message)
        return

    username = message.from_user.username or ""
    try:
        send_contact_message(text, message.from_user.id, username)
        bot.send_message(message.chat.id, CONTACT_SENT)
    except RateLimited:
        bot.send_message(message.chat.id, CONTACT_RATE_LIMITED)
    except ApiError:
        bot.send_message(message.chat.id, CONTACT_FAILED)


@bot.message_handler(commands=["contact"])
def cmd_contact(message: telebot.types.Message) -> None:
    prompt = bot.send_message(message.chat.id, CONTACT_PROMPT)
    bot.register_next_step_handler(prompt, handle_contact_message)


@bot.message_handler(commands=["image"])
def cmd_image(message: telebot.types.Message) -> None:
    prompt = bot.send_message(message.chat.id, TITLE_PROMPT)
    bot.register_next_step_handler(prompt, handle_title)


@bot.message_handler(content_types=["text"])
def cmd_unknown(message: telebot.types.Message) -> None:
    bot.send_message(message.chat.id, ABOUT_TEXT)


def _stop_on_signal(signum, _frame) -> None:
    """Docker шлёт SIGTERM при перезапуске — выходим из polling штатно."""
    log.info("Получен сигнал %s — останавливаем бота", signum)
    bot.stop_polling()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _stop_on_signal)
    log.info("Бот запускается, API: %s", settings.api_url)
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=20, allowed_updates=["message"])
    except (KeyboardInterrupt, SystemExit):
        log.info("Остановлен вручную")
    except Exception:
        log.exception("Неожиданная ошибка, бот упал")
        raise
