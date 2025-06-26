"""
Конфигурация Instagram Automation Bot v2.0
ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import os
from cryptography.fernet import Fernet

# === ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен в .env файле")

ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")
DATABASE_PATH = os.getenv("DATABASE_PATH", "sqlite:///./data/bot_database.db")

# === БЕЗОПАСНАЯ ИНИЦИАЛИЗАЦИЯ ШИФРОВАНИЯ ===
def init_encryption():
    """Безопасная инициализация ключа шифрования"""
    encryption_key = os.getenv("ENCRYPTION_KEY")
    
    # Если ключа нет или он стандартный
    if not encryption_key or encryption_key == "your_base64_encryption_key_here":
        print("🔑 Генерирую новый ключ шифрования...")
        encryption_key = Fernet.generate_key().decode()
        print(f"✅ Новый ключ: {encryption_key}")
        print("📝 Добавьте в .env файл: ENCRYPTION_KEY=" + encryption_key)
        return encryption_key, Fernet(encryption_key.encode())
    
    # Проверяем корректность существующего ключа
    try:
        cipher = Fernet(encryption_key.encode())
        print("✅ Ключ шифрования загружен успешно")
        return encryption_key, cipher
    except Exception as e:
        print(f"❌ Некорректный ключ шифрования: {e}")
        print("🔄 Генерирую новый корректный ключ...")
        encryption_key = Fernet.generate_key().decode()
        cipher = Fernet(encryption_key.encode())
        print(f"✅ Новый ключ: {encryption_key}")
        print("📝 Обновите .env файл: ENCRYPTION_KEY=" + encryption_key)
        return encryption_key, cipher

# Инициализируем шифрование
ENCRYPTION_KEY, cipher = init_encryption()

# === КОНСТАНТЫ INSTAGRAM ===
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 5))
DELAY_BETWEEN_ATTEMPTS = int(os.getenv("DELAY_BETWEEN_ATTEMPTS", 420))  # 7 минут
CAPTCHA_TIMEOUT = int(os.getenv("CAPTCHA_TIMEOUT", 1800))  # 30 минут
MAX_REQUESTS_PER_HOUR = int(os.getenv("MAX_REQUESTS_PER_HOUR", 200))
MAX_ACTIVE_SCENARIOS = int(os.getenv("MAX_ACTIVE_SCENARIOS", 2))
MIN_ACTION_DELAY = int(os.getenv("MIN_ACTION_DELAY", 15))
MAX_ACTION_DELAY = int(os.getenv("MAX_ACTION_DELAY", 30))

# === КОНСТАНТЫ ПРОКСИ ===
PROXY_CHECK_TIMEOUT = 10
PROXY_CHECK_URL = "http://httpbin.org/ip"
PROXY_RECHECK_INTERVAL = 30

# === КОНСТАНТЫ УЛУЧШЕННОЙ АВТОРИЗАЦИИ ===
FAST_RETRY_DELAY = int(os.getenv("FAST_RETRY_DELAY", 120))
MAX_FAST_ATTEMPTS = int(os.getenv("MAX_FAST_ATTEMPTS", 3))
SLOW_RETRY_DELAY = int(os.getenv("SLOW_RETRY_DELAY", 420))

# Таймауты для разных типов проверок
CHALLENGE_TIMEOUT = int(os.getenv("CHALLENGE_TIMEOUT", 1800))
SMS_CODE_TIMEOUT = int(os.getenv("SMS_CODE_TIMEOUT", 300))
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", 600))

# Интерактивные возможности
ENABLE_SMS_INPUT = os.getenv("ENABLE_SMS_INPUT", "true").lower() == "true"
ENABLE_QUICK_RETRY = os.getenv("ENABLE_QUICK_RETRY", "true").lower() == "true"
ENABLE_AUTO_PROXY_SWITCH = os.getenv("ENABLE_AUTO_PROXY_SWITCH", "true").lower() == "true"
ENABLE_SAFE_MODE = os.getenv("ENABLE_SAFE_MODE", "true").lower() == "true"

# TikTok настройки
ENABLE_TIKTOK = os.getenv("ENABLE_TIKTOK", "true").lower() == "true"
TIKTOK_MAX_COMMENTS = int(os.getenv("TIKTOK_MAX_COMMENTS", 50))
TIKTOK_MESSAGE_DELAY = int(os.getenv("TIKTOK_MESSAGE_DELAY", 30))

# === ДЕТЕКТОР ТИПОВ ПРОВЕРОК ===
CHALLENGE_DETECTION = {
    'phone_keywords': ['phone', 'sms', 'mobile', 'текст', 'смс'],
    'email_keywords': ['email', 'mail', 'почта', 'письмо'],
    'device_keywords': ['device', 'устройство', 'телефон', 'приложение'],
    'photo_keywords': ['photo', 'selfie', 'фото', 'селфи', 'снимок']
}

# === АНТИДЕТЕКТ УЛУЧШЕНИЯ ===
RANDOM_DELAYS = {
    'before_login': (3, 8),
    'after_challenge': (5, 15),
    'between_attempts': (2, 5),
}

# === НАСТРОЙКИ УВЕДОМЛЕНИЙ ===
AUTH_NOTIFICATIONS = {
    'send_progress': True,
    'send_challenges': True,
    'send_success': True,
    'send_failures': True,
}

# === СТАТИСТИКА И МОНИТОРИНГ ===
AUTH_MONITORING = {
    'track_attempts': True,
    'track_challenge_types': True,
    'track_proxy_performance': True,
    'auto_alert_threshold': 0.7,
}

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
instabots = {}
tasks = {}
captcha_confirmed = {}
auth_sessions = {}
auth_callbacks = {}
sms_codes = {}

# TikTok переменные
tiktok_sessions = {}
tiktok_tasks = {}

# === НАСТРОЙКИ АНТИДЕТЕКТ ===
INSTAGRAM_USER_AGENTS = [
    "Instagram 219.0.0.12.117 Android",
    "Instagram 250.0.0.16.109 Android",
    "Instagram 243.0.0.15.119 Android"
]

DEVICE_SETTINGS = [
    {
        'manufacturer': 'Samsung',
        'model': 'SM-G973F',
        'android_version': 29,
        'android_release': '10'
    },
    {
        'manufacturer': 'Xiaomi',
        'model': 'Mi 10',
        'android_version': 30,
        'android_release': '11'
    },
    {
        'manufacturer': 'OnePlus',
        'model': 'OnePlus 8',
        'android_version': 29,
        'android_release': '10'
    }
]

print("✅ Конфигурация загружена успешно")