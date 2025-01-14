import sqlite3
from datetime import datetime, time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import nest_asyncio  # Импортируем nest_asyncio

# Активируем nest_asyncio
nest_asyncio.apply()

# Настройки базы данных
DB_NAME = 'birthday_bot.db'

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для поздравлений с днём рождения.")

# Команда /add - добавление пользователя
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем аргументы команды
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Используйте: /add Имя Фамилия День_рождения (YYYY-MM-DD) [Текст поздравления]")
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
        await update.message.reply_text(f"Пользователь {first_name} {last_name} добавлен!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Команда /delete - удаление пользователя
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("Используйте: /delete ID_пользователя")
            return

        user_id = args[0]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Пользователь с ID {user_id} удалён.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Команда /edit - редактирование данных пользователя
async def edit_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text("Используйте: /edit ID_пользователя Имя Фамилия День_рождения (YYYY-MM-DD)")
            return

        user_id, first_name, last_name, birthday = args[0], args[1], args[2], args[3]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET first_name = ?, last_name = ?, birthday = ? WHERE id = ?",
            (first_name, last_name, birthday, user_id)
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Данные пользователя с ID {user_id} обновлены.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Команда /upload - загрузка открытки
async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("Используйте: /upload ID_пользователя")
            return

        user_id = args[0]
        if not update.message.photo:
            await update.message.reply_text("Пожалуйста, отправьте фото.")
            return

        # Получаем file_id последнего фото
        photo_file_id = update.message.photo[-1].file_id

        # Сохраняем file_id в базу данных
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET photo_file_id = ? WHERE id = ?", (photo_file_id, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Открытка для пользователя с ID {user_id} загружена.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Команда /settext - установка текста поздравления
async def set_congratulation_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Используйте: /settext ID_пользователя Текст поздравления")
            return

        user_id = args[0]
        congratulation_text = " ".join(args[1:])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET congratulation_text = ? WHERE id = ?", (congratulation_text, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Текст поздравления для пользователя с ID {user_id} обновлён.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Команда /list - список пользователей
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()

    if not users:
        await update.message.reply_text("Список пользователей пуст.")
        return

    user_list = "\n".join([f"ID: {user['id']}, Имя: {user['first_name']} {user['last_name']}, ДР: {user['birthday']}" for user in users])
    await update.message.reply_text(f"Список пользователей:\n{user_list}")

# Команда /myid - показать ID пользователя
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(f"Ваш ID: {user_id}")

# Проверка дней рождения
async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):
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
            await context.bot.send_photo(chat_id=CHAT_ID, photo=user['photo_file_id'], caption=message)
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text=message)

# Основная функция
async def main():
    # Токен вашего бота
    TOKEN = '7738581806:AAFWv74dqG48tEYcpgZRjnMGytNC9_VDF4I' 
    # ID группы, куда бот будет отправлять поздравления
    global CHAT_ID
    CHAT_ID = '156734752' 

    # Создаём приложение
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("delete", delete_user))
    application.add_handler(CommandHandler("edit", edit_user))
    application.add_handler(CommandHandler("upload", upload_photo))
    application.add_handler(CommandHandler("settext", set_congratulation_text))
    application.add_handler(CommandHandler("list", list_users))
    application.add_handler(CommandHandler("myid", my_id))
    application.add_handler(MessageHandler(filters.PHOTO, upload_photo))

    # Планировщик для проверки дней рождения
    job_queue = application.job_queue
    job_queue.run_daily(check_birthdays, time=time(hour=9, minute=0))  # Проверка в 9:00 утра

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    import asyncio

    # Запуск бота
    asyncio.run(main())