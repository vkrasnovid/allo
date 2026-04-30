"""
Шаблоны сообщений Telegram-бота Алло.

Все тексты на русском языке, в соответствии с тоном коммуникации.
Используют Markdown-форматирование для Telegram.
"""

from typing import Optional


# ===== /start — Приветствие =====

def welcome_text(first_name: str) -> str:
    return (
        f"👋 Привет, *{first_name}*!\n\n"
        "Я *Алло*, голосовой секретарь твоего салона.\n"
        "Принимаю звонки, записываю клиентов, ничего не забываю.\n\n"
        "Вот что я умею:\n"
        "📊 /status — статус и статистика за сегодня\n"
        "📅 /bookings — записи на сегодня\n"
        "📞 /calls — последние звонки\n"
        "⚙️ /settings — настроить уведомления\n"
        "❓ /help — справка\n\n"
        "Если что-то срочное — просто напиши! 🏪"
    )


# ===== /status — Статистика =====

def status_text(
    calls: int,
    bookings: int,
    escalations: int,
    answer_rate: int,
) -> str:
    status_icon = "🟢"  # позже может быть динамическим

    return (
        f"{status_icon} *Алло активен*\n\n"
        f"📊 *Статистика за сегодня:*\n"
        f"📞 Принято звонков: *{calls}*\n"
        f"✂️ Записалось: *{bookings}* ({answer_rate}%)\n"
        f"⚠️ На контроле: *{escalations}*\n\n"
        "Всё идёт по плану! 👌"
    )


# ===== /bookings — Записи =====

def bookings_text(bookings: list[dict]) -> str:
    if not bookings:
        return (
            "📅 *Записи на сегодня*\n\n"
            "Записей пока нет. Клиенты ещё не записались через Алло.\n"
            "Как только появится первая запись, я пришлю уведомление 🤝"
        )

    lines = ["📅 *Записи на сегодня*\n"]
    for b in bookings[:5]:
        status_icons = {
            "confirmed": "🟢",
            "pending": "🟡",
            "cancelled": "🔴",
            "completed": "⚪",
        }
        icon = status_icons.get(b.get("status", ""), "🟡")
        lines.append(
            f"{icon} *{b.get('client_name', 'Клиент')}* — {b.get('start_at', '')}\n"
            f"   {b.get('service_name', '')} · {b.get('master_name', '')}"
        )

    if len(bookings) > 5:
        lines.append(f"\n…и ещё {len(bookings) - 5} запись.")

    return "\n".join(lines)


# ===== Уведомление о новой записи =====

def booking_notification(
    client_name: str,
    service_name: str,
    master_name: str,
    date_time: str,
    price: str,
) -> str:
    return (
        "✅ *Новая запись!*\n\n"
        f"👤 *{client_name}*\n"
        f"💇 {service_name}\n"
        f"✂️ Мастер: {master_name}\n"
        f"🕐 {date_time}\n"
        f"💰 {price} ₽\n\n"
        "Всё под контролем! 👌"
    )


# ===== Уведомление об эскалации =====

def escalation_notification(
    client_phone: str,
    reason: str,
    duration: str,
    summary: Optional[str] = None,
) -> str:
    lines = [
        "⚠️ *Звонок переведён на вас*\n",
        f"📞 Клиент: `{client_phone}`",
        f"❓ Причина: {reason}",
        f"⏱ Длительность: {duration}",
    ]

    if summary:
        lines.append(f"\n📝 {summary}")

    lines.append("\n_Прослушайте запись в админке, чтобы понять ситуацию._")
    return "\n".join(lines)


# ===== Ежедневная сводка =====

def daily_summary(
    calls: int,
    bookings: int,
    answer_rate: int,
    escalations: int,
    tomorrow_bookings: int,
) -> str:
    return (
        "📊 *Итоги дня*\n\n"
        f"📞 Принято звонков: *{calls}*\n"
        f"✂️ Записалось: *{bookings}* ({answer_rate}%)\n"
        f"⚠️ На вашем контроле: *{escalations}*\n"
        f"📅 Завтра записей: *{tomorrow_bookings}*\n\n"
        "Спокойной ночи! 🌙"
    )


# ===== /settings — Настройки =====

def settings_text() -> str:
    return (
        "⚙️ *Настройки уведомлений*\n\n"
        "Выбери, о чём присылать уведомления:\n\n"
        "— *Новые записи* — когда клиент записался через Алло\n"
        "— *Эскалации* — когда звонок переведён на тебя\n"
        "— *Дневная сводка* — итоги дня в 21:00\n\n"
        "Нажми на кнопку, чтобы включить или выключить. 👇"
    )


def settings_toggle_on(key: str) -> str:
    names = {
        "notify_new_bookings": "Новые записи",
        "notify_escalations": "Эскалации",
        "daily_summary": "Дневная сводка",
    }
    name = names.get(key, key)
    return f"✅ *{name}* включены! Я буду присылать уведомления."


def settings_toggle_off(key: str) -> str:
    names = {
        "notify_new_bookings": "Новые записи",
        "notify_escalations": "Эскалации",
        "daily_summary": "Дневная сводка",
    }
    name = names.get(key, key)
    return f"❌ *{name}* выключены. Не буду беспокоить."


# ===== /help — Справка =====

def help_text() -> str:
    return (
        "❓ *Помощь по Алло*\n\n"
        "Я — голосовой секретарь твоего салона красоты.\n"
        "Принимаю звонки, записываю клиентов и присылаю уведомления сюда.\n\n"
        "*Команды:*\n"
        "🔹 /start — приветствие и главное меню\n"
        "🔹 /status — статистика за сегодня\n"
        "🔹 /bookings — записи на сегодня\n"
        "🔹 /calls — последние звонки\n"
        "🔹 /settings — быстрые настройки\n"
        "🔹 /help — этот текст\n\n"
        "*Не нашли нужное?*\n"
        "Полная админ-панель доступна в веб-версии. "
        "Там можно посмотреть детали звонков, "
        "изменить записи и настроить приветствие.\n\n"
        "Если что-то срочное — напиши мне, я передам разработчикам! 🏪"
    )
