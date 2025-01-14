import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# Настройки базы данных
DB_NAME = 'birthday_bot.db'

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот для поздравлений с днём рождения.")

# Команда /add - добавление пользователя
def add_user(update: Update, context: CallbackContext):
    try:
        # Получаем аргументы команды
        args = context.args
        if len(args) < 3:
            update.message.reply_text("Используйте: /add Имя Фамилия День_рождения (YYYY-MM-DD) [Текст поздравления]")
            return

        first_name, last_name, birthday = args[0], args[1], args[2]
        congratulation_text = " ".join(args[3:]) if len(args) > 3 else None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (first_name, last_name, birthday, congratulation_text) VALUES (?, ?, ?, ?)",
            (first_name, last_name, birthday, congratulation_text)
        )
        conn.commit()
        conn.close()
        update.message.reply_text(f"Пользователь {first_name} {last_name} добавлен!")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {e}")

# Команда /upload - загрузка открытки
def upload_photo(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 1:
            update.message.reply_text("Используйте: /upload ID_пользователя")
            return

        user_id = args[0]
        if not update.message.photo:
            update.message.reply_text("Пожалуйста, отправьте фото.")
            return

        # Получаем file_id последнего фото
        photo_file_id = update.message.photo[-1].file_id

        # Сохраняем file_id в базу данных
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET photo_file_id = ? WHERE id = ?", (photo_file_id, user_id))
        conn.commit()
        conn.close()
        update.message.reply_text(f"Открытка для пользователя с ID {user_id} загружена.")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {e}")

# Команда /settext - установка текста поздравления
def set_congratulation_text(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 2:
            update.message.reply_text("Используйте: /settext ID_пользователя Текст поздравления")
            return

        user_id = args[0]
        congratulation_text = " ".join(args[1:])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET congratulation_text = ? WHERE id = ?", (congratulation_text, user_id))
        conn.commit()
        conn.close()
        update.message.reply_text(f"Текст поздравления для пользователя с ID {user_id} обновлён.")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {e}")

# Команда /list - список пользователей
def list_users(update: Update, context: CallbackContext):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()

    if not users:
        update.message.reply_text("Список пользователей пуст.")
        return

    user_list = "\n".join([f"ID: {user['id']}, Имя: {user['first_name']} {user['last_name']}, ДР: {user['birthday']}" for user in users])
    update.message.reply_text(f"Список пользователей:\n{user_list}")

# Команда /myid - показать ID пользователя
def my_id(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    update.message.reply_text(f"Ваш ID: {user_id}")

# Проверка дней рождения
def check_birthdays(context: CallbackContext):
    today = datetime.today().strftime('%m-%d')  # Текущий день и месяц
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE strftime('%m-%d', birthday) = ?", (today,))
    users = cursor.fetchall()
    conn.close()

    for user in users:
        # Используем кастомный текст, если он есть, иначе текст по умолчанию
        message = user['congratulation_text'] or f"🎉🎂 Поздравляем {user['first_name']} {user['last_name']} с днём рождения! 🎂🎉"
        if user['telegram_id']:
            message += f" @{user['telegram_id']}"

        # Если есть file_id открытки, отправляем её
        if user['photo_file_id']:
            context.bot.send_photo(chat_id=CHAT_ID, photo=user['photo_file_id'], caption=message)
        else:
            context.bot.send_message(chat_id=CHAT_ID, text=message)

# Основная функция
def main():
    # Токен вашего бота
    TOKEN = 'ВАШ_ТОКЕН'
    # ID группы, куда бот будет отправлять поздравления
    global CHAT_ID
    CHAT_ID = 'ID_ВАШЕЙ_ГРУППЫ'

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Регистрация команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("add", add_user))
    dispatcher.add_handler(CommandHandler("upload", upload_photo))
    dispatcher.add_handler(CommandHandler("settext", set_congratulation_text))
    dispatcher.add_handler(CommandHandler("list", list_users))
    dispatcher.add_handler(CommandHandler("myid", my_id))
    dispatcher.add_handler(MessageHandler(Filters.photo, upload_photo))

    # Планировщик для проверки дней рождения
    job_queue = updater.job_queue
    job_queue.run_daily(check_birthdays, time=datetime.time(hour=9, minute=0))  # Проверка в 9:00 утра

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()