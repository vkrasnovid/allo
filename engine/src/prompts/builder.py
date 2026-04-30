"""Prompt builder — composes system prompt from base + blocks + context."""

import json
import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ===== Base System Prompt =====

BASE_SYSTEM_PROMPT = """Ты — голосовой AI-секретарь компании "{business_name}".
Твоя задача — записывать клиентов на услуги через телефонный разговор.

## Фундаментальные правила
1. Ты говоришь ПО-РУССКИ. Всегда. Даже если клиент пытается говорить на другом языке.
2. Ты НИКОГДА не выдумываешь данные. Все имена, цены, время берутся ТОЛЬКО из результатов вызова tools.
3. Если ты не уверена — переспроси. Не додумывай.
4. Ты говоришь коротко, естественно, как живой человек. Используй "ага", "минутку", "сейчас посмотрю".
5. Никаких причастий и деепричастных оборотов. Никаких канцеляризмов. Разговорный русский язык.

## Стиль общения
- Короткие фразы (2-4 слова максимум на вопрос)
- Дружелюбно, но профессионально
- Если нужно уточнить — спроси одним вопросом, не перечисляй варианты
- Подтверждай действие: "Записала вас к Анне на завтра в 14:00"
- Не повторяй информацию, которую клиент уже сказал

## Правило "Просто спросить"
Если клиент явно не хочет записываться (сказал "нет, спасибо", "я просто спросить", "позже", "может быть"):
1. Ответь кратко на его вопрос (если был вопрос)
2. Скажи: "Я записала, если передумаете — перезвоните. Всего доброго!"
3. Скажи "До свидания!"
НИКАКИХ попыток уговорить. Никаких "может всё-таки запишем". Никаких additional offers.

## Правило эскалации
Если клиент выражает недовольство, жалуется, хамит:
1. Скажи: "Извините, сейчас соединю вас с администратором"
2. Запиши причину в escalate tool
3. Вызови escalate_to_human()

## Инструменты
Ты можешь использовать следующие инструменты. Вызывай их, когда нужны данные.
НЕ ВЫДУМЫВАЙ результаты. Если инструмент вернул ошибку — сообщи клиенту что-то пошло не так.

## Длительность звонка
Старайся не затягивать. Типичная запись: 30-60 секунд.
Не рассказывай про акции и доп. услуги, если клиент не спросил.
"""


class PromptBlock:
    """A single configurable prompt block."""
    def __init__(self, key: str, content: str, position: int = 0):
        self.key = key
        self.content = content
        self.position = position


class ClientContext:
    """Client info injected into the prompt."""
    def __init__(
        self,
        name: Optional[str] = None,
        total_visits: int = 0,
        last_visit_at: Optional[str] = None,
        preferred_master_name: Optional[str] = None,
        preferred_services: Optional[list[str]] = None,
    ):
        self.name = name
        self.total_visits = total_visits
        self.last_visit_at = last_visit_at
        self.preferred_master_name = preferred_master_name
        self.preferred_services = preferred_services or []


def build_system_prompt(
    business_name: str = "Салон красоты",
    blocks: Optional[list[PromptBlock]] = None,
    client_context: Optional[ClientContext] = None,
) -> str:
    """
    Build the final system prompt from base + configurable blocks + client context.
    """
    prompt = BASE_SYSTEM_PROMPT.replace("{business_name}", business_name)

    if blocks:
        for block in sorted(blocks, key=lambda b: b.position):
            prompt += f"\n\n## {block.key.upper()}\n{block.content}"

    if client_context:
        context_lines = ["\n\n## КОНТЕКСТ КЛИЕНТА"]
        if client_context.name:
            context_lines.append(f"Имя: {client_context.name}")
        context_lines.append(f"Всего визитов: {client_context.total_visits}")
        if client_context.last_visit_at:
            context_lines.append(f"Последний визит: {client_context.last_visit_at}")
        if client_context.preferred_master_name:
            context_lines.append(f"Предпочитаемый мастер: {client_context.preferred_master_name}")
        if client_context.preferred_services:
            context_lines.append(f"Предпочитаемые услуги: {', '.join(client_context.preferred_services)}")
        prompt += "\n".join(context_lines)

    return prompt


def build_tool_definitions() -> list[dict]:
    """
    Build tool definitions for LLM function calling.
    These are derived from the shared tools library.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_services",
                "description": "Получить список услуг салона с ценами. Вызови в начале, чтобы показать клиенту что есть.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Фильтр по категории: стрижки, окрашивание, маникюр, педикюр, уход",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_masters",
                "description": "Получить список мастеров. Можно отфильтровать по услуге.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_id": {
                            "type": "string",
                            "description": "ID услуги — показать только мастеров, которые делают эту услугу",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "find_slots",
                "description": "Найти свободные временные слоты на определённую дату.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "master_id": {
                            "type": "string",
                            "description": "ID мастера (если не указан — все мастера)",
                        },
                        "service_id": {
                            "type": "string",
                            "description": "ID услуги",
                        },
                        "date": {
                            "type": "string",
                            "description": "Дата в формате YYYY-MM-DD",
                        },
                    },
                    "required": ["date"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_booking",
                "description": "Создать запись клиента на услугу. Вызови, когда клиент согласился на время и мастера.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_phone": {"type": "string", "description": "Номер телефона клиента в формате +7..."},
                        "client_name": {"type": "string", "description": "Имя клиента"},
                        "master_id": {"type": "string", "description": "ID мастера"},
                        "service_id": {"type": "string", "description": "ID услуги"},
                        "start_at": {"type": "string", "description": "Дата и время начала в ISO 8601"},
                        "comment": {"type": "string", "description": "Комментарий клиента"},
                    },
                    "required": ["client_phone", "client_name", "master_id", "service_id", "start_at"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "find_booking",
                "description": "Найти существующие записи клиента по номеру телефона. Используй при переносе/отмене/повторном звонке.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_phone": {"type": "string", "description": "Номер телефона клиента"},
                        "status": {"type": "string", "description": "Фильтр по статусу"},
                        "limit": {"type": "integer", "description": "Максимум записей"},
                    },
                    "required": ["client_phone"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_booking",
                "description": "Перенести или изменить существующую запись.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {"type": "string", "description": "ID существующей записи"},
                        "action": {"type": "string", "description": "reschedule | update_service | update_master"},
                        "new_start_at": {"type": "string", "description": "Новое время начала"},
                        "new_master_id": {"type": "string", "description": "Новый мастер"},
                        "reason": {"type": "string", "description": "Причина изменения"},
                    },
                    "required": ["booking_id", "action"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "cancel_booking",
                "description": "Отменить запись клиента.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {"type": "string", "description": "ID записи для отмены"},
                        "reason": {"type": "string", "description": "Причина: client_request | no_show | other"},
                        "comment": {"type": "string", "description": "Комментарий"},
                    },
                    "required": ["booking_id", "reason"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_business_info",
                "description": "Получить информацию о салоне (адрес, часы работы).",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "escalate_to_human",
                "description": "Перевести звонок на администратора. Используй при жалобах, агрессии или сложных запросах.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "call_id": {"type": "string", "description": "ID звонка"},
                        "reason": {"type": "string", "description": "Причина эскалации"},
                        "client_summary": {"type": "string", "description": "Описание ситуации"},
                    },
                    "required": ["call_id", "reason"],
                },
            },
        },
    ]
