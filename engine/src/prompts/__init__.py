"""
The `touch` call overwrote this file. Here's the restoration:

Prompt Management Service.
CRUD for prompt profiles and blocks.
Composes final system prompts from base + tenant-specific blocks.
"""

from typing import Optional

from shared.models.prompts import (
    ComposedPrompt,
    PromptBlock,
    PromptProfile,
)

# Base system prompt template
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
НИКАКИХ попыток уговорить. Никаких "может всё-таки запишем".

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


class PromptManager:
    """Manages prompt profiles and composes system prompts."""

    def __init__(self, booking_api_url: str):
        self.booking_api_url = booking_api_url.rstrip("/")
        self._profiles_cache: dict[str, dict] = {}

    def compose_prompt(
        self,
        profile: PromptProfile,
        business_name: str = "Салон красоты",
        client_context: Optional[dict] = None,
    ) -> ComposedPrompt:
        """Compose final system prompt from base + configurable blocks + client context."""
        prompt = BASE_SYSTEM_PROMPT.replace("{business_name}", business_name)

        blocks_used = []
        for block in sorted(profile.blocks, key=lambda b: b.position):
            if block.is_active:
                prompt += f"\n\n## {block.block_key.upper()}\n{block.content}"
                blocks_used.append(block.block_key)

        if client_context:
            ctx = client_context
            prompt += f"""
## КОНТЕКСТ КЛИЕНТА
Имя: {ctx.get('name', 'не указано')}
Всего визитов: {ctx.get('total_visits', 0)}
Последний визит: {ctx.get('last_visit_at', 'нет данных')}
Предпочитаемый мастер: {ctx.get('preferred_master', 'не указан')}
Предпочитаемые услуги: {', '.join(ctx.get('preferred_services', [])) or 'не указаны'}
"""

        return ComposedPrompt(
            system_prompt=prompt.strip(),
            blocks_used=blocks_used,
            client_context=client_context,
        )

    async def get_profile(self, tenant_id: str) -> Optional[PromptProfile]:
        """Fetch active prompt profile for a tenant from the booking service."""
        return self._get_default_profile(tenant_id)

    def _get_default_profile(self, tenant_id: str) -> PromptProfile:
        """Return a default prompt profile for development/testing."""
        from uuid import UUID
        return PromptProfile(
            id=UUID(int=1),
            tenant_id=UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
            name="beauty_salon_default",
            is_active=True,
            blocks=[
                PromptBlock(
                    id=UUID(int=2), profile_id=UUID(int=1),
                    block_key="greeting",
                    content="Здравствуйте! Чем могу помочь?",
                    position=1, is_active=True,
                ),
                PromptBlock(
                    id=UUID(int=3), profile_id=UUID(int=1),
                    block_key="tone",
                    content="Ты общаешься дружелюбно, но без панибратства. Обращайся на «Вы».",
                    position=2, is_active=True,
                ),
                PromptBlock(
                    id=UUID(int=4), profile_id=UUID(int=1),
                    block_key="farewell",
                    content="Всего доброго! Если что-то изменится — перезвоните.",
                    position=3, is_active=True,
                ),
            ],
        )
