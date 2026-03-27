from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from playwright.sync_api import sync_playwright

from app.calendar_common import find_matching_brand, load_json, save_json


TICKET_URL = "https://asobiticket2.asobistore.jp/booths"
DEADLINE_PATTERN = re.compile(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2}:\d{2})")


def parse_deadline(value: str) -> str:
    matches = DEADLINE_PATTERN.findall(value or "")
    if not matches:
        return (value or "").strip()
    year, month, day, hour_minute = matches[-1]
    return f"{year}-{int(month):02d}-{int(day):02d} {hour_minute}"


def find_open_booth_indexes(page: Any) -> list[int]:
    indexes: list[int] = []
    for index, booth in enumerate(page.locator("tpl-booth-overview").all()):
        if "\u53d7\u4ed8\u4e2d" in booth.inner_text():
            indexes.append(index)
    return indexes


def extract_receptions(page: Any, current_url: str, detected_brand: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []

    for reception in page.locator("tpl-reception-item").all():
        title_element = reception.locator(".reception-info-title")
        time_element = reception.locator("div[slot='content']")
        if title_element.count() == 0 or time_element.count() == 0:
            continue

        description_element = reception.locator(".reception-info-description")
        main_title = title_element.first.inner_text().strip()
        sub_title = description_element.first.inner_text().strip() if description_element.count() else ""
        deadline_text = time_element.first.inner_text().strip()

        entries.append(
            {
                "main_title": main_title,
                "phase_title": f"{main_title} {sub_title}".strip(),
                "deadline": parse_deadline(deadline_text),
                "description": current_url,
                "brand": detected_brand,
            }
        )

    return entries


def crawl_ticket_deadlines() -> None:
    print("Collecting ticket application deadlines...")
    official_schedules = load_json("schedule_data.json", [])
    grouped: defaultdict[str, list[dict[str, str]]] = defaultdict(list)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(TICKET_URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        for booth_index in find_open_booth_indexes(page):
            page.goto(TICKET_URL, wait_until="networkidle")
            page.wait_for_timeout(1500)

            booth = page.locator("tpl-booth-overview").all()[booth_index]
            live_title = booth.locator(".booth-title").inner_text().strip()
            detected_brand = find_matching_brand(live_title, official_schedules)
            booth.click()

            try:
                page.wait_for_selector("tpl-reception-item", timeout=10_000)
            except Exception:
                continue

            for reception in extract_receptions(page, page.url, detected_brand):
                grouped[reception["main_title"]].append(
                    {
                        "phase_title": reception["phase_title"],
                        "deadline": reception["deadline"],
                        "description": reception["description"],
                        "brand": reception["brand"],
                    }
                )

        browser.close()

    result = []
    for live_name, applications in grouped.items():
        applications.sort(key=lambda item: item["deadline"])
        result.append(
            {
                "live_name": live_name,
                "brand": applications[0]["brand"] if applications else "\uae30\ud0c0",
                "applications": applications,
            }
        )

    result.sort(key=lambda item: item["applications"][0]["deadline"] if item["applications"] else "")
    save_json("ticket_grouped_data.json", result)
    print(f"Saved ticket_grouped_data.json with {len(result)} groups.")


if __name__ == "__main__":
    crawl_ticket_deadlines()
