/**
 * Telegram Bot Plugin — OpenClaw plugin for sending Telegram notifications.
 *
 * TELEGRAM_BOT_TOKEN should be set via environment.
 * Uses Telegram Bot API directly via fetch (no client library needed).
 */

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const API_BASE = `https://api.telegram.org/bot${BOT_TOKEN}`;

interface TelegramButton {
  text: string;
  url?: string;
  callback_data?: string;
}

interface TelegramMessageResult {
  ok: boolean;
  result?: { message_id: number };
  description?: string;
}

async function sendTelegram(
  chatId: string,
  text: string,
  buttons?: TelegramButton[][],
  parseMode: 'Markdown' | 'HTML' = 'Markdown',
): Promise<TelegramMessageResult> {
  if (!BOT_TOKEN) {
    console.warn('[TelegramPlugin] TELEGRAM_BOT_TOKEN not set — skipping message');
    return { ok: false, description: 'Missing TELEGRAM_BOT_TOKEN' };
  }

  const payload: Record<string, unknown> = {
    chat_id: chatId,
    text,
    parse_mode: parseMode,
    disable_web_page_preview: true,
  };

  if (buttons && buttons.length > 0) {
    payload.reply_markup = {
      inline_keyboard: buttons,
    };
  }

  const res = await fetch(`${API_BASE}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  return res.json() as Promise<TelegramMessageResult>;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Отправить уведомление о новой записи владельцу салона.
 */
export async function notifyNewBooking(
  chatId: string,
  clientName: string,
  serviceName: string,
  masterName: string,
  dateTime: string,
  price: string,
): Promise<TelegramMessageResult> {
  const text = [
    '✅ *Новая запись!*',
    '',
    `👤 ${clientName}`,
    `💇 ${serviceName}`,
    `✂️ ${masterName}`,
    `🕐 ${dateTime}`,
    `💰 ${price} ₽`,
  ].join('\n');

  const buttons: TelegramButton[][] = [
    [{ text: '📋 Посмотреть в админке', url: process.env.ADMIN_PANEL_URL || '' }],
  ];

  return sendTelegram(chatId, text, buttons);
}

/**
 * Отправить уведомление об эскалации звонка.
 */
export async function notifyEscalation(
  chatId: string,
  clientPhone: string,
  reason: string,
  duration: string,
  callDetailUrl?: string,
): Promise<TelegramMessageResult> {
  const text = [
    '⚠️ *Звонок переведён на вас*',
    '',
    `📞 Клиент: \`${clientPhone}\``,
    `❓ Причина: ${reason}`,
    `⏱ Длительность: ${duration}`,
  ].join('\n');

  const buttons: TelegramButton[][] = [
    [
      { text: '📞 Позвонить клиенту', callback_data: `call_back_${clientPhone}` },
    ],
  ];

  if (callDetailUrl) {
    buttons.push([
      { text: '🎧 Прослушать запись', url: callDetailUrl },
    ]);
  }

  return sendTelegram(chatId, text, buttons);
}

/**
 * Отправить ежедневную сводку.
 */
export async function sendDailySummary(
  chatId: string,
  callsCount: number,
  bookingsCount: number,
  escalationsCount: number,
  answerRate: string,
  tomorrowBookings: number,
): Promise<TelegramMessageResult> {
  const text = [
    '📊 *Итоги дня*',
    '',
    `📞 Принято звонков: ${callsCount}`,
    `✂️ Записалось: ${bookingsCount} (${answerRate}%)`,
    `⚠️ На вашем контроле: ${escalationsCount}`,
    `📅 Завтра записей: ${tomorrowBookings}`,
    '',
    'Спокойной ночи! 🌙',
  ].join('\n');

  const buttons: TelegramButton[][] = [
    [{ text: '📊 Открыть дашборд', url: process.env.ADMIN_PANEL_URL || '' }],
  ];

  return sendTelegram(chatId, text, buttons);
}
