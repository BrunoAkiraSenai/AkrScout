import re
from datetime import datetime
from typing import Optional, Tuple


def parse_salary(text: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    if not text:
        return None, None

    text = text.replace(",", "").replace(" ", "")
    pattern = r"(?:USD|EUR|GBP|R\$)?\$?\s*(\d+(?:\.\d+)?)\s*(k|K|mil)?"
    matches = re.findall(pattern, text)

    values = []
    for amount, multiplier in matches:
        value = float(amount)
        if multiplier.lower() == "k":
            value *= 1000
        elif multiplier.lower() == "mil":
            value *= 1000
        values.append(value)

    if len(values) >= 2:
        return min(values), max(values)
    if len(values) == 1:
        return values[0], None
    return None, None


def parse_date(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%a %b %d %H:%M:%S %z %Y"):
        try:
            dt = datetime.strptime(text.replace("Z", "+0000"), fmt)
            return dt.isoformat()
        except (ValueError, AttributeError):
            continue

    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.isoformat()
    except (ValueError, AttributeError, TypeError):
        pass

    return None


def clean_html(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate(text: Optional[str], max_len: int = 5000) -> Optional[str]:
    if not text:
        return None
    return text[:max_len] if len(text) > max_len else text
