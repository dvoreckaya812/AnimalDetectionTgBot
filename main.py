import base64
import threading
import time
from multiprocessing.pool import ThreadPool
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, InputMediaVideo
from telebot.apihelper import ApiTelegramException
import requests
import json
from config import BOT_KEY, HOST, NAMES, SUPPORTED_IMAGE_EXT, SUPPORTED_VIDEO_EXT


bot = TeleBot(BOT_KEY)
IMAGE_COMMANDS = ['📷 Распознавание на изображениях', 'Распознавание на изображениях']
VIDEO_COMMANDS = ['🎥 Распознавание на видео', 'Распознавание на видео']
INFO_COMMANDS = ['❓ Справка', 'Справка', 'Инфо']


def update_loading(message):
    try:
        while True:
            time.sleep(1)
            message = bot.edit_message_text("⌛ Обработка может занять некоторое время", message.chat.id, message.id)
            time.sleep(1)
            message = bot.edit_message_text("⏳ Обработка может занять некоторое время.", message.chat.id, message.id)
            time.sleep(1)
            message = bot.edit_message_text("⌛ Обработка может занять некоторое время..", message.chat.id, message.id)
            time.sleep(1)
            message = bot.edit_message_text("⏳ Обработка может занять некоторое время...", message.chat.id, message.id)
    except ApiTelegramException:
        pass


def get_animals(data):
    if len(data) == 0:
        return "<pre>Животных не обнаружено</pre>"
    animals = ""
    for c in data:
        animals += "<b>" + NAMES[c] + "</b>, "
    animals = animals[:-2]
    return animals


def get_file(file):
    file_info = bot.get_file(file)
    downloaded_file = bot.download_file(file_info.file_path)
    return downloaded_file


def _image_handler(image):
    response = requests.post(HOST + "/image-animal-detection", data=image,
                            headers={'content-type': 'image/jpeg'})
    json_data = json.loads(response.text)
    animals = get_animals(json_data['classes'])
    image = base64.b64decode(json_data['media'])
    return animals, image


def _video_handler(video):
    response = requests.post(HOST + "/video-animal-detection", data=video,
                             headers={'content-type': 'video/mp4'})
    json_data = json.loads(response.text)
    animals = get_animals(json_data['classes'])
    video = base64.b64decode(json_data['media'])
    return animals, video


def get_menu():
    menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, input_field_placeholder='Загрузите медиафайл...')
    menu.add(KeyboardButton("📷 Распознавание на изображениях"), KeyboardButton("🎥 Распознавание на видео"))
    menu.add("❓ Справка", row_width=2)
    return menu


@bot.message_handler(commands=['start'])
def start_bot_handler(message):
    menu = get_menu()
    text = "🖐🏻 <pre>Приветсвую я автономный искусственный интеллект.</pre>\n" \
           "🛡️ <b>Моей задачей является помощь людям.</b>\n" \
           "☀️ <i>На данный момент я умею оптимизировать задачу искать и идентифицировать животных на видео" \
           "и изображениях.</i>"
    bot.send_message(message.chat.id, text, reply_markup=menu, parse_mode='HTML')


@bot.message_handler(content_types=['photo'])
def image_handler(message):
    file = message.photo[len(message.photo) - 1].file_id
    downloaded_file = get_file(file)
    animals, image = _image_handler(downloaded_file)
    bot.send_photo(message.chat.id, image,
                   "На изображении найдены следующие животные: {}".format(animals), parse_mode='HTML')


@bot.message_handler(content_types=['video'])
def video_handler(message):
    msg = bot.send_message(message.chat.id, "⏳ Обработка может занять некоторое время.", parse_mode='HTML')
    update_thread = threading.Thread(target=update_loading, args=(msg,))
    update_thread.start()
    downloaded_file = get_file(message.video.file_id)
    animals, video = _video_handler(downloaded_file)
    update_thread.join(0)

    bot.delete_message(msg.chat.id, msg.id)
    bot.send_video(message.chat.id, video,
                   caption="На видео найдены следующие животные: {}".format(animals), parse_mode='HTML')


@bot.message_handler(content_types=['document'])
def document_handler(message):
    file_info = bot.get_file(message.document.file_id)
    file_ext = file_info.file_path.split(".")[1]
    downloaded_file = bot.download_file(file_info.file_path)
    if file_ext in SUPPORTED_VIDEO_EXT:
        animals, video = _video_handler(downloaded_file)
        bot.send_video(message.chat.id, video,
                       caption="На видео найдены следующие животные: {}".format(animals), parse_mode='HTML')
    elif file_ext in SUPPORTED_IMAGE_EXT:
        animals, image = _image_handler(downloaded_file)
        bot.send_photo(message.chat.id, image,
                       "На изображении найдены следующие животные: {}".format(animals), parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "<pre>Данный тип документа не поддерживается</pre>", parse_mode='HTML')


@bot.message_handler(func=lambda m: True if m.text in IMAGE_COMMANDS else False)
def image_detection_info(message):
    text = "Для дальнейшей работы отправьте изображение в чат.\n\n" \
           "<b>Размер изображения не должен превышать 20/40* Мб</b>" \
           "<i>(ограничение Telegram)</i>\n\n" \
           "<i>*с подпиской Telegram Premium</i>"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: True if m.text in VIDEO_COMMANDS else False)
def video_detection_info(message):
    text = "Для дальнейшей работы отправьте видео в чат.\n\n" \
           "<b>Размер видеофайла не должен превышать 20/40* Мб</b>" \
           "<i>(ограничение Telegram)</i>\n\n" \
           "<i>*с подпиской Telegram Premium</i>"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: True if m.text in INFO_COMMANDS else False)
def info(message):
    text = "<pre>Данный чат-бот является частью программного комплекса по распознаванию животных.</pre>\n\n" \
           "🌐 <b>Сайт: http://127.0.0.1:5001/</b>\n\n" \
           "💬 <b>ПО разработано на технологический базе ФГБОУ ВО 'БГИТУ'.</b>"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(content_types=['text'])
def all_text_handler(message):
    text = "<pre>Хоть я и являюсь автономным искусственным интеллектом предугадать " \
           "и выполнить любое ваше действие я не могу.</pre>\n\n" \
           "<b>Воспользуйтесь либо встроенным меню, либо просто загрузите медиа-файл.</b>"
    menu = get_menu()
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=menu)


bot.infinity_polling()
