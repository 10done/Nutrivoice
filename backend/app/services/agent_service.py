from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.config import Settings
from app.schemas.meal import MealItem, MealStructured, MealTotals
from app.services.nutrition_tools import NutritionFacts, _KNOWN, lookup_food, sum_totals

logger = logging.getLogger(__name__)

_FILLER_RE = re.compile(
    r"\b(i|i'd|i've|had|have|ate|eaten|just|also|some|the|a|an|of|for|my|"
    r"breakfast|lunch|dinner|snack|today|this morning|tonight|cup|bowl|plate|"
    r"glass|piece|pieces|slice|slices|large|medium|small|little)\b",
    re.I,
)


def _clean_transcript(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    for phrase in (
        "i had ",
        "i have ",
        "i've had ",
        "i ate ",
        "i eat ",
        "i just had ",
        "i just ate ",
        "today i had ",
        "for breakfast ",
        "for lunch ",
        "for dinner ",
        "for a snack ",
        "this morning ",
        "after my workout ",
        "after the gym ",
    ):
        t = t.replace(phrase, " ")
    return re.sub(r"\s+", " ", t).strip()


def _split_segments(t: str) -> list[str]:
    if not t:
        return []
    parts = re.split(r"\s*,\s*|\s+and\s+|\s+with\s+a\s+|\s+with\s+", t, flags=re.I)
    out = [p.strip() for p in parts if p and p.strip()]
    return out if out else [t]


_WORD_TO_N = {
    "a": 1,
    "an": 1,
    "one": 1,
    "single": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "half": 0.5,
}


def _quantity_from_segment(seg: str) -> tuple[float, str]:
    s = seg.strip().lower()
    m = re.match(r"^(\d+)\s+", s)
    if m:
        return float(int(m.group(1))), s[m.end() :].strip()
    m = re.match(r"^([a-z]+)\s+", s)
    if m and m.group(1) in _WORD_TO_N:
        return float(_WORD_TO_N[m.group(1)]), s[m.end() :].strip()
    return 1.0, s


def _longest_food_token(segment: str) -> str | None:
    """Return longest _KNOWN key (except default) contained in segment."""
    seg = segment.lower()
    best: str | None = None
    for token in sorted(_KNOWN.keys(), key=len, reverse=True):
        if token == "default":
            continue
        if token in seg:
            if best is None or len(token) > len(best):
                best = token
    return best


def _mock_structured_from_text(text: str) -> MealStructured:
    """Rule-based extraction + local nutrition table (MOCK_AI / no API key fallback)."""
    raw_lower = text.lower()
    cleaned = _clean_transcript(text)
    segments = _split_segments(cleaned)
    if not segments:
        segments = [cleaned] if cleaned else [text.strip()]

    items: list[MealItem] = []
    seen: set[tuple[str, float]] = set()
    unknown_chunks: list[str] = []

    for seg in segments:
        qty, rest = _quantity_from_segment(seg)
        lookup_source = rest if rest else seg
        token = _longest_food_token(lookup_source)

        if token:
            f = lookup_food(token, qty, "serving")
            display = token.title()
            sig = (token, round(qty, 2))
            if sig in seen:
                continue
            seen.add(sig)
            items.append(
                MealItem(
                    name=display,
                    quantity=qty,
                    unit="serving",
                    calories=f.calories,
                    protein_g=f.protein_g,
                    carbs_g=f.carbs_g,
                    fat_g=f.fat_g,
                )
            )
        else:
            chunk = _FILLER_RE.sub(" ", lookup_source)
            chunk = re.sub(r"\s+", " ", chunk).strip()
            if len(chunk) >= 2:
                unknown_chunks.append(chunk)

    needs_review = False
    if unknown_chunks:
        needs_review = True
        combined = ", ".join(unknown_chunks)[:120]
        f = lookup_food("meal", 1.0, "serving")
        items.append(
            MealItem(
                name=combined[:80] or "Unlisted foods",
                quantity=1,
                unit="meal",
                calories=f.calories,
                protein_g=f.protein_g,
                carbs_g=f.carbs_g,
                fat_g=f.fat_g,
            )
        )

    if not items:
        f = lookup_food("meal", 1.0, "serving")
        snippet = (text.strip()[:80] or "Meal")[:80]
        items.append(
            MealItem(
                name=snippet,
                quantity=1,
                unit="serving",
                calories=f.calories,
                protein_g=f.protein_g,
                carbs_g=f.carbs_g,
                fat_g=f.fat_g,
            )
        )
        needs_review = True

    facts = [NutritionFacts(i.calories, i.protein_g, i.carbs_g, i.fat_g) for i in items]
    t = sum_totals(facts)
    meal_type = (
        "breakfast"
        if "breakfast" in raw_lower
        else ("lunch" if "lunch" in raw_lower else ("dinner" if "dinner" in raw_lower else "snack"))
    )
    tags: list[str] = []
    if t.protein_g >= 25:
        tags.append("Protein Dense")

    return MealStructured(
        items=items,
        totals=MealTotals(calories=t.calories, protein_g=t.protein_g, carbs_g=t.carbs_g, fat_g=t.fat_g),
        meal_type=meal_type,
        tags=tags,
        needs_review=needs_review,
    )


def _groq_structured(text: str, settings: Settings) -> MealStructured:
    if not settings.groq_api_key or not settings.groq_api_key.strip():
        return _mock_structured_from_text(text)

    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    schema_hint = {
        "items": [
            {
                "name": "string",
                "quantity": 1,
                "unit": "string",
                "calories": 0,
                "protein_g": 0,
                "carbs_g": 0,
                "fat_g": 0,
            }
        ],
        "totals": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0},
        "meal_type": "breakfast|lunch|dinner|snack",
        "tags": ["string"],
        "needs_review": False,
    }
    user_msg = (
        f"User said: {text}\n"
        "Extract each food with realistic portion macros (approximate USDA-style values). "
        "Sum totals across items. "
        "Respond with ONLY a JSON object (no markdown) with keys: items, totals, meal_type, tags, needs_review. "
        f"Shape reference: {json.dumps(schema_hint)}"
    )
    kwargs = dict(
        model=settings.groq_model,
        messages=[
            {
                "role": "system",
                "content": "You are a nutrition logging assistant. Reply with JSON only, no code fences.",
            },
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )
    try:
        r = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
    except Exception:
        r = client.chat.completions.create(**kwargs)
    raw = (r.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data: dict[str, Any] = json.loads(raw)
    return MealStructured.model_validate(data)


def run_meal_agent(transcript: str, settings: Settings) -> MealStructured:
    if settings.mock_ai:
        return _mock_structured_from_text(transcript)
    try:
        return _groq_structured(transcript, settings)
    except Exception:
        logger.exception("Groq meal parsing failed; using rule-based fallback")
        return _mock_structured_from_text(transcript)


def title_from_structured(structured: MealStructured) -> str:
    if not structured.items:
        return "Meal"
    if len(structured.items) == 1:
        return structured.items[0].name.title()
    return " & ".join(i.name.title() for i in structured.items[:3])
