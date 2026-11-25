from __future__ import annotations

from pathlib import Path
from typing import Any

from .excel_export import export_workbook
from .gemini_extractor import extract_entities_from_pages
from .huggingface_ner import extract_ner_from_pages, load_huggingface_ner
from .matching import compare_documents
from .pdf_utils import load_pdf_pages


PDF1_DEFAULT_FIELDS = [
    "Booking No",
    "Address",
    "Order No",
    "Vessel name",
    "OBOL number",
    "Depart date",
    "Cutoff date",
    "Destination port",
    "Total ROLL Shipped",
    "Total Lots Shipped",
    "Total Containers",
    "CBM",
    "HTS Code",
]

PDF2_DEFAULT_FIELDS = [
    "Sea waybill no",
    "Voyage no",
    "Booking Ref",
    "Port of Discharge",
    "Date of issue",
    "Onboard date",
    "SCAC code",
]


def run_project(
    pdf1_path: str | Path,
    pdf2_path: str | Path,
    output_path: str | Path = "entity_extraction_comparison.xlsx",
    pdf1_fields: list[str] | None = None,
    pdf2_fields: list[str] | None = None,
    gemini_model: str | None = None,
    hf_model: str | None = None,
    ner_pipeline: Any | None = None,
) -> dict[str, Any]:
    """Extract entities from two PDFs, run NER, compare values, and export Excel."""
    pdf1_pages = load_pdf_pages(pdf1_path)
    pdf2_pages = load_pdf_pages(pdf2_path)

    fields1 = pdf1_fields or PDF1_DEFAULT_FIELDS
    fields2 = pdf2_fields or PDF2_DEFAULT_FIELDS

    pdf1_gemini = extract_entities_from_pages(
        Path(pdf1_path).name, pdf1_pages, fields1, model_name=gemini_model
    )
    pdf2_gemini = extract_entities_from_pages(
        Path(pdf2_path).name, pdf2_pages, fields2, model_name=gemini_model
    )

    # Use one Hugging Face pipeline instance for both PDFs.
    active_ner = ner_pipeline or load_huggingface_ner(hf_model)
    pdf1_ner = extract_ner_from_pages(
        Path(pdf1_path).name, pdf1_pages, active_ner
    )
    pdf2_ner = extract_ner_from_pages(
        Path(pdf2_path).name, pdf2_pages, active_ner
    )
    hf_entities = pdf1_ner + pdf2_ner

    comparison_rows = compare_documents(pdf1_gemini, pdf2_gemini)

    workbook = export_workbook(
        pdf1_gemini,
        pdf2_gemini,
        hf_entities,
        comparison_rows,
        output_path,
    )

    return {
        "pdf1_entities": pdf1_gemini,
        "pdf2_entities": pdf2_gemini,
        "huggingface_entities": hf_entities,
        "comparisons": comparison_rows,
        "output_path": str(workbook),
    }
