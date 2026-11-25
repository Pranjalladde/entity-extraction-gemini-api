from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


def normalize_entity_value(value: Any) -> str:
    """Normalize case, whitespace and punctuation before comparing values."""
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


def compare_documents(
    pdf1_entities: list[dict[str, Any]],
    pdf2_entities: list[dict[str, Any]],
    fuzzy_threshold: float = 0.88,
) -> list[dict[str, Any]]:
    """Compare extracted values across documents.

    Returns exact matches, high-similarity candidates, unmatched PDF 1 values,
    and values present only in PDF 2. Similarity is a text signal, not proof of
    identity or shipment equivalence.
    """
    if not 0 <= fuzzy_threshold <= 1:
        raise ValueError("fuzzy_threshold must be between 0 and 1.")

    right = []
    for row in pdf2_entities:
        value = str(row.get("Entity Value", "")).strip()
        normalized = normalize_entity_value(value)
        if normalized:
            right.append((row, value, normalized))

    used_right: set[int] = set()
    results: list[dict[str, Any]] = []

    for left in pdf1_entities:
        left_value = str(left.get("Entity Value", "")).strip()
        left_normalized = normalize_entity_value(left_value)
        if not left_normalized:
            continue

        candidate_list = []
        for index, (right_row, right_value, right_normalized) in enumerate(right):
            score = SequenceMatcher(
                None, left_normalized, right_normalized
            ).ratio()
            if score >= fuzzy_threshold:
                candidate_list.append((score, index, right_row, right_value))

        if not candidate_list:
            results.append({
                "PDF 1 Entity Type": left.get("Entity Type", ""),
                "PDF 1 Value": left_value,
                "PDF 2 Entity Type": "",
                "PDF 2 Value": "",
                "Match Result": "No match",
                "Similarity (%)": 0.0,
            })
            continue

        candidate_list.sort(key=lambda item: item[0], reverse=True)
        score, index, right_row, right_value = candidate_list[0]
        used_right.add(index)

        exact = left_normalized == normalize_entity_value(right_value)
        results.append({
            "PDF 1 Entity Type": left.get("Entity Type", ""),
            "PDF 1 Value": left_value,
            "PDF 2 Entity Type": right_row.get("Entity Type", ""),
            "PDF 2 Value": right_value,
            "Match Result": "Exact match" if exact else "Similar candidate",
            "Similarity (%)": round(score * 100, 2),
        })

    for index, (right_row, right_value, _) in enumerate(right):
        if index not in used_right:
            results.append({
                "PDF 1 Entity Type": "",
                "PDF 1 Value": "",
                "PDF 2 Entity Type": right_row.get("Entity Type", ""),
                "PDF 2 Value": right_value,
                "Match Result": "Only in PDF 2",
                "Similarity (%)": 0.0,
            })

    return results
