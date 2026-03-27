from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from app.calendar_common import save_json


BIRTHDAY_URL = "https://imas-db.jp/calendar/birthdays.html"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
DATE_PATTERN = re.compile(r"^\d{1,2}/\d{1,2}$")


def fetch_html(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def find_section_date(section: Tag) -> str | None:
    for candidate in section.previous_elements:
        if isinstance(candidate, NavigableString):
            text = candidate.strip()
            if DATE_PATTERN.match(text):
                return text
        elif isinstance(candidate, Tag):
            text = candidate.get_text(" ", strip=True)
            if DATE_PATTERN.match(text):
                return text
    return None


def parse_birthdays(html: str) -> dict[str, list[dict[str, str]]]:
    soup = BeautifulSoup(html, "html.parser")
    birthdays: dict[str, list[dict[str, str]]] = {}

    for section in soup.select("ul.list-unstyled"):
        date_key = find_section_date(section)
        if not date_key:
            continue

        idols = []
        for item in section.select("li"):
            name_element = item.select_one(".idol-name")
            if not name_element:
                continue
            brand_element = item.select_one(".badge")
            idols.append(
                {
                    "name": name_element.get_text(strip=True),
                    "brand": brand_element.get_text(strip=True) if brand_element else "\uae30\ud0c0",
                }
            )

        if idols:
            birthdays.setdefault(date_key, []).extend(idols)

    return birthdays


def crawl_birthdays() -> None:
    print("Collecting birthday data from imas-db...")
    birthday_data = parse_birthdays(fetch_html(BIRTHDAY_URL))
    save_json("birthday_data.json", birthday_data)
    print(f"Saved birthday_data.json with {len(birthday_data)} dates.")


if __name__ == "__main__":
    crawl_birthdays()
