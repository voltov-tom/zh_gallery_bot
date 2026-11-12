# Образ бота: Python 3.12, запуск от непривилегированного пользователя.
# Наружу бот ничего не публикует — работает long polling и сам ходит к
# api.telegram.org и к API сайта.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py main.py ./

RUN useradd --create-home --uid 1000 bot
USER bot

CMD ["python", "main.py"]
