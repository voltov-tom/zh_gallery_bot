# zh-gallery bot

Телеграм-бот, который показывает работы с [zh-gallery](https://zh-gallery.ru).

## Команды

| Команда | Что делает |
|---|---|
| `/random` | случайная работа |
| `/image` | работа по названию (диалог, выход — `/stop`) |
| `/about`, `/start`, `/help` | что умеет |
| `/stop` | прервать диалог |

## Установка

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # и заполнить
python main.py
```

## Переменные окружения

| Переменная | Зачем |
|---|---|
| `ZH_GALLERY_BOT_API_KEY` | токен бота от [@BotFather](https://t.me/BotFather) |
| `ZH_GALLERY_API_URL` | адрес сайта, по умолчанию `https://zh-gallery.ru` |
| `ZH_GALLERY_API_TOKEN` | `TELEGRAM_BOT_TOKEN` с сайта: бот шлёт его в заголовке `X-Bot-Token` |

Без `ZH_GALLERY_API_TOKEN` API сайта отвечает 403 — это защита от накрутки
просмотров, поэтому токен обязателен.

## Проверка без Телеграма

```bash
ZH_GALLERY_BOT_API_KEY=dummy ZH_GALLERY_API_URL=http://localhost:8080 \
ZH_GALLERY_API_TOKEN=<токен с сайта> \
python -c "from main import get_random_item, format_caption; print(format_caption(get_random_item()))"
```
