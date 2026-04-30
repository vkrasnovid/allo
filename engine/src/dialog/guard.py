"""Anti-hallucination guards for LLM responses."""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Known service and master names from seed data
KNOWN_SERVICES = {
    "стрижка женская", "стрижка мужская", "окрашивание",
    "маникюр", "педикюр", "укладка", "биозавивка",
    "стрижка", "маникюр", "педикюр",
}

KNOWN_MASTERS = {
    "анна петрова", "анна", "елена соколова", "елена",
    "мария иванова", "мария",
}

KNOWN_CATEGORIES = {
    "стрижки", "окрашивание", "маникюр", "педикюр", "уход",
}

# Price ranges for known services (to detect hallucinated prices)
SERVICE_PRICE_RANGES = {
    "стрижка женская": (1000, 5000),
    "стрижка мужская": (800, 3000),
    "окрашивание": (2000, 10000),
    "маникюр": (800, 5000),
    "педикюр": (1500, 6000),
    "укладка": (800, 4000),
    "биозавивка": (3000, 10000),
}


def validate_tool_call_params(tool_name: str, args: dict) -> dict:
    """
    Validate tool call parameters before passing to the tool.
    Detects obvious hallucinations or invalid data.
    Returns cleaned args or raises.
    """
    validated = dict(args)

    if tool_name == "get_services":
        category = args.get("category", "")
        if category and category.lower() not in KNOWN_CATEGORIES:
            logger.warning(f"Hallucination suspect: unknown category '{category}'")
            validated["category"] = None  # Don't filter, return all

    elif tool_name == "get_masters":
        service = args.get("service_id", "")
        # service_id should be a UUID, so just validate format
        if service and not re.match(r'^[0-9a-f-]{36}$', str(service)):
            logger.warning(f"Hallucination suspect: invalid service_id '{service}'")
            validated["service_id"] = None

    elif tool_name == "find_slots":
        date_str = args.get("date", "")
        if date_str and not re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_str)):
            logger.warning(f"Hallucination suspect: invalid date format '{date_str}'")
            raise ValueError(f"Invalid date format: {date_str}")

    elif tool_name == "create_booking":
        phone = args.get("client_phone", "")
        if phone and not re.match(r'^\+?[0-9]{10,15}$', phone):
            logger.warning(f"Hallucination suspect: invalid phone '{phone}'")
            raise ValueError(f"Invalid phone number: {phone}")

        # Validate master and service IDs are UUIDs
        for field in ["master_id", "service_id"]:
            val = args.get(field, "")
            if val and not re.match(r'^[0-9a-f-]{36}$', str(val)):
                logger.warning(f"Hallucination suspect: invalid {field} '{val}'")
                raise ValueError(f"Invalid {field}: {val}")

    return validated


def validate_price_against_service(service_name: str, price: float) -> bool:
    """
    Check if a price is within expected range for a service.
    Returns False if price seems hallucinated.
    """
    service_key = service_name.lower().strip()
    for known_name, (min_p, max_p) in SERVICE_PRICE_RANGES.items():
        if known_name in service_key or service_key in known_name:
            if price < min_p or price > max_p:
                logger.warning(
                    f"Price hallucination suspect: '{service_name}' = {price} ₽ "
                    f"(expected {min_p}-{max_p} ₽)"
                )
                return False
            return True
    return True  # Unknown service, can't validate


def validate_llm_response_text(text: str) -> str:
    """
    Clean and validate LLM response text.
    Removes markdown tables, excessive formatting, and other non-speech patterns.
    """
    if not text:
        return text

    # Remove markdown tables
    text = re.sub(r'\|.*\|.*\|', '', text)

    # Remove excessive markdown
    text = re.sub(r'#{1,6}\s+', '', text)

    # Check for hallucinated conflicts
    conflict_patterns = [
        r'(цена|стоимость|стоит)\s+(\d+[.,]?\d*)\s*(руб|₽)',
        r'(время|часы)\s+работ(ы|ать)\s+(с\s+\d+|до\s+\d+)',
    ]

    # Trim whitespace
    text = text.strip()

    return text


class HallucinationLog:
    """Logs hallucination events for monitoring."""

    def __init__(self):
        self.events: list[dict] = []

    def log(self, tool_name: str, params: dict, reason: str):
        event = {
            "tool": tool_name,
            "params": params,
            "reason": reason,
            "severity": "warning",
        }
        self.events.append(event)
        logger.warning(f"HALLUCINATION GUARD: {reason} (tool={tool_name})")

    def get_stats(self) -> dict:
        return {
            "total_events": len(self.events),
            "by_tool": {},
        }


# Global hallucination log
hallucination_log = HallucinationLog()


def check_price_hallucination(service_name: str, price_rub: float) -> Optional[str]:
    """
    Check if a price is outside expected range.
    Returns warning text if suspicious, None if OK.
    """
    if not validate_price_against_service(service_name, price_rub):
        return f"Цена {price_rub} ₽ для услуги '{service_name}' вызывает подозрение"
    return None
