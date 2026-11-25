from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def export_workbook(
    pdf1_entities: list[dict[str, Any]],
    pdf2_entities: list[dict[str, Any]],
    huggingface_entities: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Export extraction and matching outputs to a four-sheet Excel workbook."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    gemini_columns = [
        "Document", "Page", "Block", "Entity Type", "Entity Value", "Source"
    ]
    hf_columns = [
        "Document", "Page", "Chunk", "Entity Type",
        "Entity Value", "Confidence", "Source"
    ]
    compare_columns = [
        "PDF 1 Entity Type", "PDF 1 Value", "PDF 2 Entity Type",
        "PDF 2 Value", "Match Result", "Similarity (%)"
    ]

    with pd.ExcelWriter(destination, engine="openpyxl") as writer:
        pd.DataFrame(pdf1_entities, columns=gemini_columns).to_excel(
            writer, sheet_name="PDF 1 - Gemini", index=False
        )
        pd.DataFrame(pdf2_entities, columns=gemini_columns).to_excel(
            writer, sheet_name="PDF 2 - Gemini", index=False
        )
        pd.DataFrame(huggingface_entities, columns=hf_columns).to_excel(
            writer, sheet_name="Hugging Face NER", index=False
        )
        pd.DataFrame(comparison_rows, columns=compare_columns).to_excel(
            writer, sheet_name="Entity Matching", index=False
        )

    return destination
