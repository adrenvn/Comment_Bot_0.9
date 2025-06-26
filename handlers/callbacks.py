"""
Основные обработчики callback запросов (нажатий кнопок)
handlers/callbacks.py - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ ОШИБОК ПАРСИНГА
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.validators import is_admin, is_user
from ui.menus import main_menu, admin_menu, scenarios_menu, tiktok_scenarios_menu

logger = logging.getLogger(__name__)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data

    logger.info(f"🔧 CALLBACK: '{data}' от пользователя {user_id}")

    # Проверка доступа
    if not is_admin(user_id) and not is_user(user_id):
        await query.edit_message_text("🚫 У вас нет доступа к боту.")
        return

    is_admin_user = is_admin(user_id)
    is_user_user = is_user(user_id)

    try:
        # === ОСНОВНАЯ НАВИГАЦИЯ ===
        if data == 'back':
            await query.edit_message_text(
                "🏠 Главное меню:",
                reply_markup=main_menu(is_admin_user, is_user_user)
            )
        elif data == 'scenarios_menu':
            await query.edit_message_text(
                "📂 Управление сценариями:",
                reply_markup=scenarios_menu()
            )
        elif data == 'admin_panel':
            if is_admin_user:
                await query.edit_message_text(
                    "👑 Панель администратора:",
                    reply_markup=admin_menu()
                )
            else:
                await query.edit_message_text("🚫 У вас нет доступа к админ-панели.")

        # === ВЫБОР ПЛАТФОРМЫ ===
        elif data == 'instagram_scenarios':
            await query.edit_message_text(
                "📸 <b>Instagram автоматизация</b>\n\n"
                "Выберите действие:",
                parse_mode='HTML',
                reply_markup=scenarios_menu()
            )

        elif data == 'tiktok_scenarios':
            await query.edit_message_text(
                "🎵 <b>TikTok автоматизация</b>\n\n"
                "Выберите действие:",
                parse_mode='HTML',
                reply_markup=tiktok_scenarios_menu()
            )
        
        # === УПРАВЛЕНИЕ ПРОКСИ ===
        elif data == 'manage_proxies':
            try:
                from handlers.proxy import manage_proxies_menu
                await manage_proxies_menu(query)
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        elif data == 'add_proxy':
            try:
                from handlers.proxy import start_add_proxy
                await start_add_proxy(query, context)
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        elif data == 'list_proxies':
            try:
                from handlers.proxy import list_proxies
                await list_proxies(query)
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        elif data == 'check_all_proxies':
            try:
                from handlers.proxy import check_all_proxies
                await check_all_proxies(query)
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        elif data == 'proxy_stats':
            try:
                from handlers.proxy import show_proxy_stats
                await show_proxy_stats(query)
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        
        # === СОЗДАНИЕ ПРОКСИ - ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ ===
        elif data.startswith('proxy_type_'):
            try:
                from handlers.proxy import handle_proxy_type_selection
                proxy_type = data.split('_')[2]
                await handle_proxy_type_selection(query, context, proxy_type)
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
            except Exception as e:
                logger.error(f"Ошибка выбора типа прокси: {e}")
                await query.edit_message_text("❌ Ошибка выбора типа прокси.")
        elif data == 'confirm_proxy':
            try:
                from handlers.proxy import create_proxy_server
                await create_proxy_server(query, context)
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
            except Exception as e:
                logger.error(f"Ошибка создания прокси: {e}")
                await query.edit_message_text("❌ Ошибка создания прокси.")
        elif data.startswith('delete_proxy_'):
            try:
                from handlers.proxy import delete_proxy_server
                proxy_id = int(data.split('_')[2])
                await delete_proxy_server(query, proxy_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID прокси.")
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        elif data.startswith('check_proxy_'):
            try:
                from handlers.proxy import check_single_proxy
                proxy_id = int(data.split('_')[2])
                await check_single_proxy(query, proxy_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID прокси.")
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        elif data.startswith('manage_proxy_'):
            try:
                from handlers.proxy import manage_single_proxy
                proxy_id = int(data.split('_')[2])
                await manage_single_proxy(query, proxy_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID прокси.")
            except ImportError:
                await query.edit_message_text("❌ Модуль proxy не найден.")
        
        # === СЦЕНАРИИ ===
        elif data == 'add_scenario':
            try:
                from handlers.scenarios import start_scenario_creation
                await start_scenario_creation(query, context, user_id)
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data == 'my_scenarios':
            try:
                from handlers.scenarios import show_user_scenarios
                await show_user_scenarios(query, user_id)
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        
        # === TIKTOK СЦЕНАРИИ ===
        elif data == 'add_tiktok_scenario':
            try:
                from handlers.tiktok_handlers import start_tiktok_scenario_creation
                await start_tiktok_scenario_creation(query, context, user_id)
            except ImportError:
                await query.edit_message_text(
                    "❌ <b>TikTok функционал недоступен</b>\n\n"
                    "Модуль TikTok обработчиков не найден.\n"
                    "Обратитесь к администратору.",
                    parse_mode='HTML'
                )
        elif data == 'my_tiktok_scenarios':
            try:
                from handlers.tiktok_handlers import show_user_tiktok_scenarios
                await show_user_tiktok_scenarios(query, user_id)
            except ImportError:
                await query.edit_message_text("❌ Модуль tiktok_handlers не найден.")
        
        # === СОЗДАНИЕ СЦЕНАРИЯ ===
        elif data == 'confirm_scenario':
            try:
                from handlers.scenarios import confirm_scenario_creation
                await confirm_scenario_creation(query, context)
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data in ['1d', '3d', '7d', '14d', '30d']:
            try:
                from handlers.scenarios import handle_duration_selection
                await handle_duration_selection(query, context, data)
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        
        # === ВЫБОР ПРОКСИ ДЛЯ СЦЕНАРИЯ ===
        elif data == 'choose_proxy':
            await show_proxy_selection(query, context)
        elif data == 'choose_best_proxy':
            await select_best_proxy_automatically(query, context)
        elif data == 'safe_mode_creation':
            await handle_safe_mode_creation(query, context)
        elif data == 'no_proxy':
            await handle_proxy_choice(query, context)
        elif data.startswith('select_proxy_'):
            try:
                proxy_id = int(data.split("_")[2])
                await select_proxy_for_scenario(query, context, proxy_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID прокси.")
        
        # === УПРАВЛЕНИЕ СЦЕНАРИЯМИ - ИСПРАВЛЕННАЯ ОБРАБОТКА ===
        elif data.startswith('manage_') and data != 'manage_proxies' and data != 'manage_users' and data != 'manage_admins':
            try:
                from handlers.scenarios import show_scenario_management
                scenario_id = int(data.split("_")[1])
                await show_scenario_management(query, scenario_id, user_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data.startswith('check_comments_'):
            try:
                from handlers.scenarios import check_scenario_comments
                scenario_id = int(data.split("_")[2])
                await check_scenario_comments(query, scenario_id, user_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data.startswith('send_messages_'):
            try:
                from handlers.scenarios import send_pending_messages
                scenario_id = int(data.split("_")[2])
                await send_pending_messages(query, scenario_id, user_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data.startswith('pause_') and not data.startswith('pause_proxy'):
            try:
                from handlers.scenarios import pause_scenario
                scenario_id = int(data.split("_")[1])
                await pause_scenario(query, scenario_id, user_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data.startswith('resume_'):
            try:
                from handlers.scenarios import resume_scenario
                scenario_id = int(data.split("_")[1])
                await resume_scenario(query, scenario_id, user_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data.startswith('restart_'):
            try:
                scenario_id = int(data.split("_")[1])
                await restart_scenario_enhanced(query, scenario_id, user_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
        elif data.startswith('delete_') and not data.startswith('delete_proxy'):
            try:
                from handlers.scenarios import delete_scenario
                scenario_id = int(data.split("_")[1])
                await delete_scenario(query, scenario_id, user_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data.startswith('schedule_check_'):
            try:
                from handlers.scenarios import show_schedule_menu
                scenario_id = int(data.split("_")[2])
                await show_schedule_menu(query, scenario_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректный ID сценария.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        elif data.startswith('set_timer_'):
            try:
                from handlers.scenarios import set_check_timer
                parts = data.split("_")
                minutes = int(parts[2])
                scenario_id = int(parts[3])
                await set_check_timer(query, minutes, scenario_id)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Некорректные параметры таймера.")
            except ImportError:
                await query.edit_message_text("❌ Модуль scenarios не найден.")
        
        # === АДМИНСКИЕ ФУНКЦИИ - ИСПРАВЛЕНЫ ===
        elif data == 'manage_users':
            if is_admin_user:
                try:
                    from handlers.scenarios import show_manage_users_info
                    await show_manage_users_info(query)
                except ImportError:
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
            else:
                await query.edit_message_text("🚫 У вас нет доступа к управлению пользователями.")
        elif data == 'manage_admins':
            if is_admin_user:
                try:
                    from handlers.scenarios import show_manage_admins_info
                    await show_manage_admins_info(query)
                except ImportError:
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
            else:
                await query.edit_message_text("🚫 У вас нет доступа к управлению администраторами.")
        elif data == 'status_scenarios':
            if is_admin_user:
                try:
                    from handlers.scenarios import show_scenarios_status
                    await show_scenarios_status(query)
                except ImportError:
                    await query.edit_message_text("❌ Модуль scenarios не найден.")
            else:
                await query.edit_message_text("🚫 У вас нет доступа к статистике.")
        elif data == 'all_scenarios':
            if is_admin_user:
                try:
                    from handlers.scenarios import show_all_scenarios
                    await show_all_scenarios(query)
                except ImportError:
                    await query.edit_message_text("❌ Модуль scenarios не найден.")
            else:
                await query.edit_message_text("🚫 У вас нет доступа к списку сценариев.")
        
        # === ПОМОЩЬ ===
        elif data == 'help':
            try:
                from handlers.scenarios import show_help_info
                await show_help_info(query)
            except ImportError:
                await query.edit_message_text(
                    "❓ <b>Помощь</b>\n\n"
                    "📖 Instagram Automation Bot v2.0\n\n"
                    "🤖 Автоматизация комментариев Instagram\n"
                    "🎵 Поддержка TikTok (в разработке)\n"
                    "🌐 Интеграция с прокси серверами\n"
                    "📊 Детальная статистика\n\n"
                    "👑 Для администраторов доступны расширенные функции.",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
                    ])
                )
        
        # === ИНФОРМАЦИОННЫЕ КНОПКИ ===
        elif data == 'noop':
            pass  # Ничего не делаем для информационных кнопок
        
        # === НЕИЗВЕСТНЫЕ CALLBACK'И ===
        else:
            logger.warning(f"Неизвестный callback: {data}")
            await query.edit_message_text(
                f"❌ Неизвестная команда: {data}\n\nВозможно, функция еще не реализована.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Главное меню", callback_data='back')]
                ])
            )

    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

# === ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОКСИ В СЦЕНАРИЯХ ===

async def select_best_proxy_automatically(query, context):
    """Автоматический выбор лучшего прокси"""
    try:
        from database.models import ProxyServer
        from database.connection import Session
        
        session = Session()
        try:
            # Ищем лучший прокси (работающий, с минимальным использованием)
            best_proxy = session.query(ProxyServer).filter_by(
                is_active=True, 
                is_working=True
            ).order_by(ProxyServer.usage_count.asc()).first()
            
            if not best_proxy:
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
            
            context.user_data['proxy_id'] = best_proxy.id
            context.user_data['step'] = 'ig_username'
            
            await query.edit_message_text(
                f"🎯 <b>Автоматически выбран лучший прокси!</b>\n\n"
                f"📡 <b>Прокси:</b> {best_proxy.name}\n"
                f"🌐 <b>Тип:</b> {best_proxy.proxy_type.upper()}\n"
                f"🌍 <b>Сервер:</b> {best_proxy.host}:{best_proxy.port}\n"
                f"📊 <b>Использований:</b> {best_proxy.usage_count}\n\n"
                f"🔧 <b>Шаг 1/5:</b> Введите логин Instagram аккаунта:\n\n"
                f"💡 <i>Пример: username (без @)</i>",
                parse_mode='HTML'
            )
        finally:
            session.close()
    except ImportError:
        await query.edit_message_text("❌ Функция недоступна.")

async def show_proxy_selection(query, context):
    """Показ списка доступных прокси для выбора"""
    try:
        from database.models import ProxyServer
        from database.connection import Session
        
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
    except ImportError:
        await query.edit_message_text("❌ Модуль scenarios не найден.")

async def select_proxy_for_scenario(query, context, proxy_id):
    """Выбор конкретного прокси для сценария"""
    try:
        from database.models import ProxyServer
        from database.connection import Session
        
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
    except ImportError:
        await query.edit_message_text("❌ Модуль scenarios не найден.")

async def handle_safe_mode_creation(query, context):
    """Безопасный режим создания сценария"""
    context.user_data['proxy_id'] = None
    context.user_data['safe_mode'] = True
    context.user_data['step'] = 'ig_username'
    
    await query.edit_message_text(
        f"🛡️ <b>Безопасный режим активирован</b>\n\n"
        f"🔐 <b>Особенности безопасного режима:</b>\n"
        f"• Увеличенные задержки между действиями\n"
        f"• Дополнительные проверки безопасности\n"
        f"• Защита от блокировки аккаунта\n"
        f"• Работа без прокси, но с мерами предосторожности\n\n"
        f"🔧 <b>Шаг 1/5:</b> Введите логин Instagram аккаунта:\n\n"
        f"💡 <i>Пример: username (без @)</i>",
        parse_mode='HTML'
    )

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

async def restart_scenario_enhanced(query, scenario_id, user_id):
    """Перезапуск сценария с улучшенной авторизацией"""
    try:
        from database.models import Scenario
        from database.connection import Session
        
        session = Session()
        try:
            scenario = session.query(Scenario).filter_by(id=scenario_id).first()
            if not scenario:
                await query.edit_message_text("❌ Сценарий не найден.")
                return
                
            if scenario.user.telegram_id != user_id and not is_admin(user_id):
                await query.edit_message_text("🚫 У вас нет доступа к этому сценарию.")
                return

            # Остановка старой задачи
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
                pass  # Если модуль config недоступен

            # Сброс состояния
            scenario.status = 'running'
            scenario.auth_status = 'waiting'
            scenario.auth_attempt = 1
            scenario.error_message = None
            session.merge(scenario)
            session.commit()

            # Создаем простое меню управления
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 Проверить комментарии", callback_data=f'check_comments_{scenario_id}'),
                    InlineKeyboardButton("📤 Отправить сообщения", callback_data=f'send_messages_{scenario_id}')
                ],
                [
                    InlineKeyboardButton("⏸️ Пауза", callback_data=f'pause_{scenario_id}'),
                    InlineKeyboardButton("🔄 Перезапуск", callback_data=f'restart_{scenario_id}')
                ],
                [
                    InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_{scenario_id}'),
                    InlineKeyboardButton("🔙 Назад", callback_data='my_scenarios')
                ]
            ])

            await query.edit_message_text(
                "🚀 <b>Сценарий перезапущен</b>\n\n"
                f"📱 Сценарий: #{scenario_id}\n"
                f"👤 Аккаунт: @{scenario.ig_username}\n\n"
                f"⚡ Начинается авторизация...\n"
                f"📊 Отслеживайте прогресс в реальном времени",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            logger.info(f"Сценарий {scenario_id} перезапущен пользователем {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка перезапуска сценария: {e}")
            await query.edit_message_text("❌ Ошибка при перезапуске сценария.")
        finally:
            session.close()
    except ImportError as e:
        logger.error(f"Отсутствует модуль: {e}")
        await query.edit_message_text("❌ Функция перезапуска временно недоступна.")