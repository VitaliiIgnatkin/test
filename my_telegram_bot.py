import logging
import sqlite3
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import requests

API_KEY = '6411432435:AAGIJb81llZH82Hp5Sgc1OxtCq01t6Qr1js'  
bot = Bot(token=API_KEY)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Инициализация SQLite базы данных
conn = sqlite3.connect("translations.db")
cursor = conn.cursor()

# Создание таблицы TranslationHistory, если её нет
cursor.execute("""
    CREATE TABLE IF NOT EXISTS TranslationHistory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        original_text TEXT,
        translated_text TEXT
    )
""")
conn.commit()

def translate_text(text):
    auth_key = '33320ddc-687f-ea17-c4af-539dbf1a4b46:fx'  
    url = 'https://api-free.deepl.com/v2/translate'
    params = {'target_lang': 'RU'}
    data = {'text': text}
    headers = {'Authorization': f'DeepL-Auth-Key {auth_key}'}
    
    response = requests.post(url, headers=headers, params=params, data=data).json()
    
    if 'translations' in response:
        translation = response['translations'][0]['text']
        return translation
    else:
        return 'Ошибка при переводе текста'

# Создайте клавиатуру с двумя кнопками: "Перевести" и "Моя история"
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
button_translate = KeyboardButton('Перевести')
button_history = KeyboardButton('Моя история')
button_other_history = KeyboardButton('История другого')
keyboard.add(button_translate, button_history, button_other_history)

@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    logging.info(f'Пользователь {message.from_user.username} начал взаимодействие с ботом')
    await message.reply(
        "Привет! Я бот-переводчик. Отправь мне текст на английском, и я переведу его на русский.",
        reply_markup=keyboard
    )

# Обработчик для кнопки "Моя история"
@dp.message_handler(lambda message: message.text.lower() == 'моя история')
async def request_history(message: types.Message):
    # Сохраняем chat_id пользователя, который запросил историю
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    cursor.execute("""
        SELECT original_text, translated_text
        FROM TranslationHistory
        WHERE user_id=?
    """, (user_id,))
    history = cursor.fetchall()

    if not history:
        await message.answer("У вас пока нет истории переводов.")
        return

    # Формируем текст для отправки пользователю
    history_text = "Ваша история переводов:\n"
    for original, translated in history:
        history_text += f"Оригинальный текст: {original}\nПереведенный текст: {translated}\n\n"

    # Отправляем историю пользователю
    await message.answer(history_text)

# Обработчик для кнопки "История другого"
@dp.message_handler(lambda message: message.text.lower() == 'история другого')
async def request_other_history(message: types.Message):
    await message.answer("Введите chat_id пользователя, чью историю переводов вы хотите посмотреть:")

# Обработчик для получения chat_id другого пользователя
@dp.message_handler(lambda message: message.text.isdigit())
async def get_chat_id(message: types.Message):
    chat_id = int(message.text)

    # Запрашиваем историю переводов по chat_id
    cursor.execute("""
        SELECT original_text, translated_text
        FROM TranslationHistory
        WHERE chat_id=?
    """, (chat_id,))
    history = cursor.fetchall()

    if not history:
        await message.answer("У данного пользователя пока нет истории переводов.")
        return

    # Формируем текст для отправки пользователю
    history_text = f"История переводов пользователя с chat_id {chat_id}:\n"
    for original, translated in history:
        history_text += f"Оригинальный текст: {original}\nПереведенный текст: {translated}\n\n"

    # Отправляем историю пользователю
    await message.answer(history_text)

@dp.message_handler()
async def translate_message(message: types.Message):
    text_to_translate = message.text
    translation = translate_text(text_to_translate)

    # Запись перевода в базу данных
    user_id = message.from_user.id
    chat_id = message.chat.id
    cursor.execute("""
        INSERT INTO TranslationHistory (user_id, chat_id, original_text, translated_text)
        VALUES (?, ?, ?, ?)
    """, (user_id, chat_id, text_to_translate, translation))
    conn.commit()

    # Отправляем перевод в новом сообщении
    await message.answer(f"Перевод:\n{translation}")

    # Отправляем новое сообщение для ввода следующего текста
    await message.answer("Отправьте мне текст, и я его переведу.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
