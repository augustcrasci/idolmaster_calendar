from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from app.calendar_common import load_json, save_json
from app.get_holidays import generate_holidays
from app.idolbd import crawl_birthdays
from app.imasportal_year import crawl_official_schedule
from app.ticketing import crawl_ticket_deadlines


ProgressCallback = Callable[[str, str], None]
UPDATE_STEPS: list[tuple[str, Callable[[], None]]] = [
    ('공식 일정 업데이트 중...', crawl_official_schedule),
    ('생일 데이터 업데이트 중...', crawl_birthdays),
    ('티켓 데이터 업데이트 중...', crawl_ticket_deadlines),
    ('휴일 데이터 업데이트 중...', generate_holidays),
]


def extract_sort_date(raw_value: str) -> str:
    text = str(raw_value or '').strip()
    if not text:
        return ''
    digits = []
    token = ''
    for char in text:
        if char.isdigit() or char == ':':
            token += char
        elif token:
            digits.append(token)
            token = ''
    if token:
        digits.append(token)
    if len(digits) >= 3:
        year, month, day = digits[0], digits[1], digits[2]
        time_value = digits[3] if len(digits) >= 4 and ':' in digits[3] else '99:99'
        return f'{int(year):04d}-{int(month):02d}-{int(day):02d} {time_value}'
    return text


def normalize_schedule_items(items: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for item in items:
        title = str(item.get('title') or '').strip()
        link = str(item.get('link') or '').strip()
        date_text = str(item.get('date') or '').strip()
        key = f'{title}|{link}'
        normalized[key] = {
            'source': 'schedule',
            'section': '공식 일정',
            'brand': str(item.get('brand') or '기타'),
            'title': title,
            'date': date_text,
            'link': link,
            'sort_date': extract_sort_date(date_text),
        }
    return normalized


def normalize_ticket_items(groups: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for group in groups:
        brand = str(group.get('brand') or '기타')
        live_name = str(group.get('live_name') or '').strip()
        for application in group.get('applications', []):
            phase_title = str(application.get('phase_title') or live_name).strip()
            link = str(application.get('description') or '').strip()
            deadline = str(application.get('deadline') or '').strip()
            key = f'{phase_title}|{link}'
            normalized[key] = {
                'source': 'ticket',
                'section': '티켓',
                'brand': str(application.get('brand') or brand),
                'title': phase_title,
                'date': deadline,
                'link': link,
                'sort_date': extract_sort_date(deadline),
            }
    return normalized


def normalize_birthday_items(items: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for date_key, idols in items.items():
        for idol in idols:
            name = str(idol.get('name') or '').strip()
            brand = str(idol.get('brand') or '기타')
            title = f'생일 {name}'
            key = f'{title}|{brand}'
            normalized[key] = {
                'source': 'birthday',
                'section': '생일',
                'brand': brand,
                'title': title,
                'date': str(date_key),
                'link': '',
                'sort_date': str(date_key),
            }
    return normalized


def capture_sources() -> dict[str, dict[str, dict[str, str]]]:
    return {
        'schedule': normalize_schedule_items(load_json('schedule_data.json', [])),
        'ticket': normalize_ticket_items(load_json('ticket_grouped_data.json', [])),
        'birthday': normalize_birthday_items(load_json('birthday_data.json', {})),
    }


def compare_source(
    before_items: dict[str, dict[str, str]],
    after_items: dict[str, dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    added = [after_items[key] for key in after_items.keys() - before_items.keys()]
    removed = [before_items[key] for key in before_items.keys() - after_items.keys()]
    changed: list[dict[str, Any]] = []

    for key in before_items.keys() & after_items.keys():
        before_entry = before_items[key]
        after_entry = after_items[key]
        if any(before_entry.get(field) != after_entry.get(field) for field in ('brand', 'title', 'date', 'link')):
            changed.append({'before': before_entry, 'after': after_entry})

    added.sort(key=lambda item: item.get('sort_date') or item.get('date') or '')
    removed.sort(key=lambda item: item.get('sort_date') or item.get('date') or '')
    changed.sort(key=lambda item: item['after'].get('sort_date') or item['after'].get('date') or '')
    return {'added': added, 'removed': removed, 'changed': changed}



def build_change_summary(
    before_state: dict[str, dict[str, dict[str, str]]],
    after_state: dict[str, dict[str, dict[str, str]]],
) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    combined_added: list[dict[str, str]] = []

    for source_name in ('schedule', 'ticket', 'birthday'):
        diff = compare_source(before_state.get(source_name, {}), after_state.get(source_name, {}))
        sources[source_name] = diff
        combined_added.extend(diff['added'])

    combined_added.sort(key=lambda item: item.get('sort_date') or item.get('date') or '')
    summary = {
        'added': sum(len(value['added']) for value in sources.values()),
        'removed': sum(len(value['removed']) for value in sources.values()),
        'changed': sum(len(value['changed']) for value in sources.values()),
    }
    return {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': summary,
        'recent_added': combined_added[-60:],
        'sources': sources,
    }



def main(progress_callback: ProgressCallback | None = None) -> None:
    before_state = capture_sources()
    total = len(UPDATE_STEPS)

    for index, (label, func) in enumerate(UPDATE_STEPS, start=1):
        if progress_callback:
            progress_callback('업데이트 중입니다.', f'{index}/{total} {label}')
        func()

    after_state = capture_sources()
    save_json('change_summary.json', build_change_summary(before_state, after_state))


if __name__ == '__main__':
    main()
