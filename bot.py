# bot.py - Улучшенный Telegram бот DPI Breaker для Railway
# requirements.txt:
# pyTelegramBotAPI==4.14.0
# python-dotenv==1.0.0  (опционально для локального теста)

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import os
import uuid
import json
import logging
from datetime import datetime, timedelta
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен из Railway Variables (обязательно добавь TELEGRAM_BOT_TOKEN)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден! Добавь в Railway Variables.")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Путь к файлу (exe или rar)
DPI_FILE = 'dpi_breaker.exe'  # Распакуй RAR и положи сюда

# База данных в JSON (для Railway добавь PostgreSQL для продакшена)
DB_FILE = 'users.json'
users = {}  # {user_id: {'key': str, 'expires': datetime, 'used': bool}}

def load_db():
    global users
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                users = json.load(f)
                # Конверт дат
                for uid, data in users.items():
                    users[uid]['expires'] = datetime.fromisoformat(data['expires'])
    except Exception as e:
        logger.error(f"Ошибка загрузки БД: {e}")

def save_db():
    try:
        data = {}
        for uid, uinfo in users.items():
            data[uid] = {
                'key': uinfo['key'],
                'expires': uinfo['expires'].isoformat(),
                'used': uinfo.get('used', False)
            }
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения БД: {e}")

load_db()

def generate_key():
    """Генерирует уникальный ключ XXX-XXX-XXX"""
    return f"{uuid.uuid4().hex[:3].upper()}-{uuid.uuid4().hex[4:7].upper()}-{uuid.uuid4().hex[8:11].upper()}"

def is_key_valid(user_id):
    """Проверяет валидность ключа"""
    if user_id not in users:
        return False
    expires = users[user_id]['expires']
    return datetime.now() < expires and not users[user_id].get('used', False)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    
    # Проверка подписки
    if user_id in users and is_key_valid(user_id):
        show_menu(chat_id, "✅ Ваша подписка активна!", user_id)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🎁 Получить 7-дневную подписку", callback_data="get_sub"))
    markup.add(InlineKeyboardButton("🔑 Проверить ключ", callback_data="check_key"))
    
    bot.send_message(
        chat_id,
        "🎉 **Добро пожаловать в DPI Breaker Bot!**\n\n"
        "DPI Breaker — инструмент для обхода DPI-блокировок (Роскомнадзор и т.д.).\n"
        "*Скорость до 1 Гбит/с, без VPN!*\n\n"
        "Нажмите кнопку для бесплатной 7-дневной подписки:",
        parse_mode='Markdown',
        reply_markup=markup,
        disable_web_page_preview=True
    )

def show_menu(chat_id, text, user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📥 Скачать DPI Breaker + ключ", callback_data="download"))
    markup.add(InlineKeyboardButton("📊 Мой ключ", callback_data="my_key"))
    markup.add(InlineKeyboardButton("ℹ️ Инструкция", callback_data="help"))
    
    bot.send_message(chat_id, f"{text}\n\nВыберите действие:", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id
    
    try:
        if call.data == "get_sub":
            # Выдача новой подписки
            key = generate_key()
            expires = datetime.now() + timedelta(days=7)
            users[user_id] = {'key': key, 'expires': expires, 'used': False}
            save_db()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📥 Скачать файл", callback_data="download"))
            
            bot.edit_message_text(
                f"✅ **Подписка выдана!**\n\n"
                f"🔑 **Ваш ключ:** `{key}`\n"
                f"⏰ **Истекает:** {expires.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Нажмите для скачивания:",
                chat_id, call.message.message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
            
        elif call.data == "download":
            if not os.path.exists(DPI_FILE):
                bot.send_message(chat_id, "❌ Файл не найден. Обратитесь к @admin.")
                return
            
            users[user_id]['used'] = True
            save_db()
            
            with open(DPI_FILE, 'rb') as f:
                bot.send_document(
                    chat_id,
                    f,
                    caption=f"📥 **DPI Breaker** (Windows exe)\n\n"
                           f"🔑 **Ключ:** `{users[user_id]['key']}`\n"
                           f"⏰ **До:** {users[user_id]['expires'].strftime('%d.%m.%Y')}\n\n"
                           f"**Инструкция:**\n"
                           f"1. Запустите exe\n"
                           f"2. Введите ключ\n"
                           f"3. Готово!\n\n"
                           f"⚠️ Закройте антивирус на время установки.\n"
                           f"📞 Поддержка: @your_support",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("🔄 Новая подписка", callback_data="get_sub")
                    )
                )
            
            bot.delete_message(chat_id, call.message.message_id)
            
        elif call.data == "check_key":
            if user_id in users and is_key_valid(user_id):
                bot.answer_callback_query(call.id, f"✅ Ключ `{users[user_id]['key']}` валиден до {users[user_id]['expires'].strftime('%d.%m.%Y')}")
                show_menu(chat_id, "✅ Ключ активен!", user_id)
            else:
                bot.answer_callback_query(call.id, "❌ Ключ недействителен или истёк")
                bot.edit_message_text("❌ Подписка не найдена. Получите новую!", chat_id, call.message.message_id)
                
        elif call.data == "my_key":
            if user_id in users:
                info = users[user_id]
                status = "✅ Активна" if is_key_valid(user_id) else "❌ Истёк"
                bot.edit_message_text(
                    f"🔑 **Ваш ключ:** `{info['key']}`\n"
                    f"⏰ **Истекает:** {info['expires'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"📊 **Статус:** {status}",
                    chat_id, call.message.message_id, parse_mode='Markdown'
                )
            else:
                bot.answer_callback_query(call.id, "❌ Нет подписки")
                
        elif call.data == "help":
            help_text = """
**Инструкция по DPI Breaker:**

1. Скачайте и запустите `dpi_breaker.exe`
2. Введите полученный ключ
3. Программа запустится автоматически
4. DPI-трафик будет обходить блокировки!

**Что это даёт:**
• Доступ к Telegram/VK/YouTube без VPN
• Скорость до 1 Гбит/с
• Работает с играми (CS/Valorant)

⚠️ *Антивирус может ругаться — добавьте в исключения.*
            """
            bot.edit_message_text(help_text, chat_id, call.message.message_id, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Ошибка в callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка. Попробуйте позже.")

# Graceful shutdown
def signal_handler(sig, frame):
    logger.info("Сохранение БД...")
    save_db()
    logger.info("Бот остановлен.")
    os._exit(0)

if __name__ == '__main__':
    logger.info("🚀 DPI Breaker Bot запущен!")
    logger.info(f"Файл доступен: {os.path.exists(DPI_FILE)}")
    
    # Обработка сигналов (Railway restarts)
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bot.infinity_polling(none_stop=True, interval=1, timeout=30)
