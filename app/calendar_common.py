from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
@dataclass(frozen=True)
class BrandInfo:
    canonical: str
    aliases: tuple[str, ...]


BRANDS: tuple[BrandInfo, ...] = (
    BrandInfo("765PRO", ("765PRO", "ALLSTARS", "ASOBISTAGE", "MILLION&ALLSTARS")),
    BrandInfo("\uc2e0\ub370\ub810\ub77c \uac78\uc988", ("CINDERELLA", "DERESUTE", "CG")),
    BrandInfo("\ubc00\ub9ac\uc5b8 \ub77c\uc774\ube0c", ("MILLION", "MILLIONLIVE", "MLTD")),
    BrandInfo("SideM", ("SIDEM", "315")),
    BrandInfo("\uc0e4\uc774\ub2c8 \uceec\ub7ec\uc988", ("SHINYCOLORS", "SHINY", "283PRODUCTION")),
    BrandInfo("\ud559\uc6d0\ub9c8\uc2a4", ("GAKUMAS",)),
    BrandInfo("876PRO", ("876PRO", "876")),
)


def data_path(filename: str) -> Path:
    return DATA_DIR / filename


def load_json(filename: str, default: Any) -> Any:
    path = data_path(filename)
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def save_json(filename: str, payload: Any) -> None:
    path = data_path(filename)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def normalize_text(value: str) -> str:
    return re.sub(r"[\s\W_]+", "", (value or "")).upper()


def infer_brand(*values: str) -> str:
    normalized_values = [normalize_text(value) for value in values if value]
    if not normalized_values:
        return "\uae30\ud0c0"

    for brand in BRANDS:
        aliases = [normalize_text(brand.canonical), *(normalize_text(alias) for alias in brand.aliases)]
        for source in normalized_values:
            if any(alias and alias in source for alias in aliases):
                return brand.canonical
    return "\uae30\ud0c0"


def infer_brand_candidates(*values: str) -> list[str]:
    normalized_values = [normalize_text(value) for value in values if value]
    matches: list[str] = []
    if not normalized_values:
        return matches

    for brand in BRANDS:
        aliases = [normalize_text(brand.canonical), *(normalize_text(alias) for alias in brand.aliases)]
        for source in normalized_values:
            if any(alias and alias in source for alias in aliases):
                matches.append(brand.canonical)
                break
    return matches


def find_matching_brand(title: str, schedule_items: Iterable[dict[str, Any]]) -> str:
    normalized_title = normalize_text(title)
    if not normalized_title:
        return "\uae30\ud0c0"

    for item in schedule_items:
        schedule_title = normalize_text(str(item.get("title", "")))
        if not schedule_title:
            continue
        if normalized_title in schedule_title or schedule_title in normalized_title:
            return str(item.get("brand") or "\uae30\ud0c0")
    return infer_brand(title)
