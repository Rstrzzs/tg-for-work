import json
from utils import download_voice, download_photo
import telebot
import sqlite3
from telebot import types
import random
import requests

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS zakazchiki (
                        id INTEGER PRIMARY KEY,
                        telegram_id INTEGER,
                        name TEXT,
                        type_of_work TEXT,
                        deadlines TEXT,
                        price TEXT,
                        telegram_name TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                           id INTEGER PRIMARY KEY,
                           telegram_id INTEGER UNIQUE,
                           name TEXT,
                           age INTEGER,
                           gender TEXT,
                           interests TEXT,
                           telegram_name TEXT UNIQUE
                       )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS all_users (
                           id INTEGER PRIMARY KEY,
                           telegram_id INTEGER UNIQUE
                       )''')
    conn.commit()
    conn.close()
# Добавление пользователя в базу данных
def add_zakaz(telegram_id, name, age, gender, interests,telegram_name):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO zakazchiki (telegram_id, name, type_of_work, deadlines, price, telegram_name)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (telegram_id, name, age, gender, interests, telegram_name))
    conn.commit()
    conn.close()

def add_worker(telegram_id, name, age, gender, interests, telegram_name):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO users (telegram_id, name, age, gender, interests, telegram_name)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (telegram_id, name, age, gender, interests, telegram_name))
    conn.commit()
    conn.close()
def db_table_val(telegram_id):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO all_users (telegram_id)
                          VALUES (?)''',
                   (telegram_id,))
    conn.commit()
    conn.close()

# Поиск анкет других пользователей
def get_random_profile(telegram_name):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT id, telegram_id, name, age, gender, interests, telegram_name FROM users WHERE telegram_name != ?''', (telegram_name,))
    results = cursor.fetchall()
    conn.close()
    if results:
        return random.choice(results)
    return None

def get_random_work(telegram_name):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT id, telegram_id, name, type_of_work, deadlines, price, telegram_name FROM zakazchiki WHERE telegram_name != ?''', (telegram_name,))
    results = cursor.fetchall()
    conn.close()
    if results:
        return random.choice(results)
    return None
# Получение всех профилей из базы данных
def count_all_records(table_name):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute(f'''SELECT COUNT(*) FROM {table_name}''')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Инициализация бота
TOKEN = 'API_KEY'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True, content_types=['photo'])
def handle_photo(message):
    print(message)
    download_photo(message, bot,1)
    bot.reply_to(message, "Поймал фото")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    telegram_id = message.from_user.id

    query = f"SELECT 1 FROM all_users WHERE telegram_id = ? LIMIT 1"
    cursor.execute(query, (telegram_id,))

    result = cursor.fetchone()
    print(result)

    if (result == None):

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заказчик")
        markup.add("Работник")
        bot.send_message(message.chat.id, 'Привет, добро пожаловать в бота по поиску работы. Вы заказчик или работник?',
                     reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Поиск работы")
        markup.add("Поиск исполнителя")
        markup.add("Создать заказ")
        bot.send_message(message.chat.id, 'Привет! Удачных поисков.',
                         reply_markup=markup)
@bot.message_handler(regexp='Заказчик')
def profile(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id,
                     "Пожалуйста, введите данные заказчика по форме: Имя/Компания; Тип работы; Сроки; Оплата работы\n",
                     reply_markup=markup)
    bot.register_next_step_handler(message, save_profile_zakaz)
@bot.message_handler(regexp='Создать заказ')
def profile(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id,
                     "Пожалуйста, введите данные заказчика по форме: Имя/Компания; Тип работы; Сроки; Оплата работы\n",
                     reply_markup=markup)
    bot.register_next_step_handler(message, save_profile_zakaz)
@bot.message_handler(regexp='Работник')
def profile(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id,
                     "Пожалуйста, введите данные работника по форме: Имя; Возраст; Пол; Интересы/возможности\n",
                     reply_markup=markup)
    bot.register_next_step_handler(message, save_profile_worker)
# Обработка введённых данных профиля


def save_profile_zakaz(message):
    user_data = message.text.split('; ')
    if len(user_data) == 4:
        name, type_of_work, deadlines, price = user_data
        try:
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Меню")
            telegram_id = message.from_user.id
            telegram_name = message.from_user.username
            add_zakaz(telegram_id, name, type_of_work, deadlines, price, telegram_name)
            bot.send_message(message.chat.id, "Ваш профиль сохранён!",reply_markup=markup)
            db_table_val(telegram_id)

            bot.register_next_step_handler(message, main_menu)
        except ValueError:
            bot.send_message(message.chat.id, " ")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заказчик")
        markup.add("Работник")
        bot.send_message(message.chat.id, "Неверный формат. Попробуйте ещё раз.", reply_markup=markup)
def save_profile_worker(message):
    user_data = message.text.split('; ')
    if len(user_data) == 4:
        name, type_of_work, deadlines, price = user_data
        try:
            telegram_id = message.from_user.id
            telegram_name = message.from_user.username
            add_worker(telegram_id, name, type_of_work, deadlines, price,telegram_name)
            bot.send_message(message.chat.id, "Ваш профиль сохранён!")
            db_table_val(telegram_id)
            bot.send_message(message.chat.id, "Пришлите фото профиля. Строго в формате .png")
            bot.register_next_step_handler(message, save_profile_photo)
        except ValueError:
            bot.send_message(message.chat.id, " ")
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заказчик")
        markup.add("Работник")
        bot.send_message(message.chat.id, "Неверный формат. Попробуйте ещё раз.", reply_markup=markup)

def save_profile_photo(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Меню")
    total_users = count_all_records('users')
    download_photo(message, bot, total_users)
    bot.send_message(message.chat.id, "Фото добавлено!", reply_markup=markup)
def main_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Поиск работы")
    markup.add("Поиск исполнителя")
    markup.add("Создать заказ")
    bot.send_message(message.chat.id, 'Привет! Удачных поисков.',
                     reply_markup=markup)

@bot.message_handler(regexp='Меню')
def profile(message):
    main_menu(message)

#обработчик search рабочтитичякой
@bot.message_handler(regexp='Поиск исполнителя')
def search(message):
    telegram_name = message.from_user.username
    profile = get_random_profile(telegram_name)

    if profile:
        profile_id,telegram_id, name, age, gender, interests, telegram_name = profile

        response = (f"Вот случайная анкета:\n\n"
                    f"Имя: {name}\n"
                    f"Возраст: {age}\n"
                    f"Пол: {gender}\n"
                    f"Интересы/возможности: {interests}")

        # Добавление инлайн-кнопок для лайка и дизлайка
        markup = types.InlineKeyboardMarkup()
        like_button = types.InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{telegram_name}_{telegram_id}")
        dislike_button = types.InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{telegram_name}")
        markup.add(like_button, dislike_button)
        #print(profile_id)
        with open(f"users_image/{profile_id}.png",'rb') as photo:
            bot.send_photo(message.chat.id,photo,caption=response,reply_markup=markup,parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "К сожалению, пока нет доступных анкет.")

# Обработка нажатий на кнопки лайка и дизлайка
@bot.callback_query_handler(func=lambda call: call.data.startswith("like_"))
def handle_like(call):
    data_parts = call.data.split("_")  # Разбиваем строку на части
    telegram_name = data_parts[1]
    tg_id = data_parts[2]
    print(data_parts)
    bot.send_message(call.message.chat.id, f"Вы поставили лайк! Telegram ID анкеты: @{telegram_name}")
    bot.send_message(tg_id, f"Вам поставили лайк. Telegram ID анкеты: @{call.message.chat.username}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("dislike_"))
def handle_dislike(call):
    disliked_profile = call.data.split("_")[1]
    bot.delete_message(call.message.chat.id, call.message.message_id)  # Удаление предыдущей анкеты
    telegram_name = call.message.chat.username

    while True:
        profile = get_random_profile(telegram_name)
        if not profile or profile[5] != disliked_profile:
            break

    if profile:
        profile_id,telegram_id, name, age, gender, interests, telegram_name = profile
        response = (f"Вот следующая анкета:\n\n"
                    f"Имя: {name}\n"
                    f"Возраст: {age}\n"
                    f"Пол: {gender}\n"
                    f"Интересы: {interests}")

        # Добавление инлайн-кнопок для лайка и дизлайка
        markup = types.InlineKeyboardMarkup()
        like_button = types.InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{telegram_name}_{telegram_id}")
        dislike_button = types.InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{telegram_name}")
        markup.add(like_button, dislike_button)

        with open(f"users_image/{profile_id}.png", 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo, caption=response, reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "К сожалению, больше нет доступных анкет.")


#обработчик search working
@bot.message_handler(regexp='Поиск работы')
def search(message):
    telegram_name = message.from_user.username
    profile = get_random_work(telegram_name)

    if profile:
        profile_id,telegram_id, name, age, gender, interests, telegram_name = profile
        response = (f"Вот случайная анкета:\n\n"
                    f"Имя: {name}\n"
                    f"Тип работы: {age}\n"
                    f"Сроки: {gender}\n"
                    f"Оплата: {interests}")

        # Добавление инлайн-кнопок для лайка и дизлайка
        markup = types.InlineKeyboardMarkup()
        like_button = types.InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{telegram_name}_{telegram_id}")
        dislike_button = types.InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"govno_{telegram_name}")
        markup.add(like_button, dislike_button)

        bot.send_message(message.chat.id, response, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "К сожалению, пока нет доступных анкет.")

# Обработка нажатий на кнопки лайка и дизлайка
@bot.callback_query_handler(func=lambda call: call.data.startswith("like_"))
def handle_like(call):

    print(1, call.data.split("_"))
    profile_id = call.data.split("_")[1]
    name = call.data.split("_"[2])
    bot.send_message(call.message.chat.id, f"Вы поставили лайк! Telegram ID анкеты: @{profile_id}")
    bot.send_message(name, f"Вам поставили лайк. Telegram ID анкеты: @{call.message.chat.username}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("govno_"))
def handle_dislike(call):
    disliked_profile = call.data.split("_")[1]
    bot.delete_message(call.message.chat.id, call.message.message_id)  # Удаление предыдущей анкеты
    telegram_name = call.message.chat.username
    profile = get_random_work(telegram_name)

    if profile:
        profile_id, telegram_id, name, age, gender, interests, telegram_name = profile
        response = (f"Вот следующая анкета:\n\n"
                    f"Имя: {name}\n"
                    f"Возраст: {age}\n"
                    f"Пол: {gender}\n"
                    f"Интересы: {interests}")

        # Добавление инлайн-кнопок для лайка и дизлайка
        markup = types.InlineKeyboardMarkup()
        like_button = types.InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{telegram_name}_{telegram_id}")
        dislike_button = types.InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"govno_{telegram_name}")
        markup.add(like_button, dislike_button)

        bot.send_message(call.message.chat.id, response, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "К сожалению, больше нет доступных анкет.")

# Основной код
if __name__ == '__main__':
    # Инициализация базы данных
    init_db()

    # Запуск бота
    bot.polling(none_stop=True)
