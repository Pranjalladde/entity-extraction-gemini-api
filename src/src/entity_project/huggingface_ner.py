from __future__ import annotations

import os
from typing import Any

from .pdf_utils import chunk_text


DEFAULT_HF_MODEL = "dslim/bert-base-NER"


def load_huggingface_ner(model_name: str | None = None):
    """Load a pretrained Hugging Face BERT token-classification pipeline.

    This is inference with a public pretrained checkpoint. It is not a reproduction
    of a custom fine-tuning run; a custom checkpoint can be supplied through
    HF_NER_MODEL when available.
    """
    selected_model = model_name or os.getenv("HF_NER_MODEL", DEFAULT_HF_MODEL)
    token = os.getenv("HF_TOKEN") or None

    try:
        from transformers import pipeline
    except ImportError as exc:
        raise ImportError(
            "Transformers is missing. Run: pip install -r requirements.txt"
        ) from exc

    return pipeline(
        task="token-classification",
        model=selected_model,
        tokenizer=selected_model,
        aggregation_strategy="simple",
        token=token,
    )


def extract_ner_from_pages(
    document_name: str,
    pages: list[dict[str, Any]],
    ner_pipeline: Any | None = None,
    model_name: str | None = None,
) -> list[dict[str, Any]]:
    """Extract general NER entities from PDF pages with Hugging Face."""
    if ner_pipeline is None:
        ner_pipeline = load_huggingface_ner(model_name)

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for page in pages:
        chunks = chunk_text(page["text"])
        for chunk_number, chunk in enumerate(chunks, start=1):
            predictions = ner_pipeline(chunk)

            for item in predictions:
                entity_value = str(item.get("word", "")).strip()
                entity_type = str(
                    item.get("entity_group") or item.get("entity") or "UNKNOWN"
                ).upper()

                if not entity_value:
                    continue

                dedupe_key = (entity_type, entity_value.casefold())
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                rows.append({
                    "Document": document_name,
                    "Page": page["page"],
                    "Chunk": chunk_number,
                    "Entity Type": entity_type,
                    "Entity Value": entity_value,
                    "Confidence": round(float(item.get("score", 0.0)), 4),
                    "Source": "Hugging Face",
                })

    return rows
