#!/usr/bin/env python3
"""
Instagram Automation Bot v2.0 с поддержкой TikTok
Основной файл запуска бота - ПРОСТОЕ ИСПРАВЛЕНИЕ
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

# Загрузка переменных окружения
load_dotenv()

# Импорты конфигурации
from config import TELEGRAM_TOKEN, ADMIN_TELEGRAM_ID

def setup_logging():
    """Настройка логирования"""
    # Создаём директории
    for directory in ["./logs", "./data", "./sessions"]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Для Docker совместимости
    log_dir = "/app/logs" if os.path.exists("/app") else "./logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "bot.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

async def universal_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик текстовых сообщений"""
    logger = logging.getLogger(__name__)
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    logger.info(f"📝 TEXT INPUT: '{text}' от пользователя {user_id}")
    logger.info(f"🔍 USER_DATA: {context.user_data}")
    
    try:
        # Проверка доступа
        from utils.validators import is_admin, is_user
        if not is_admin(user_id) and not is_user(user_id):
            await update.message.reply_text("🚫 У вас нет доступа к боту.")
            return
        
        # 1. ОБРАБОТКА СОЗДАНИЯ ПРОКСИ (proxy_step)
        if 'proxy_step' in context.user_data:
            logger.info(f"🌐 Обрабатываю ввод прокси: {context.user_data['proxy_step']}")
            try:
                from handlers.proxy import handle_proxy_input
                await handle_proxy_input(update, context)
                return
            except ImportError as e:
                logger.error(f"❌ Модуль proxy недоступен: {e}")
                await update.message.reply_text("❌ Модуль создания прокси недоступен.")
                return
            except Exception as e:
                logger.error(f"❌ Ошибка обработки прокси: {e}")
                await update.message.reply_text("❌ Ошибка при обработке данных прокси.")
                return
        
        # 2. ОБРАБОТКА СОЗДАНИЯ СЦЕНАРИЕВ INSTAGRAM (step)
        elif 'step' in context.user_data and context.user_data.get('platform') != 'tiktok':
            logger.info(f"📸 Обрабатываю ввод Instagram: {context.user_data['step']}")
            try:
                from handlers.scenarios import handle_text_input
                await handle_text_input(update, context)
                return
            except ImportError as e:
                logger.error(f"❌ Модуль scenarios недоступен: {e}")
                await update.message.reply_text("❌ Модуль сценариев недоступен.")
                return
            except Exception as e:
                logger.error(f"❌ Ошибка обработки сценариев: {e}")
                await update.message.reply_text("❌ Ошибка при обработке сценария.")
                return
        
        # 3. ОБРАБОТКА TIKTOK СЦЕНАРИЕВ
        elif 'step' in context.user_data and context.user_data.get('platform') == 'tiktok':
            logger.info(f"🎵 Обрабатываю ввод TikTok: {context.user_data['step']}")
            try:
                from handlers.tiktok_handlers import handle_tiktok_text_input
                await handle_tiktok_text_input(update, context)
                return
            except ImportError:
                await update.message.reply_text("❌ TikTok функционал недоступен.")
                return
        
        # 4. ОБРАБОТКА ИМПОРТА ПРОКСИ
        elif 'import_step' in context.user_data:
            logger.info(f"📥 Обрабатываю импорт прокси: {context.user_data['import_step']}")
            try:
                from handlers.proxy_import import handle_import_input
                await handle_import_input(update, context)
                return
            except ImportError:
                await update.message.reply_text("❌ Функция импорта недоступна.")
                return
        
        # 5. SMS КОДЫ И КОМАНДЫ АВТОРИЗАЦИИ
        elif text.isdigit() and len(text) in [4, 5, 6, 8]:
            logger.info(f"📱 Получен SMS код: {text}")
            try:
                from services.enhanced_auth import handle_sms_code_input
                await handle_sms_code_input(update, context)
                return
            except ImportError:
                await update.message.reply_text("SMS коды пока не поддерживаются.")
                return
        
        # 6. БАЗОВЫЕ КОМАНДЫ
        elif text.lower() in ['привет', 'hello', 'hi']:
            await update.message.reply_text(
                "👋 Привет! Я Instagram Automation Bot v2.0\n\n"
                "Используйте команду /start для начала работы."
            )
        elif text.lower() in ['помощь', 'help']:
            await update.message.reply_text(
                "📖 Используйте команду /help для получения справки"
            )
        
        # 7. НЕИЗВЕСТНЫЕ СООБЩЕНИЯ
        else:
            logger.info(f"❓ Неизвестное сообщение: {text}")
            await update.message.reply_text(
                "❓ <b>Непонятная команда</b>\n\n"
                "Используйте /start для открытия главного меню\n"
                "или /help для получения справки.",
                parse_mode='HTML'
            )
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в универсальном обработчике: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке сообщения.\n"
            "Попробуйте /start для возврата в главное меню."
        )

def main():
    """Основная функция запуска бота"""
    logger = setup_logging()
    
    try:
        # Проверка токена
        if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your_telegram_bot_token_here":
            logger.error("❌ TELEGRAM_TOKEN не настроен в .env файле!")
            logger.error("Получите токен от @BotFather и добавьте в .env файл")
            return
        
        if not ADMIN_TELEGRAM_ID or ADMIN_TELEGRAM_ID == "your_telegram_id_here":
            logger.error("❌ ADMIN_TELEGRAM_ID не настроен в .env файле!")
            logger.error("Получите ваш ID от @userinfobot и добавьте в .env файл")
            return
        
        logger.info("🚀 Запуск Instagram Automation Bot v2.0")
        logger.info(f"👑 Администратор: {ADMIN_TELEGRAM_ID}")
        
        # Инициализация базы данных
        from database.connection import init_database
        if not init_database():
            logger.error("❌ Ошибка инициализации базы данных")
            return
        
        # Создание приложения
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Импорт обработчиков
        from handlers.commands import start, help_command, add_user, delete_user, add_admin
        from handlers.callbacks import button_handler
        
        # Регистрация обработчиков команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("adduser", add_user))
        application.add_handler(CommandHandler("deleteuser", delete_user))
        application.add_handler(CommandHandler("addadmin", add_admin))
        
        # Регистрация обработчиков callback'ов
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Регистрация универсального обработчика текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, universal_text_handler))
        
        logger.info("✅ Все обработчики зарегистрированы")
        
        # Запуск бота
        logger.info("🤖 Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=['message', 'callback_query'])
        
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()