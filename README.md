# zh-gallery bot

Телеграм-бот, который показывает работы с [zh-gallery](https://zh-gallery.ru).

## Команды

| Команда | Что делает |
|---|---|
| `/random` | случайная работа |
| `/image` | работа по названию (диалог, выход — `/stop`) |
| `/contact` | написать Жене: сообщение уходит на почту `zhenya@zh-gallery.ru` |
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

## «Напишите мне»

`/contact` — бот спрашивает текст, отправляет его в
`POST /api/telegram_bot/send_message/`, а сайт пересылает письмо на
`CONTACT_EMAIL` (по умолчанию `zhenya@zh-gallery.ru`). Ограничения: до 2000
символов и 3 сообщения с одного аккаунта за 10 минут — дальше бот отвечает
«слишком много сообщений».

## Проверка без Телеграма

```bash
ZH_GALLERY_BOT_API_KEY=dummy ZH_GALLERY_API_URL=http://localhost:8080 \
ZH_GALLERY_API_TOKEN=<токен с сайта> \
python -c "from main import get_random_item, format_caption; print(format_caption(get_random_item()))"
```

## Прод

Бот живёт на **NL** (`178.208.66.61`), а не рядом с сайтом: в РФ `api.telegram.org`
недоступен, с zh-gallery.ru соединение не устанавливается. Сайт и Telegram с NL
доступны, поэтому бот стоит там.

- образ: `ghcr.io/voltov-tom/zh-gallery-bot:<sha>` (публичный GHCR);
- стек: `deploy/bot/docker-compose.prod.yml` в репозитории сайта (бот и sidecar xray),
  портов наружу нет: Telegram в РФ недоступен, трафик бота идёт через VLESS на KZ;
- секреты: `.env` рядом с compose (`600`), в образ не попадают (см. `.dockerignore`);
- деплой: push в `refactor` → GitHub Actions собирает образ и заходит по SSH
  пользователем `deploybot`, у которого ключ ограничен forced-command
  (`status`, `logs`, `deploy <sha>`). Секрет репозитория: `BOT_DEPLOY_SSH_KEY`.

Локальная проверка контейнера:

```bash
docker build -t zh-bot:test .
docker run --rm --env-file .env zh-bot:test
```
