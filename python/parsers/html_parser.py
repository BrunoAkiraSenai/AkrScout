from bs4 import BeautifulSoup
from typing import List, Dict, Optional


def parse_html(content: str) -> BeautifulSoup:
    return BeautifulSoup(content, "lxml")


def extract_json_from_script(soup: BeautifulSoup, script_id: Optional[str] = None) -> Optional[Dict]:
    import json

    scripts = soup.find_all("script", type="application/json")
    if script_id:
        scripts = [s for s in scripts if s.get("id") == script_id]

    for script in scripts:
        try:
            return json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def extract_text(element) -> Optional[str]:
    if element is None:
        return None
    return element.get_text(strip=True)


def extract_links(element, selector: str = "a") -> List[str]:
    return [
        a.get("href", "")
        for a in element.select(selector)
        if a.get("href")
    ]
