"""Mock dialog scenarios for testing conversation flows."""

import pytest
from uuid import uuid4


# ===== Mock dialog: Booking flow =====

BOOKING_FLOW = [
    # (role, text, expected_tool)
    ("user", "Здравствуйте, хочу записаться на стрижку", "get_services"),
    ("assistant", "У нас есть женская стрижка за 2500 ₽ и мужская за 1500 ₽. Какая вас интересует?", None),
    ("user", "Женскую, пожалуйста", "get_masters"),
    ("assistant", "Это может сделать Анна или Мария. К кому хотите?", None),
    ("user", "К Анне", "find_slots"),
    ("assistant", "На завтра есть свободное время в 14:00 и 16:00. Вам какое удобно?", None),
    ("user", "В 14:00", "create_booking"),
    ("assistant", "Записала вас к Анне на завтра в 14:00. Всего доброго!", None),
]

# ===== Mock dialog: Just asking =====

JUST_ASKING_FLOW = [
    ("user", "Здравствуйте, подскажите, вы работаете в воскресенье?", "get_business_info"),
    ("assistant", "Да, работаем с 10:00 до 18:00. Хотите записаться?", None),
    ("user", "Нет, спасибо, я просто спросить", None),
    ("assistant", "Я записала, если передумаете — перезвоните. Всего доброго!", None),
]

# ===== Mock dialog: Reschedule =====

RESCHEDULE_FLOW = [
    ("user", "Здравствуйте, мне нужно перенести запись", "find_booking"),
    ("assistant", "У вас есть запись на стрижку к Анне, 15 апреля в 14:00. Хотите её перенести?", None),
    ("user", "Да, на 1 мая, тоже в 14:00", "find_slots"),
    ("assistant", "На 1 мая в 14:00 есть свободное время. Переношу?", None),
    ("user", "Да", "update_booking"),
    ("assistant", "Перенесла вашу запись на 1 мая в 14:00. Всего доброго!", None),
]

# ===== Mock dialog: Cancel =====

CANCEL_FLOW = [
    ("user", "Здравствуйте, хочу отменить запись", "find_booking"),
    ("assistant", "У вас есть запись на стрижку к Анне, 1 мая в 14:00. Отменить её?", None),
    ("user", "Да, пожалуйста", "cancel_booking"),
    ("assistant", "Отменила запись. Если передумаете — перезвоните. Всего доброго!", None),
]

# ===== Mock dialog: Escalation =====

ESCALATION_FLOW = [
    ("user", "Вы ужасный сервис, я недовольна!", None),
    ("assistant", "Извините, сейчас соединю вас с администратором", "escalate_to_human"),
]


class TestMockDialogs:

    def check_flow(self, flow: list[tuple]):
        """Verify dialog structure is valid."""
        for i, (role, text, expected_tool) in enumerate(flow):
            assert role in ("user", "assistant")
            assert isinstance(text, str)
            assert len(text) > 0
            if expected_tool:
                assert expected_tool in [
                    "get_services", "get_masters", "find_slots",
                    "create_booking", "find_booking", "update_booking",
                    "cancel_booking", "get_business_info", "escalate_to_human",
                ]

    def test_booking_flow_structure(self):
        self.check_flow(BOOKING_FLOW)
        # Verify the flow has final confirmation
        assert any("Записала" in step[1] for step in BOOKING_FLOW)

    def test_just_asking_flow_structure(self):
        self.check_flow(JUST_ASKING_FLOW)
        # Verify no booking tool is called
        assert not any(step[2] == "create_booking" for step in JUST_ASKING_FLOW if step[2])

    def test_reschedule_flow_structure(self):
        self.check_flow(RESCHEDULE_FLOW)
        # Verify update_booking is called
        assert any(step[2] == "update_booking" for step in RESCHEDULE_FLOW if step[2])

    def test_cancel_flow_structure(self):
        self.check_flow(CANCEL_FLOW)
        # Verify cancel_booking is called
        assert any(step[2] == "cancel_booking" for step in CANCEL_FLOW if step[2])

    def test_escalation_flow_structure(self):
        self.check_flow(ESCALATION_FLOW)
        # Verify escalate is called
        assert any(step[2] == "escalate_to_human" for step in ESCALATION_FLOW if step[2])

    def test_dialog_length(self):
        """Dialogs should be reasonable length (not too many turns)."""
        for flow in [BOOKING_FLOW, JUST_ASKING_FLOW, RESCHEDULE_FLOW, CANCEL_FLOW, ESCALATION_FLOW]:
            assert 2 <= len(flow) <= 10, f"Dialog has {len(flow)} turns"

    def test_no_hallucinated_prices(self):
        """Prices in dialogs should be reasonable."""
        import re
        for flow in [BOOKING_FLOW, JUST_ASKING_FLOW, RESCHEDULE_FLOW, CANCEL_FLOW, ESCALATION_FLOW]:
            for _, text, _ in flow:
                prices = re.findall(r'(\d+)\s*(?:₽|руб)', text)
                for price in prices:
                    val = int(price)
                    assert 100 <= val <= 20000, f"Price {val} outside reasonable range"
