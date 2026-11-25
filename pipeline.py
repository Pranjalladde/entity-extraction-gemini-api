from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader

DEFAULT_ENTITY_FIELDS = [
    "VESSEL", "ETD BUSAN", "NO.&Date of Invoice",
    "Shipper/Exporter", "TOTAL CIF", "PURCHASE ORDER NO.",
]
DEFAULT_MODEL_NAME = "gemini-3.8-flash"
GENERATION_CONFIG = {
    "temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 2048,
}
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]


def configure_gemini(api_key: str | None = None) -> None:
    load_dotenv()
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError("GEMINI_API_KEY is missing. Put your own key in a local .env file.")
    genai.configure(api_key=key)


def create_model(model_name: str | None = None):
    selected = model_name or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL_NAME
    return genai.GenerativeModel(
        model_name=selected,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS,
    )


def load_pdf_pages(pdf_path: str | Path) -> list[dict[str, Any]]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF.")
    documents = PyPDFLoader(str(path)).load()
    pages = []
    for index, document in enumerate(documents, start=1):
        text = (document.page_content or "").strip()
        if text:
            page_no = int(document.metadata.get("page", index - 1)) + 1
            pages.append({"page": page_no, "text": text})
    if not pages:
        raise ValueError("No selectable text found. Scanned PDFs need OCR first.")
    return pages


def split_into_blocks(page_text: str) -> list[str]:
    blocks = [re.sub(r"[ \t]+", " ", b).strip() for b in re.split(r"\n\s*\n", page_text)]
    return [b for b in blocks if b]


def build_extraction_prompt(block: str, entity_fields: list[str]) -> str:
    fields = ", ".join(entity_fields)
    return (
        f"Extract these entities from the PDF text: {fields}.\n"
        "Return one entity per line in exactly this format: ENTITY NAME | extracted value.\n"
        "Use only information in the supplied text; do not guess. If absent, return ENTITY NAME | NOT FOUND. "
        "Preserve identifiers, dates, amounts, currencies and punctuation. Do not add Markdown or explanations.\n\n"
        f"PDF text:\n{block}"
    )


def parse_entity_response(response_text: str, entity_fields: list[str]) -> dict[str, str]:
    canonical = {field.casefold(): field for field in entity_fields}
    result = {field: "" for field in entity_fields}
    for raw in (response_text or "").splitlines():
        line = raw.replace("**", "").strip().lstrip("-• ").strip()
        if "|" not in line:
            continue
        left, value = line.split("|", 1)
        field = left.strip().strip("*").casefold()
        value = value.strip().strip("*")
        if field in canonical and value.casefold() not in {"not found", "not available", "n/a", "none"}:
            result[canonical[field]] = value
    return result


def extract_entities_from_pdf(
    pdf_path: str | Path,
    entity_fields: list[str] | None = None,
    model_name: str | None = None,
    api_key: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fields = entity_fields or DEFAULT_ENTITY_FIELDS
    if not fields or any(not f.strip() for f in fields):
        raise ValueError("At least one non-empty entity field is required.")
    configure_gemini(api_key)
    model = create_model(model_name)
    pages = load_pdf_pages(pdf_path)
    rows: list[dict[str, Any]] = []
    for page in pages:
        for block_no, block in enumerate(split_into_blocks(page["text"]), start=1):
            chat = model.start_chat(history=[])
            response = chat.send_message(build_extraction_prompt(block, fields))
            parsed = parse_entity_response(response.text or "", fields)
            for entity_type, entity_value in parsed.items():
                rows.append({"Page": page["page"], "Block": block_no,
                             "Entity Type": entity_type, "Entity Value": entity_value})
    page_df = pd.DataFrame(rows, columns=["Page", "Block", "Entity Type", "Entity Value"])
    summary_rows = []
    for field in fields:
        values = []
        if not page_df.empty:
            for value in page_df.loc[page_df["Entity Type"] == field, "Entity Value"].tolist():
                if value and value not in values:
                    values.append(value)
        summary_rows.append({"Entity Type": field, "Entity Value": " | ".join(values)})
    return pd.DataFrame(summary_rows), page_df


def export_to_excel(summary_df: pd.DataFrame, page_df: pd.DataFrame, output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(destination, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Entities from PDF", index=False)
        page_df.to_excel(writer, sheet_name="Page-wise Results", index=False)
    return destination
