from __future__ import annotations

import holidays

from app.calendar_common import save_json


YEARS = [2026, 2027, 2028]


def generate_holidays() -> None:
    print("Generating KR/JP holiday data...")
    holiday_data: dict[str, dict[str, str]] = {}

    for date_value, name in holidays.KR(years=YEARS).items():
        date_key = date_value.strftime("%Y-%m-%d")
        holiday_data.setdefault(date_key, {"kr": "", "jp": ""})["kr"] = name

    for date_value, name in holidays.JP(years=YEARS).items():
        date_key = date_value.strftime("%Y-%m-%d")
        holiday_data.setdefault(date_key, {"kr": "", "jp": ""})["jp"] = name

    save_json("holidays.json", holiday_data)
    print(f"Saved holidays.json with {len(holiday_data)} dates.")


if __name__ == "__main__":
    generate_holidays()
