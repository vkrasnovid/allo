#!/usr/bin/env python3
"""Seed data for test beauty salon."""

import asyncio
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session_factory, get_engine
from src.models import Base, TenantORM, ServiceORM, MasterORM, MasterServiceORM, \
    ClientORM, PromptProfileORM, PromptBlockORM, NotificationSettingsORM, SipSettingsORM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

TEST_TENANT_ID = uuid4()


async def seed():
    engine = get_engine()
    factory = get_session_factory()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        # Check if already seeded
        result = await session.execute(
            select(TenantORM).where(TenantORM.slug == "elegant")
        )
        if result.scalar_one_or_none():
            logger.info("Seed data already exists, skipping")
            return

        # 1. Tenant
        tenant = TenantORM(
            id=TEST_TENANT_ID,
            name="Салон красоты Элегант",
            slug="elegant",
            phone="+74951234567",
            address="ул. Тверская, д. 15",
            description="Салон красоты премиум-класса в центре Москвы",
            timezone="Europe/Moscow",
            status="active",
        )
        session.add(tenant)

        # 2. Services
        services_data = [
            ("Стрижка женская", "Классическая стрижка любой длины", 60, 2500.00, "стрижки"),
            ("Стрижка мужская", "Мужская стрижка машинкой и ножницами", 40, 1500.00, "стрижки"),
            ("Окрашивание", "Окрашивание любой сложности", 120, 5000.00, "окрашивание"),
            ("Маникюр", "Классический маникюр с покрытием", 60, 2000.00, "маникюр"),
            ("Педикюр", "Аппаратный педикюр", 90, 3000.00, "педикюр"),
            ("Укладка", "Укладка феном", 40, 1800.00, "уход"),
            ("Биозавивка", "Биологическая завивка волос", 150, 5500.00, "окрашивание"),
        ]

        services = {}
        for name, desc, dur, price, category in services_data:
            svc = ServiceORM(
                tenant_id=tenant.id,
                name=name,
                description=desc,
                duration_min=dur,
                price_rub=price,
                category=category,
                is_active=True,
            )
            session.add(svc)
            services[name] = svc
            logger.info(f"  Service: {name} — {price} ₽")

        # 3. Masters
        masters_data = [
            ("Анна Петрова", "+79161111111", "Стрижки, окрашивание, укладка"),
            ("Елена Соколова", "+79162222222", "Маникюр, педикюр"),
            ("Мария Иванова", "+79163333333", "Стрижки, окрашивание, биозавивка"),
        ]

        masters = {}
        for name, phone, spec in masters_data:
            m = MasterORM(
                tenant_id=tenant.id,
                name=name,
                phone=phone,
                specialization=spec,
                is_active=True,
            )
            session.add(m)
            masters[name] = m
            logger.info(f"  Master: {name} — {spec}")

        await session.flush()

        # 4. Master-service links
        links = [
            (masters["Анна Петрова"], services["Стрижка женская"]),
            (masters["Анна Петрова"], services["Стрижка мужская"]),
            (masters["Анна Петрова"], services["Окрашивание"]),
            (masters["Анна Петрова"], services["Укладка"]),
            (masters["Елена Соколова"], services["Маникюр"]),
            (masters["Елена Соколова"], services["Педикюр"]),
            (masters["Мария Иванова"], services["Стрижка женская"]),
            (masters["Мария Иванова"], services["Окрашивание"]),
            (masters["Мария Иванова"], services["Биозавивка"]),
            (masters["Мария Иванова"], services["Укладка"]),
        ]
        for master, svc in links:
            link = MasterServiceORM(master_id=master.id, service_id=svc.id)
            session.add(link)

        # 5. Test clients
        test_client = ClientORM(
            tenant_id=tenant.id,
            phone="+79161234567",
            name="Мария Иванова",
            total_visits=3,
            preferences={"preferred_master": str(masters["Анна Петрова"].id)},
        )
        session.add(test_client)

        # 6. Prompt profile for beauty salon
        profile = PromptProfileORM(
            tenant_id=tenant.id,
            name="beauty_salon",
            is_active=True,
        )
        session.add(profile)
        await session.flush()

        prompt_blocks = [
            ("greeting", 'Салон красоты «Элегант», здравствуйте! Чем могу помочь?', 1),
            ("tone", "Ты общаешься дружелюбно, но без панибратства. Обращайся на «Вы».", 2),
            ("business_info",
             "Название: Салон красоты Элегант\n"
             "Адрес: ул. Тверская, д. 15\n"
             "Телефон: +74951234567\n"
             "Часы работы: Пн-Пт 09:00-21:00, Сб 10:00-20:00, Вс 10:00-18:00",
             3),
            ("rules",
             "Правила салона:\n"
             "- Отмена записи — за 2 часа\n"
             "- Опоздание более 15 минут — перенос\n"
             "- 152-ФЗ: обязательно скажи «В целях контроля качества наш разговор может быть записан» в начале",
             4),
            ("farewell",
             "Будем ждать вас в салоне! Если что-то изменится — перезвоните. Всего доброго!",
             5),
        ]
        for key, content, pos in prompt_blocks:
            block = PromptBlockORM(
                profile_id=profile.id,
                block_key=key,
                content=content,
                position=pos,
                is_active=True,
            )
            session.add(block)

        # 7. Notification settings
        notif = NotificationSettingsORM(
            tenant_id=tenant.id,
            sms_enabled=True,
            reminder_day=True,
            reminder_hour=True,
        )
        session.add(notif)

        # 8. SIP settings
        sip = SipSettingsORM(
            tenant_id=tenant.id,
            did="+74951234567",
            forward_number="+79991234567",
            is_active=True,
        )
        session.add(sip)

        await session.commit()
        logger.info(f"\n✅ Seed complete! Tenant ID: {tenant.id}")
        logger.info(f"   7 услуг, 3 мастера, 1 клиент")
        logger.info(f"   1 prompt profile (4 blocks)")
        logger.info(f"   1 notification settings, 1 sip settings")


if __name__ == "__main__":
    asyncio.run(seed())
