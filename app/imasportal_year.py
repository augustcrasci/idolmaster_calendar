from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from playwright.sync_api import Page, sync_playwright

from app.calendar_common import infer_brand_candidates, save_json


BASE_URL = "https://idolmaster-official.jp"
CATEGORY_KEYWORDS = (
    "\u30e9\u30a4\u30d6",
    "\u30a4\u30d9\u30f3\u30c8",
    "\u30e9\u30b8\u30aa",
    "\u914d\u4fe1",
    "\u30b0\u30c3\u30ba",
    "\u30b3\u30e9\u30dc",
    "\u30ad\u30e3\u30f3\u30da\u30fc\u30f3",
)
BRAND_PATH_SIGNATURES = {
    "M31.54,14.47c1": "765PRO",
    "M18.55,19.49c.16": "\uc2e0\ub370\ub810\ub77c \uac78\uc988",
    "M28.27,13.16c2.07": "\ubc00\ub9ac\uc5b8 \ub77c\uc774\ube0c",
    "M25.96,9.67c1.06": "\uc0e4\uc774\ub2c8 \uceec\ub7ec\uc988",
    "M35.52,9.47c": "SideM",
    "M20.65,4.57c0-": "\ud559\uc6d0\ub9c8\uc2a4",
    "m24.54,24.81c-": "876PRO",
}


@dataclass(frozen=True)
class MonthTarget:
    year: int
    month: int

    @property
    def iso_month(self) -> str:
        return f"{self.year}-{self.month:02d}"


def add_months(base: date, offset: int) -> MonthTarget:
    year = base.year + ((base.month - 1 + offset) // 12)
    month = ((base.month - 1 + offset) % 12) + 1
    return MonthTarget(year=year, month=month)


def build_month_targets(month_count: int = 12) -> list[MonthTarget]:
    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    return [add_months(first_of_month, offset) for offset in range(month_count)]


def infer_ongoing_start_year(start_month: int, start_day: int, end_month: int, end_day: int, target: MonthTarget) -> int:
    today = date.today()
    candidate_years = [today.year - 1, today.year, target.year - 1, target.year]

    for year in dict.fromkeys(candidate_years):
        start_date = date(year, start_month, start_day)
        end_year = year + 1 if (end_month, end_day) < (start_month, start_day) else year
        end_date = date(end_year, end_month, end_day)
        if start_date <= today <= end_date:
            return year

    if start_month < target.month:
        return target.year + 1
    return target.year


def extract_brand_names(item: Any) -> str:
    brands: set[str] = set()
    for path in item.locator("svg path").all():
        signature = path.get_attribute("d") or ""
        for prefix, brand in BRAND_PATH_SIGNATURES.items():
            if signature.startswith(prefix):
                brands.add(brand)
    return ", ".join(sorted(brands)) if brands else "\uae30\ud0c0"


def resolve_brand(raw_brand: str, title: str, category: str, link: str) -> str:
    detected = [brand.strip() for brand in raw_brand.split(",") if brand.strip()]
    inferred = infer_brand_candidates(title, category, link)

    if len(detected) <= 1:
        return detected[0] if detected else "\uae30\ud0c0"

    for brand in inferred:
        if brand in detected:
            return brand

    return ", ".join(detected)


def normalize_link(href: str | None) -> str:
    if not href:
        return ""
    return href if href.startswith("http") else f"{BASE_URL}{href}"


def build_date_string(date_id: str | None, time_text: str, target: MonthTarget) -> str:
    if date_id:
        return date_id.replace("schedule_list_", "")

    full_range_match = re.search(r"(\d{1,2})/(\d{1,2})\s*[~\u301c\uff5e]\s*(\d{1,2})/(\d{1,2})", time_text)
    if full_range_match:
        start_month, start_day, end_month, end_day = map(int, full_range_match.groups())
        start_year = infer_ongoing_start_year(start_month, start_day, end_month, end_day, target)
        return f"{start_year}-{start_month:02d}-{start_day:02d} Ongoing"

    range_match = re.search(r"(\d{1,2})/(\d{1,2})\s*[~\u301c\uff5e]", time_text)
    if range_match:
        start_month, start_day = map(int, range_match.groups())
        year = target.year + (1 if start_month < target.month else 0)
        return f"{year}-{start_month:02d}-{start_day:02d} Ongoing"

    if re.search(r"\d{1,2}[:\uff1a]\d{2}", time_text):
        today = date.today()
        return today.strftime("%Y-%m-%d")

    return f"{target.year}-{target.month:02d}-01 Ongoing"


def extract_schedule_item(item: Any, target: MonthTarget) -> dict[str, str] | None:
    category = ", ".join(item.locator('li[class*="style_category"]').all_inner_texts()).strip()
    if not any(keyword in category for keyword in CATEGORY_KEYWORDS):
        return None

    title_link = item.locator('a[class*="style_title_link"]')
    if title_link.count() == 0:
        return None

    date_id = item.evaluate(
        """el => {
            const parent = el.closest('li[id^="schedule_list_"]');
            return parent ? parent.id : null;
        }"""
    )
    time_label = item.locator('p[class*="style_head_dsdate"]')
    time_text = time_label.inner_text().strip() if time_label.count() else ""

    raw_brand = extract_brand_names(item)
    title = title_link.inner_text().strip()
    link = normalize_link(title_link.get_attribute("href"))

    return {
        "brand": resolve_brand(raw_brand, title, category, link),
        "category": category,
        "title": title,
        "date": f"{build_date_string(date_id, time_text, target)} {time_text}".strip(),
        "link": link,
    }


def open_all_ongoing_sections(page: Page) -> None:
    buttons = page.locator('button:has-text("\u5b9f\u65bd\u4e2d\u306e\u30a4\u30d9\u30f3\u30c8")').all()
    for button in buttons:
        if not button.is_visible():
            continue
        try:
            button.click()
            page.wait_for_timeout(250)
        except Exception:
            continue


def go_to_next_month(page: Page) -> bool:
    clicked = page.evaluate(
        """() => {
            const buttons = Array.from(document.querySelectorAll('button.style_controller__n3mRj'));
            const nextButton = buttons.find(button => button.querySelector('div[data-type="right"]'));
            if (!nextButton) return false;
            nextButton.click();
            return true;
        }"""
    )
    if clicked:
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(250)
    return bool(clicked)


def crawl_official_schedule() -> None:
    print("Collecting official portal schedules...")
    collected: list[dict[str, str]] = []
    targets = build_month_targets(12)
    start_url = f"{BASE_URL}/schedule?date={targets[0].iso_month}"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(start_url, wait_until="networkidle")

        for index, target in enumerate(targets):
            try:
                page.wait_for_selector(f"li[id*='{target.iso_month}-']", timeout=10_000)
            except Exception:
                pass

            open_all_ongoing_sections(page)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(300)

            items = page.locator('div[class*="style_article"]').all()
            month_items = [entry for entry in (extract_schedule_item(item, target) for item in items) if entry]
            collected.extend(month_items)
            print(f"Collected {len(month_items)} items for {target.iso_month}.")

            if index != len(targets) - 1 and not go_to_next_month(page):
                break

        browser.close()

    unique_items = list({f"{item['title']}|{item['date']}|{item['link']}": item for item in collected}.values())
    unique_items.sort(key=lambda item: item["date"])
    save_json("schedule_data.json", unique_items)
    print(f"Saved schedule_data.json with {len(unique_items)} items.")


if __name__ == "__main__":
    crawl_official_schedule()
