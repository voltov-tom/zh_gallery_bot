import requests
import telebot
from config import ZH_GALLERY_BOT_API_KEY

API_KEY = ZH_GALLERY_BOT_API_KEY
bot = telebot.TeleBot(API_KEY)

clipboard = u'\U0001F4CB'
heart = u'\U0001F497'
eyes = u'\U0001F440'


@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(message.chat.id, 'Стою...')


@bot.message_handler(commands=['about'])
def about(message):
    bot.send_message(
        message.chat.id,
        'Пока я умею только показывать картинки с zh-gallery.ru, но я учусь...'
    )


@bot.message_handler(commands=['image'])
def cmd_get_image(message):
    send = bot.send_message(
        message.chat.id, 'Дай мне название картинки с zh-gallery.ru и я пришлю её тебе напиши "stop" для остановки'
    )
    bot.register_next_step_handler(send, get_image_from_api)


@bot.message_handler(commands=['random'])
def random_from_api(message):
    if str.lower(message.text) == '/stop':
        stop(message)
        return
    try:
        request = requests.get(f'https://zh-gallery.ru/api/telegram_bot/get_random_item')
        # request = requests.get(f'http://localhost:8000/api/telegram_bot/get_random_item')
        response = request.json()
        media_item_url = response.get('mediaItemUrl')
        title = response.get('title')
        description = response.get('description')
        likes = response.get('likes')
        views = response.get('views')
        text = f'*{title}*\n{clipboard}{description}\n{heart} {likes} {eyes} {views}'
        bot.send_photo(message.chat.id, media_item_url, caption=text, parse_mode='Markdown')

    except Exception as error:
        print(error)
        send = bot.send_message(message.chat.id, 'Что-то пошло не так, попробуй еще раз...')
        bot.register_next_step_handler(send, random_from_api)


def get_image_from_api(message):
    if str.lower(message.text) == '/stop':
        stop(message)
        return
    try:
        request = requests.get(f'http://zh-gallery.ru/api/telegram_bot/get_media_item/{message.text}')
        # request = requests.get(f'http://localhost:8000/api/telegram_bot/get_media_item/{message.text}')

        if request.status_code == 404:
            send = bot.send_message(message.chat.id, 'Не найдено, попробуй еще раз...')
            bot.register_next_step_handler(send, get_image_from_api)
        else:
            response = request.json()
            media_item_url = response.get('mediaItemUrl')
            title = response.get('title')
            description = response.get('description')
            likes = response.get('likes')
            views = response.get('views')
            text = f'*{title}*\n{clipboard}{description}\n{heart} {likes} {eyes} {views}'
            bot.send_photo(message.chat.id, media_item_url, caption=text, parse_mode='Markdown')

    except Exception as error:
        print(error)
        send = bot.send_message(message.chat.id, 'Что-то пошло не так, попробуй еще раз...')
        bot.register_next_step_handler(send, get_image_from_api)


@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(message.chat.id, 'Стою...')


@bot.message_handler(content_types=['text'])
def text(message):
    about(message)


if __name__ == "__main__":
    try:
        bot.infinity_polling(interval=0, timeout=20, allowed_updates=['util.update_types'])
    except (KeyboardInterrupt, SystemExit):
        print("KeyboardInterrupt or exit(), goodbye!")
    except Exception as e:
        print(f"Uncaught exception: {e}")
