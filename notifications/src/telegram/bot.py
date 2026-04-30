"""
Telegram Bot — Алло голосовой секретарь.

Команды:
  /start     — Приветствие с inline-клавиатурой
  /status    — Статус системы и сегодняшняя статистика
  /bookings  — Записи на сегодня
  /settings  — Быстрые настройки уведомлений
  /help      — Справка

Анти-спам: максимум 1 сообщение в 30 секунд на пользователя.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from .templates import (
    welcome_text,
    status_text,
    bookings_text,
    help_text,
    settings_text,
    booking_notification,
    escalation_notification,
    daily_summary,
    settings_toggle_on,
    settings_toggle_off,
)

logger = logging.getLogger(__name__)

# ─── Anti-spam ────────────────────────────────────────────────────────────────

_last_message: dict[int, float] = {}  # user_id -> timestamp


def _check_spam(user_id: int) -> bool:
    """Возвращает True, если пользователь нарушил анти-спам."""
    now = asyncio.get_event_loop().time()
    last = _last_message.get(user_id, 0.0)
    if now - last < 30.0:
        return True
    _last_message[user_id] = now
    return False


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _moscow_now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


async def _fetch_bookings_for_today() -> list[dict]:
    """
    Заглушка для получения записей на сегодня.
    В реальном боте заменяется на запрос к Booking Service API.
    """
    return []


async def _fetch_today_stats() -> dict:
    """
    Заглушка для получения статистики.
    В реальном боте заменяется на запрос к Booking Service API.
    """
    return {
        "calls": 0,
        "bookings": 0,
        "escalations": 0,
        "answer_rate": 0,
    }


async def _fetch_settings(chat_id: int) -> dict:
    """Заглушка для получения настроек уведомлений."""
    return {
        "notify_new_bookings": True,
        "notify_escalations": True,
        "daily_summary": True,
    }


# ─── Handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start — приветствие."""
    user = update.effective_user
    if not user or _check_spam(user.id):
        return

    keyboard = [
        [
            InlineKeyboardButton("📊 Статус", callback_data="status"),
            InlineKeyboardButton("📅 Записи", callback_data="bookings"),
        ],
        [
            InlineKeyboardButton("📞 Звонки", callback_data="calls"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text(user.first_name or "друг"),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /status — статистика за сегодня."""
    user = update.effective_user
    if not user or _check_spam(user.id):
        return

    stats = await _fetch_today_stats()
    await update.message.reply_text(
        status_text(
            calls=stats["calls"],
            bookings=stats["bookings"],
            escalations=stats["escalations"],
            answer_rate=stats["answer_rate"],
        ),
        parse_mode="Markdown",
    )


async def bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /bookings — записи на сегодня."""
    user = update.effective_user
    if not user or _check_spam(user.id):
        return

    today_bookings = await _fetch_bookings_for_today()

    keyboard = None
    if len(today_bookings) > 5:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Все записи", url=(
                context.bot_data.get("admin_url", "")
            ))],
        ])

    await update.message.reply_text(
        bookings_text(today_bookings),
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /settings — настройки уведомлений."""
    user = update.effective_user
    if not user or _check_spam(user.id):
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    prefs = await _fetch_settings(chat_id)

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if prefs['notify_new_bookings'] else '❌'} Новые записи",
                callback_data="toggle_bookings",
            ),
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if prefs['notify_escalations'] else '❌'} Эскалации",
                callback_data="toggle_escalations",
            ),
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if prefs['daily_summary'] else '❌'} Дневная сводка",
                callback_data="toggle_summary",
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        settings_text(),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help — справка."""
    user = update.effective_user
    if not user or _check_spam(user.id):
        return

    await update.message.reply_text(
        help_text(),
        parse_mode="Markdown",
    )


# ─── Callback Query Handler ───────────────────────────────────────────────────

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на inline-кнопки."""
    query = update.callback_query
    if not query or not query.data:
        return

    user = query.from_user
    if user and _check_spam(user.id):
        await query.answer("Слишком часто! Подождите немного.")
        return

    await query.answer()

    if query.data == "status":
        stats = await _fetch_today_stats()
        await query.edit_message_text(
            status_text(
                calls=stats["calls"],
                bookings=stats["bookings"],
                escalations=stats["escalations"],
                answer_rate=stats["answer_rate"],
            ),
            parse_mode="Markdown",
        )

    elif query.data == "bookings":
        today = await _fetch_bookings_for_today()
        keyboard = None
        if len(today) > 5:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Все записи", url=(
                    context.bot_data.get("admin_url", "")
                ))],
            ])
        await query.edit_message_text(
            bookings_text(today),
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif query.data == "calls":
        await query.edit_message_text(
            "📞 Последние звонки — скоро появится в админ-панели.",
            parse_mode="Markdown",
        )

    elif query.data == "settings":
        chat_id = update.effective_chat.id if update.effective_chat else 0
        prefs = await _fetch_settings(chat_id)
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✅' if prefs['notify_new_bookings'] else '❌'} Новые записи",
                    callback_data="toggle_bookings",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if prefs['notify_escalations'] else '❌'} Эскалации",
                    callback_data="toggle_escalations",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if prefs['daily_summary'] else '❌'} Дневная сводка",
                    callback_data="toggle_summary",
                ),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            settings_text(),
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    elif query.data == "help":
        await query.edit_message_text(
            help_text(),
            parse_mode="Markdown",
        )

    elif query.data.startswith("toggle_"):
        # Toggle notification preference
        key_map = {
            "toggle_bookings": "notify_new_bookings",
            "toggle_escalations": "notify_escalations",
            "toggle_summary": "daily_summary",
        }
        pref_key = key_map.get(query.data)
        if pref_key:
            now_val = context.user_data.get(pref_key, True)
            context.user_data[pref_key] = not now_val
            new_val = not now_val

            await query.edit_message_text(
                settings_toggle_on(pref_key) if new_val else settings_toggle_off(pref_key),
                parse_mode="Markdown",
            )


# ─── Application factory ──────────────────────────────────────────────────────

def create_bot(token: str, admin_url: str = "") -> Application:
    """
    Создаёт и настраивает Telegram Bot Application.

    Args:
        token: Токен Telegram бота (из переменной TELEGRAM_BOT_TOKEN).
        admin_url: URL админ-панели для кнопок-ссылок.

    Returns:
        Готовый к запуску Application.
    """
    application = Application.builder().token(token).build()

    # Сохраняем URL админки в bot_data для доступа из хендлеров
    application.bot_data["admin_url"] = admin_url

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("bookings", bookings))
    application.add_handler(CommandHandler("settings", settings_cmd))
    application.add_handler(CommandHandler("help", help_cmd))

    # Регистрируем обработчик inline-кнопок
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Telegram bot handlers registered")
    return application
