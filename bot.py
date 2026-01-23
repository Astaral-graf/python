# bot.py - Telegram бот с RAR файлом для Railway
# requirements.txt: pyTelegramBotAPI==4.14.0

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import logging

# Настройка логов
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен из Railway Variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден! Добавь в Railway Variables.")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Фиксированный ключ
KEY = "wZyeex3lBXA4H77KP5vM"

# Путь к RAR файлу
DPI_FILE = 'DPI Breaker.rar'

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Выдать подписку", callback_data="get_sub"))
    
    bot.send_message(
        message.chat.id,
        "🎉 **Вы получили семидневную бесплатную подписку на DPI Breaker!**\n\n"
        "DPI Breaker обходит блокировки Роскомнадзора и DPI для доступа к заблокированным сайтам.\n\n"
        "Нажмите кнопку ниже для активации:",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == "get_sub":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📥 Получить файл и ключ", callback_data="download"))
        
        bot.edit_message_text(
            "✅ **Подписка активирована!**\n\n"
            "Скачайте DPI Breaker и используйте ключ для активации.\n\n"
            "⏰ Ключ действителен **7 дней** с момента активации.",
            chat_id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    elif call.data == "download":
        if not os.path.exists(DPI_FILE):
            bot.send_message(chat_id, "❌ Файл не найден. Обратитесь к администратору.")
            logger.error(f"Файл {DPI_FILE} не найден!")
            return
        
        try:
            with open(DPI_FILE, 'rb') as file:
                bot.send_document(
                    chat_id,
                    file,
                    caption=f"📥 **DPI Breaker.rar**\n\n"
                           f"🔑 **Ваш ключ активации:**\n`{KEY}`\n\n"
                           f"**Инструкция:**\n"
                           f"1. Распакуйте RAR-архив (WinRAR/7-Zip)\n"
                           f"2. Запустите start(general).bat\n"
                           f"3. Введите ключ\n"
                           f"4. Наслаждайтесь 7 днями без блокировок!\n\n"
                           f"⚠️ Закройте антивирус на время установки.\n"
                           f"💬 Поддержка: @your_support",
                    parse_mode='Markdown'
                )
            
            # Удаляем предыдущее сообщение
            bot.delete_message(chat_id, call.message.message_id)
            logger.info(f"RAR файл отправлен пользователю {call.from_user.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки файла: {e}")
            bot.send_message(chat_id, "❌ Ошибка отправки. Попробуйте позже.")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "Используйте команду /start для запуска бота.")

if __name__ == '__main__':
    logger.info("🚀 DPI Breaker Bot запущен!")
    logger.info(f"RAR файл найден: {os.path.exists(DPI_FILE)}")
    logger.info(f"Ключ: {KEY}")
    
    bot.infinity_polling(none_stop=True, interval=1, timeout=30)


