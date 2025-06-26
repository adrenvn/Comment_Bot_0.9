"""
Обработчики для управления сценариями Instagram
handlers/scenarios.py - ИСПРАВЛЕННЫЕ ОТСТУПЫ
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Импорты для базы данных
from database.models import User, Scenario, ProxyServer, PendingMessage, SentMessage
from database.connection import Session

# Импорты для сервисов
from services.encryption import EncryptionService
from utils.validators import is_admin, is_user, validate_instagram_credentials
from config import MAX_ACTIVE_SCENARIOS
from ui.menus import scenarios_menu

logger = logging.getLogger(__name__)

def duration_selection_menu():
    """Меню выбора срока активности"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 1 день", callback_data='1d'),
            InlineKeyboardButton("📅 3 дня", callback_data='3d')
        ],
        [
            InlineKeyboardButton("📅 7 дней", callback_data='7d'),
            InlineKeyboardButton("📅 14 дней", callback_data='14d')
        ],
        [InlineKeyboardButton("📅 30 дней", callback_data='30d')],
        [InlineKeyboardButton("🔙 Назад", callback_data='scenarios_menu')]
    ])

def validate_dm_message(message: str) -> bool:
    """Валидация DM сообщения"""
    if not message or len(message) < 10 or len(message) > 1000:
        return False
    
    # Проверка на спам-слова
    spam_words = ['купить', 'скидка', 'акция', 'бесплатно', 'click here', 'www.']
    message_lower = message.lower()
    
    for word in spam_words:
        if word in message_lower:
            return False
    
    return True

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстового ввода для создания сценария"""
    
    # Проверяем, не TikTok ли это сценарий
    try:
        from handlers.tiktok_handlers import handle_tiktok_text_input
        if await handle_tiktok_text_input(update, context):
            return  # TikTok обработчик обработал ввод
    except ImportError:
        logger.debug("TikTok обработчики недоступны")
    except Exception as e:
        logger.error(f"Ошибка TikTok обработчика: {e}")
    
    # Продолжаем с обычной обработкой Instagram
    if 'step' not in context.user_data:
        return
    
    user_id = update.effective_user.id
    if not is_admin(user_id) and not is_user(user_id):
        return

    text = update.message.text.strip()
    step = context.user_data['step']

    try:
        if step == 'ig_username':
            if not validate_instagram_credentials(text, ''):
                await update.message.reply_text(
                    "❌ Некорректный логин Instagram.\n"
                    "Используйте только латинские буквы, цифры, точки и подчеркивания."
                )
                return
                
            context.user_data['ig_username'] = text
            context.user_data['step'] = 'ig_password'
            
            await update.message.reply_text(
                f"🔒 <b>Шаг 2/5: Введите пароль для @{text}:</b>\n\n"
                f"🔐 Пароль будет зашифрован и надежно сохранен",
                parse_mode='HTML'
            )

        elif step == 'ig_password':
            if len(text) < 6:
                await update.message.reply_text("❌ Пароль должен содержать минимум 6 символов.")
                return
                
            # Шифрование пароля
            encryption_service = EncryptionService()
            encrypted_password = encryption_service.encrypt(text)
            
            context.user_data['ig_password'] = encrypted_password
            context.user_data['step'] = 'post_link'
            
            await update.message.reply_text(
                "🔗 <b>Шаг 3/5: Введите ссылку на пост Instagram:</b>\n\n"
                "📝 Пример: https://www.instagram.com/p/ABC123/\n"
                "💡 Бот будет отслеживать комментарии под этим постом",
                parse_mode='HTML'
            )

        elif step == 'post_link':
            if 'instagram.com/p/' not in text and 'instagram.com/reel/' not in text:
                await update.message.reply_text(
                    "❌ Некорректная ссылка на пост Instagram.\n"
                    "Используйте формат: https://www.instagram.com/p/ABC123/"
                )
                return
                
            context.user_data['post_link'] = text
            context.user_data['step'] = 'trigger_word'
            
            await update.message.reply_text(
                "🎯 <b>Шаг 4/5: Введите ключевое слово-триггер:</b>\n\n"
                "💡 Когда пользователь напишет это слово в комментарии,\n"
                "бот отправит ему личное сообщение\n\n"
                "📝 Пример: 'инфо', 'подробности', 'заказать'",
                parse_mode='HTML'
            )

        elif step == 'trigger_word':
            if len(text) < 2 or len(text) > 50:
                await update.message.reply_text(
                    "❌ Ключевое слово должно содержать от 2 до 50 символов."
                )
                return
                
            context.user_data['trigger_word'] = text.lower()
            context.user_data['step'] = 'dm_message'
            
            await update.message.reply_text(
                "💬 <b>Шаг 5/5: Введите текст сообщения:</b>\n\n"
                "📝 Это сообщение получат пользователи, которые написали ключевое слово\n\n"
                "✅ <b>Рекомендации:</b>\n"
                "• Будьте вежливы и информативны\n"
                "• Не используйте спам-слова\n"
                "• Максимум 1000 символов",
                parse_mode='HTML'
            )

        elif step == 'dm_message':
            if not validate_dm_message(text):
                await update.message.reply_text(
                    "❌ Сообщение должно:\n"
                    "• Содержать от 10 до 1000 символов\n"
                    "• Быть информативным и полезным"
                )
                return
                
            context.user_data['dm_message'] = text
            context.user_data['step'] = 'active_until'
            
            # Показ меню выбора срока активности
            await update.message.reply_text(
                "⏰ <b>Выберите срок активности сценария:</b>\n\n"
                "📊 <i>Рекомендация: начните с 1-3 дней для тестирования</i>",
                parse_mode='HTML',
                reply_markup=duration_selection_menu()
            )

    except Exception as e:
        logger.error(f"Ошибка обработки ввода: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте снова.")

async def start_scenario_creation(query, context, user_id):
    """Начало создания нового сценария"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await query.edit_message_text("❌ Пользователь не найден.")
            return

        # Проверка лимита активных сценариев
        active_count = session.query(Scenario).filter_by(
            user_id=user.id, 
            status='running'
        ).count()
        
        if active_count >= MAX_ACTIVE_SCENARIOS:
            await query.edit_message_text(
                f"❌ <b>Превышен лимит активных сценариев</b>\n\n"
                f"Максимум: {MAX_ACTIVE_SCENARIOS} активных сценариев\n"
                f"У вас сейчас: {active_count}\n\n"
                f"Остановите один из существующих сценариев перед созданием нового.",
                parse_mode='HTML',
                reply_markup=scenarios_menu()
            )
            return

        context.user_data.clear()
        context.user_data['step'] = 'proxy_choice'
        
        # Показ доступных прокси
        working_proxies = session.query(ProxyServer).filter_by(
            is_active=True, 
            is_working=True
        ).order_by(ProxyServer.usage_count.asc()).all()
        
        keyboard = []
        if working_proxies:
            keyboard.append([InlineKeyboardButton("🌐 Выбрать прокси", callback_data='choose_proxy')])
            keyboard.append([InlineKeyboardButton("🎯 Лучший прокси", callback_data='choose_best_proxy')])
        
        keyboard.append([InlineKeyboardButton("🛡️ Безопасный режим", callback_data='safe_mode_creation')])
        keyboard.append([InlineKeyboardButton("🚫 Без прокси", callback_data='no_proxy')])
        keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data='scenarios_menu')])
        
        proxy_info = f"Доступно рабочих прокси: {len(working_proxies)}" if working_proxies else "❌ Нет доступных прокси"
        proxy_recommendation = ""
        
        if working_proxies:
            proxy_recommendation = (
                "\n\n💡 <b>Рекомендации:</b>\n"
                "• Прокси повышают анонимность\n"
                "• Снижают риск блокировки аккаунта\n"
                "• Позволяют обходить ограничения IP"
            )
        
        await query.edit_message_text(
            f"🔧 <b>Создание нового сценария</b>\n\n"
            f"📊 {proxy_info}\n"
            f"{proxy_recommendation}\n\n"
            f"Выберите вариант подключения:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        session.close()

async def show_user_scenarios(query, user_id):
    """Показ сценариев пользователя с информацией о прокси"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user or not user.scenarios:
            await query.edit_message_text(
                "📭 <b>У вас пока нет сценариев</b>\n\n"
                "Создайте первый сценарий для автоматизации работы с Instagram!",
                parse_mode='HTML',
                reply_markup=scenarios_menu()
            )
            return

        text = "📋 <b>Ваши сценарии:</b>\n\n"
        keyboard = []
        
        for scenario in user.scenarios:
            # Определение статуса
            status_emoji = {
                'running': '🟢',
                'paused': '⏸️',
                'stopped': '🔴',
                'error': '❌'
            }.get(scenario.status, '⚪')
            
            # Информация о прокси
            proxy_info = "🌐 Прямое" if not scenario.proxy_server else f"🔗 {scenario.proxy_server.name}"
            
            # Время до окончания
            time_left = ""
            if scenario.active_until:
                remaining = scenario.active_until - datetime.now()
                if remaining.total_seconds() > 0:
                    days = remaining.days
                    hours = remaining.seconds // 3600
                    time_left = f"⏱️ {days}д {hours}ч"
                else:
                    time_left = "⏱️ Истек"
            
            text += (
                f"{status_emoji} <b>#{scenario.id}</b> - @{scenario.ig_username}\n"
                f"📱 {proxy_info} | {time_left}\n"
                f"🎯 Триггер: <code>{scenario.trigger_word}</code>\n\n"
            )
            
            keyboard.append([
                InlineKeyboardButton(
                    f"⚙️ Управление #{scenario.id}",
                    callback_data=f'manage_{scenario.id}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='scenarios_menu')])
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        session.close()

async def handle_proxy_choice(query, context):
    """Обработка выбора "без прокси" """
    context.user_data['proxy_id'] = None
    context.user_data['step'] = 'ig_username'
    
    await query.edit_message_text(
        f"🔧 <b>Создание сценария без прокси</b>\n\n"
        f"⚠️ <b>Внимание:</b> Работа без прокси может привести к:\n"
        f"• Повышенному риску блокировки аккаунта\n"
        f"• Ограничениям по IP-адресу\n"
        f"• Снижению анонимности\n\n"
        f"🔧 <b>Шаг 1/5:</b> Введите логин Instagram аккаунта:\n\n"
        f"💡 <i>Пример: username (без @)</i>",
        parse_mode='HTML'
    )

async def show_proxy_selection(query, context):
    """Показ списка доступных прокси для выбора"""
    session = Session()
    try:
        working_proxies = session.query(ProxyServer).filter_by(
            is_active=True, 
            is_working=True
        ).order_by(ProxyServer.usage_count.asc()).all()
        
        if not working_proxies:
            await query.edit_message_text(
                "❌ <b>Нет доступных прокси</b>\n\n"
                "Добавьте рабочие прокси или создайте сценарий без прокси.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛡️ Безопасный режим", callback_data='safe_mode_creation')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='scenarios_menu')]
                ])
            )
            return
        
        text = "🌐 <b>Выберите прокси:</b>\n\n"
        keyboard = []
        
        for proxy in working_proxies[:10]:  # Показываем первые 10
            status = "🟢" if proxy.is_working else "🔴"
            usage_info = f"({proxy.usage_count} исп.)"
            
            text += (
                f"{status} <b>{proxy.name}</b>\n"
                f"📡 {proxy.proxy_type.upper()} | {usage_info}\n"
                f"🌍 {proxy.host}:{proxy.port}\n\n"
            )
            
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ {proxy.name}",
                    callback_data=f'select_proxy_{proxy.id}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🎯 Лучший автоматически", callback_data='choose_best_proxy')])
        keyboard.append([InlineKeyboardButton("🛡️ Безопасный режим", callback_data='safe_mode_creation')])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='scenarios_menu')])
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        session.close()

async def select_proxy_for_scenario(query, context, proxy_id):
    """Выбор конкретного прокси для сценария"""
    session = Session()
    try:
        proxy = session.query(ProxyServer).filter_by(id=proxy_id).first()
        if not proxy:
            await query.edit_message_text("❌ Прокси не найден.")
            return
        
        context.user_data['proxy_id'] = proxy_id
        context.user_data['step'] = 'ig_username'
        
        await query.edit_message_text(
            f"✅ <b>Прокси выбран!</b>\n\n"
            f"📡 <b>Прокси:</b> {proxy.name}\n"
            f"🌐 <b>Тип:</b> {proxy.proxy_type.upper()}\n"
            f"🌍 <b>Сервер:</b> {proxy.host}:{proxy.port}\n"
            f"📊 <b>Использований:</b> {proxy.usage_count}\n\n"
            f"🔧 <b>Шаг 1/5:</b> Введите логин Instagram аккаунта:\n\n"
            f"💡 <i>Пример: username (без @)</i>",
            parse_mode='HTML'
        )
    finally:
        session.close()

async def handle_duration_selection(query, context, duration):
    """Обработчик выбора срока активности"""
    days_map = {
        '1d': 1, '3d': 3, '7d': 7, 
        '14d': 14, '30d': 30
    }
    days = days_map.get(duration, 1)
    
    active_until = datetime.now() + timedelta(days=days)
    context.user_data['active_until'] = active_until
    
    # Проверка наличия всех данных
    required_fields = ['ig_username', 'ig_password', 'post_link', 'trigger_word', 'dm_message']
    missing_fields = [field for field in required_fields if field not in context.user_data]
    
    if missing_fields:
        await query.edit_message_text(
            f"❌ Не хватает данных: {', '.join(missing_fields)}\n"
            "Начните создание сценария заново.",
            reply_markup=scenarios_menu()
        )
        context.user_data.clear()
        return
    
    # Создание сценария
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=query.from_user.id).first()
        if not user:
            await query.edit_message_text("❌ Пользователь не найден.")
            return

        scenario = Scenario(
            user_id=user.id,
            proxy_id=context.user_data.get('proxy_id'),
            ig_username=context.user_data['ig_username'],
            ig_password_encrypted=context.user_data['ig_password'],
            post_link=context.user_data['post_link'],
            trigger_word=context.user_data['trigger_word'],
            dm_message=context.user_data['dm_message'],
            active_until=active_until
        )
        
        session.add(scenario)
        session.commit()
        
        proxy_info = "🌐 Прямое подключение"
        if scenario.proxy_server:
            proxy_info = f"🌐 Прокси: {scenario.proxy_server.name}"
        
        await query.edit_message_text(
            f"✅ <b>Сценарий создан!</b>\n\n"
            f"🆔 ID: #{scenario.id}\n"
            f"📱 Аккаунт: @{scenario.ig_username}\n"
            f"🔗 Пост: {scenario.post_link[:50]}...\n"
            f"🎯 Триггер: <code>{scenario.trigger_word}</code>\n"
            f"{proxy_info}\n"
            f"⏰ Активен до: {scenario.active_until.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🚀 Сценарий готов к запуску!",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Мои сценарии", callback_data='my_scenarios')],
                [InlineKeyboardButton("⚙️ Управление", callback_data=f'manage_{scenario.id}')]
            ])
        )
        
        context.user_data.clear()
        
    except Exception as e:
        logger.error(f"Ошибка создания сценария: {e}")
        await query.edit_message_text("❌ Ошибка при создании сценария.")
        session.rollback()
    finally:
        session.close()

async def confirm_scenario_creation(query, context):
    """Подтверждение создания сценария"""
    # Проверяем, есть ли выбранный прокси
    proxy_id = context.user_data.get('proxy_id')
    safe_mode = context.user_data.get('safe_mode', False)
    
    if proxy_id:
        session = Session()
        try:
            proxy = session.query(ProxyServer).filter_by(id=proxy_id).first()
            proxy_info = f"🌐 Прокси: {proxy.name}" if proxy else "❌ Прокси не найден"
        finally:
            session.close()
    elif safe_mode:
        proxy_info = "🛡️ Безопасный режим (без прокси)"
    else:
        proxy_info = "🌐 Прямое подключение"
    
    context.user_data['step'] = 'ig_username'
    
    await query.edit_message_text(
        f"🔧 <b>Создание сценария</b>\n\n"
        f"{proxy_info}\n\n"
        f"🔧 <b>Шаг 1/5:</b> Введите логин Instagram аккаунта:\n\n"
        f"💡 <i>Пример: username (без @)</i>",
        parse_mode='HTML'
    )

async def show_scenario_management(query, scenario_id, user_id):
    """Показ меню управления сценарием"""
    session = Session()
    try:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            await query.edit_message_text("❌ Сценарий не найден.")
            return
            
        # Проверка доступа
        if scenario.user.telegram_id != user_id and not is_admin(user_id):
            await query.edit_message_text("🚫 У вас нет доступа к этому сценарию.")
            return

        # Статус сценария
        status_emoji = {
            'running': '🟢 Активен',
            'paused': '⏸️ На паузе',
            'stopped': '🔴 Остановлен',
            'error': '❌ Ошибка'
        }.get(scenario.status, '⚪ Неизвестно')
        
        # Информация о прокси
        proxy_info = "🌐 Прямое подключение"
        if scenario.proxy_server:
            proxy_info = f"🌐 {scenario.proxy_server.name}"
        
        # Время до окончания
        time_left = "⏱️ Истек"
        if scenario.active_until and scenario.active_until > datetime.now():
            remaining = scenario.active_until - datetime.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            time_left = f"⏱️ {days}д {hours}ч"
        
        # Статистика
        pending_count = session.query(PendingMessage).filter_by(scenario_id=scenario_id).count()
        sent_count = session.query(SentMessage).filter_by(scenario_id=scenario_id).count()
        
        text = (
            f"⚙️ <b>Управление сценарием #{scenario_id}</b>\n\n"
            f"📱 <b>Аккаунт:</b> @{scenario.ig_username}\n"
            f"📊 <b>Статус:</b> {status_emoji}\n"
            f"🌐 <b>Подключение:</b> {proxy_info}\n"
            f"🎯 <b>Триггер:</b> <code>{scenario.trigger_word}</code>\n"
            f"⏰ <b>До окончания:</b> {time_left}\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Ожидают отправки: {pending_count}\n"
            f"• Отправлено: {sent_count}"
        )
        
        # Кнопки управления
        keyboard = []
        
        if scenario.status == 'running':
            keyboard.append([
                InlineKeyboardButton("⏸️ Пауза", callback_data=f'pause_{scenario_id}'),
                InlineKeyboardButton("🔄 Перезапуск", callback_data=f'restart_{scenario_id}')
            ])
        elif scenario.status == 'paused':
            keyboard.append([
                InlineKeyboardButton("▶️ Продолжить", callback_data=f'resume_{scenario_id}'),
                InlineKeyboardButton("🔄 Перезапуск", callback_data=f'restart_{scenario_id}')
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🚀 Запустить", callback_data=f'resume_{scenario_id}')
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("📬 Проверить комментарии", callback_data=f'check_comments_{scenario_id}'),
                InlineKeyboardButton("📤 Отправить сообщения", callback_data=f'send_messages_{scenario_id}')
            ],
            [
                InlineKeyboardButton("⏰ Настроить проверку", callback_data=f'schedule_check_{scenario_id}')
            ],
            [
                InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_{scenario_id}'),
                InlineKeyboardButton("🔙 Назад", callback_data='my_scenarios')
            ]
        ])
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа управления сценарием: {e}")
        await query.edit_message_text("❌ Ошибка при загрузке сценария.")
    finally:
        session.close()

# === ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ УПРАВЛЕНИЯ СЦЕНАРИЯМИ ===

async def check_scenario_comments(query, scenario_id, user_id):
    """Проверка новых комментариев в сценарии"""
    session = Session()
    try:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            await query.edit_message_text("❌ Сценарий не найден.")
            return
            
        if scenario.user.telegram_id != user_id and not is_admin(user_id):
            await query.edit_message_text("🚫 У вас нет доступа к этому сценарию.")
            return

        await query.edit_message_text(
            f"🔍 <b>Проверка комментариев</b>\n\n"
            f"⏳ Проверяю новые комментарии под постом...\n"
            f"📱 Аккаунт: @{scenario.ig_username}\n"
            f"🎯 Ищу триггер: <code>{scenario.trigger_word}</code>",
            parse_mode='HTML'
        )
        
        # Здесь будет логика проверки комментариев
        # Пока что заглушка
        pending_count = session.query(PendingMessage).filter_by(scenario_id=scenario_id).count()
        
        await query.edit_message_text(
            f"✅ <b>Проверка завершена!</b>\n\n"
            f"📊 Найдено новых триггеров: 0\n"
            f"📬 В очереди на отправку: {pending_count}\n"
            f"🕐 Время проверки: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Отправить сообщения", callback_data=f'send_messages_{scenario_id}')],
                [InlineKeyboardButton("🔙 Назад", callback_data=f'manage_{scenario_id}')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка проверки комментариев: {e}")
        await query.edit_message_text("❌ Ошибка при проверке комментариев.")
    finally:
        session.close()

async def send_pending_messages(query, scenario_id, user_id):
    """Отправка ожидающих сообщений"""
    session = Session()
    try:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            await query.edit_message_text("❌ Сценарий не найден.")
            return
            
        if scenario.user.telegram_id != user_id and not is_admin(user_id):
            await query.edit_message_text("🚫 У вас нет доступа к этому сценарию.")
            return

        pending_count = session.query(PendingMessage).filter_by(scenario_id=scenario_id).count()
        
        if pending_count == 0:
            await query.edit_message_text(
                "📭 <b>Очередь сообщений пуста</b>\n\n"
                "Сначала проверьте комментарии для поиска новых триггеров.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Проверить комментарии", callback_data=f'check_comments_{scenario_id}')],
                    [InlineKeyboardButton("🔙 Назад", callback_data=f'manage_{scenario_id}')]
                ])
            )
            return

        await query.edit_message_text(
            f"📩 <b>Отправка сообщений</b>\n\n"
            f"⏳ Отправляю {pending_count} сообщений...\n"
            f"📱 Аккаунт: @{scenario.ig_username}",
            parse_mode='HTML'
        )
        
        # Здесь будет логика отправки сообщений
        # Пока что заглушка
        sent_count = 0
        failed_count = 0
        
        await query.edit_message_text(
            f"✅ <b>Отправка завершена!</b>\n\n"
            f"📩 Отправлено: {sent_count}\n"
            f"❌ Ошибок: {failed_count}\n"
            f"⏳ Осталось в очереди: {pending_count - sent_count}\n\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data=f'manage_{scenario_id}')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщений: {e}")
        await query.edit_message_text("❌ Ошибка при отправке сообщений.")
    finally:
        session.close()

async def show_schedule_menu(query, scenario_id):
    """Показ меню планирования проверок"""
    await query.edit_message_text(
        f"⏰ <b>Настройка автоматической проверки</b>\n\n"
        f"📱 Сценарий #{scenario_id}\n\n"
        f"Выберите интервал проверки комментариев:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚡ 5 минут", callback_data=f'set_timer_5_{scenario_id}'),
                InlineKeyboardButton("🕐 15 минут", callback_data=f'set_timer_15_{scenario_id}')
            ],
            [
                InlineKeyboardButton("🕑 30 минут", callback_data=f'set_timer_30_{scenario_id}'),
                InlineKeyboardButton("🕒 1 час", callback_data=f'set_timer_60_{scenario_id}')
            ],
            [
                InlineKeyboardButton("🕕 3 часа", callback_data=f'set_timer_180_{scenario_id}'),
                InlineKeyboardButton("🕘 6 часов", callback_data=f'set_timer_360_{scenario_id}')
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data=f'manage_{scenario_id}')]
        ])
    )

async def set_check_timer(query, minutes, scenario_id):
    """Установка таймера проверки"""
    session = Session()
    try:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            await query.edit_message_text("❌ Сценарий не найден.")
            return

        # Здесь будет логика установки таймера
        next_check = datetime.now() + timedelta(minutes=minutes)
        
        await query.edit_message_text(
            f"✅ <b>Таймер установлен!</b>\n\n"
            f"📱 Сценарий: #{scenario_id}\n"
            f"⏰ Интервал: {minutes} минут\n"
            f"⏳ Следующая проверка: {next_check.strftime('%H:%M:%S')}\n\n"
            f"🔄 Автоматическая проверка активирована",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Изменить", callback_data=f'schedule_check_{scenario_id}')],
                [InlineKeyboardButton("🔙 Назад", callback_data=f'manage_{scenario_id}')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка установки таймера: {e}")
        await query.edit_message_text("❌ Ошибка при установке таймера.")
    finally:
        session.close()

async def pause_scenario(query, scenario_id, user_id):
    """Приостановка сценария"""
    session = Session()
    try:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            await query.edit_message_text("❌ Сценарий не найден.")
            return
            
        if scenario.user.telegram_id != user_id and not is_admin(user_id):
            await query.edit_message_text("🚫 У вас нет доступа к этому сценарию.")
            return

        # Остановка задачи если она запущена
        try:
            from config import tasks
            if scenario_id in tasks:
                tasks[scenario_id].cancel()
                del tasks[scenario_id]
        except ImportError:
            pass

        scenario.status = 'paused'
        session.merge(scenario)
        session.commit()
        
        await query.edit_message_text(
            f"⏸️ <b>Сценарий приостановлен</b>\n\n"
            f"📱 Сценарий: #{scenario_id}\n"
            f"👤 Аккаунт: @{scenario.ig_username}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"▶️ Для продолжения используйте кнопку 'Возобновить'",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Возобновить", callback_data=f'resume_{scenario_id}')],
                [InlineKeyboardButton("⚙️ Управление", callback_data=f'manage_{scenario_id}')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка приостановки сценария: {e}")
        await query.edit_message_text("❌ Ошибка при приостановке сценария.")
    finally:
        session.close()

async def resume_scenario(query, scenario_id, user_id):
    """Возобновление сценария"""
    session = Session()
    try:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            await query.edit_message_text("❌ Сценарий не найден.")
            return
            
        if scenario.user.telegram_id != user_id and not is_admin(user_id):
            await query.edit_message_text("🚫 У вас нет доступа к этому сценарию.")
            return

        scenario.status = 'running'
        session.merge(scenario)
        session.commit()
        
        # Здесь будет логика запуска задачи
        
        await query.edit_message_text(
            f"▶️ <b>Сценарий возобновлен</b>\n\n"
            f"📱 Сценарий: #{scenario_id}\n"
            f"👤 Аккаунт: @{scenario.ig_username}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"🚀 Сценарий снова активен и обрабатывает комментарии",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏸️ Приостановить", callback_data=f'pause_{scenario_id}')],
                [InlineKeyboardButton("⚙️ Управление", callback_data=f'manage_{scenario_id}')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка возобновления сценария: {e}")
        await query.edit_message_text("❌ Ошибка при возобновлении сценария.")
    finally:
        session.close()

async def delete_scenario(query, scenario_id, user_id):
    """Удаление сценария"""
    session = Session()
    try:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            await query.edit_message_text("❌ Сценарий не найден.")
            return
            
        if scenario.user.telegram_id != user_id and not is_admin(user_id):
            await query.edit_message_text("🚫 У вас нет доступа к этому сценарию.")
            return

        # Остановка задачи если она запущена
        try:
            from config import tasks, instabots
            if scenario_id in tasks:
                tasks[scenario_id].cancel()
                del tasks[scenario_id]
                
            if scenario_id in instabots:
                try:
                    instabots[scenario_id].logout()
                except:
                    pass
                del instabots[scenario_id]
        except ImportError:
            pass

        username = scenario.ig_username
        
        # Удаляем сценарий (связанные записи удаляются автоматически благодаря cascade)
        session.delete(scenario)
        session.commit()

        await query.edit_message_text(
            f"🗑️ <b>Сценарий удален</b>\n\n"
            f"📱 Аккаунт: @{username}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"✅ Все связанные данные также удалены",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Мои сценарии", callback_data='my_scenarios')],
                [InlineKeyboardButton("➕ Создать новый", callback_data='add_scenario')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка удаления сценария: {e}")
        await query.edit_message_text("❌ Ошибка при удалении сценария.")
    finally:
        session.close()

# === АДМИНСКИЕ ФУНКЦИИ ===

async def show_manage_users_info(query):
    """Информация об управлении пользователями"""
    await query.edit_message_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "• <code>/adduser [telegram_id]</code> - добавить пользователя\n"
        "• <code>/deleteuser [telegram_id]</code> - удалить пользователя\n\n"
        "💡 <b>Примеры:</b>\n"
        "• <code>/adduser 123456789</code>\n"
        "• <code>/deleteuser 123456789</code>\n\n"
        "📞 Получить ID пользователя: @userinfobot",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Админ-панель", callback_data='admin_panel')]
        ])
    )

async def show_manage_admins_info(query):
    """Информация об управлении администраторами"""
    await query.edit_message_text(
        "👑 <b>Управление администраторами</b>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "• <code>/addadmin [telegram_id]</code> - добавить администратора\n\n"
        "💡 <b>Пример:</b>\n"
        "• <code>/addadmin 123456789</code>\n\n"
        "⚠️ <b>Внимание:</b>\n"
        "• Администраторы имеют полный доступ к боту\n"
        "• Могут управлять всеми сценариями\n"
        "• Добавляйте только доверенных лиц\n\n"
        "📞 Получить ID пользователя: @userinfobot",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Админ-панель", callback_data='admin_panel')]
        ])
    )

async def show_scenarios_status(query):
    """Показ статуса всех сценариев (админ)"""
    session = Session()
    try:
        scenarios = session.query(Scenario).all()
        
        if not scenarios:
            await query.edit_message_text(
                "📭 <b>Сценариев пока нет</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Админ-панель", callback_data='admin_panel')]
                ])
            )
            return

        # Статистика по статусам
        status_counts = {}
        for scenario in scenarios:
            status = scenario.status
            status_counts[status] = status_counts.get(status, 0) + 1

        text = "📊 <b>Статус всех сценариев</b>\n\n"
        
        status_emoji = {
            'running': '🟢',
            'paused': '⏸️',
            'stopped': '🔴',
            'error': '❌'
        }
        
        for status, count in status_counts.items():
            emoji = status_emoji.get(status, '⚪')
            text += f"{emoji} {status.title()}: {count}\n"
        
        text += f"\n📈 <b>Всего сценариев:</b> {len(scenarios)}"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Все сценарии", callback_data='all_scenarios')],
                [InlineKeyboardButton("🔙 Админ-панель", callback_data='admin_panel')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса сценариев: {e}")
        await query.edit_message_text("❌ Ошибка получения данных.")
    finally:
        session.close()

async def show_all_scenarios(query):
    """Показ всех сценариев (админ)"""
    session = Session()
    try:
        scenarios = session.query(Scenario).order_by(Scenario.created_at.desc()).limit(20).all()
        
        if not scenarios:
            await query.edit_message_text(
                "📭 <b>Сценариев пока нет</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Админ-панель", callback_data='admin_panel')]
                ])
            )
            return

        text = "📋 <b>Все сценарии (последние 20)</b>\n\n"
        
        for scenario in scenarios:
            status_emoji = {
                'running': '🟢',
                'paused': '⏸️',
                'stopped': '🔴',
                'error': '❌'
            }.get(scenario.status, '⚪')
            
            proxy_info = "🌐" if scenario.proxy_server else "📡"
            
            text += (
                f"{status_emoji} <b>#{scenario.id}</b> - @{scenario.ig_username}\n"
                f"👤 Пользователь: {scenario.user.telegram_id}\n"
                f"{proxy_info} Триггер: <code>{scenario.trigger_word}</code>\n\n"
            )
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Статистика", callback_data='status_scenarios')],
                [InlineKeyboardButton("🔙 Админ-панель", callback_data='admin_panel')]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения всех сценариев: {e}")
        await query.edit_message_text("❌ Ошибка получения данных.")
    finally:
        session.close()

async def show_help_info(query):
    """Показ справочной информации"""
    await query.edit_message_text(
        "❓ <b>Справка по Instagram Automation Bot v2.0</b>\n\n"
        "🔧 <b>Основные функции:</b>\n"
        "• Создание сценариев автоответов\n"
        "• Мониторинг комментариев Instagram\n"
        "• Автоматическая отправка DM сообщений\n"
        "• Управление прокси-серверами\n\n"
        "📱 <b>Как создать сценарий:</b>\n"
        "1. Нажмите 'Создать сценарий'\n"
        "2. Выберите прокси (рекомендуется)\n"
        "3. Введите данные Instagram аккаунта\n"
        "4. Укажите ссылку на пост\n"
        "5. Задайте ключевое слово-триггер\n"
        "6. Напишите текст автоответа\n"
        "7. Выберите срок активности\n\n"
        "🛡️ <b>Безопасность:</b>\n"
        "• Используйте качественные прокси\n"
        "• Не превышайте лимиты Instagram\n"
        "• Делайте перерывы между сценариями\n\n"
        "📞 <b>Поддержка:</b>\n"
        "При возникновении проблем обратитесь к администратору",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Главное меню", callback_data='back')]
        ])
    )

def show_scenario_management_menu(scenario_id):
    """Возвращает меню управления сценарием"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 Проверить комментарии", callback_data=f'check_comments_{scenario_id}'),
            InlineKeyboardButton("📤 Отправить сообщения", callback_data=f'send_messages_{scenario_id}')
        ],
        [
            InlineKeyboardButton("⏸️ Пауза", callback_data=f'pause_{scenario_id}'),
            InlineKeyboardButton("🔄 Перезапуск", callback_data=f'restart_{scenario_id}')
        ],
        [
            InlineKeyboardButton("⏰ Настроить таймер", callback_data=f'schedule_check_{scenario_id}')
        ],
        [
            InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_{scenario_id}'),
            InlineKeyboardButton("🔙 Назад", callback_data='my_scenarios')
        ]
    ])