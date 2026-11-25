
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
import google.generativeai as genai

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader


# -----------------------------------------
# 1. DEFAULT ENTITY FIELDS
# -----------------------------------------

DEFAULT_ENTITY_FIELDS = [
    "VESSEL",
    "ETD BUSAN",
    "NO.&Date of Invoice",
    "Shipper/Exporter",
    "TOTAL CIF",
    "PURCHASE ORDER NO.",
]


# -----------------------------------------
# 2. GEMINI CONFIGURATION
# -----------------------------------------

GENERATION_CONFIG = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

DEFAULT_MODEL_NAME = "gemini-3.8-flash"


def configure_gemini(api_key: str | None = None) -> None:
    """Configure Gemini using a private environment variable."""

    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    key = api_key or os.getenv("GEMINI_API_KEY")

    if not key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Add your key to the local .env file."
        )

    genai.configure(api_key=key)


def create_model(model_name: str | None = None):
    """Initialize the Gemini generative model."""

    selected_model = (
        model_name
        or os.getenv("GEMINI_MODEL")
        or DEFAULT_MODEL_NAME
    )

    return genai.GenerativeModel(
        model_name=selected_model,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS,
    )


# -----------------------------------------
# 3. LOAD PDF DOCUMENT
# -----------------------------------------

def load_pdf_pages(pdf_path: str | Path) -> list[dict[str, Any]]:
    """Load PDF content page by page using LangChain."""

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Please provide a PDF file.")

    loader = PyPDFLoader(str(path))
    documents = loader.load()

    pages = []

    for index, document in enumerate(documents, start=1):

        page_content = (document.page_content or "").strip()

        if page_content:
            page_number = int(
                document.metadata.get("page", index - 1)
            ) + 1

            pages.append({
                "page": page_number,
                "text": page_content
            })

    if not pages:
        raise ValueError(
            "No readable PDF text found. "
            "Scanned PDFs may require OCR."
        )

    return pages


# -----------------------------------------
# 4. SPLIT PDF TEXT INTO BLOCKS
# -----------------------------------------

def split_into_blocks(page_text: str) -> list[str]:
    """Split PDF page content into smaller text blocks."""

    blocks = re.split(
        r"\n\s*\n",
        page_text
    )

    blocks = [
        re.sub(r"[ \t]+", " ", block).strip()
        for block in blocks
    ]

    blocks = [
        block for block in blocks if block
    ]

    # If there are no paragraph breaks,
    # process the complete page as one block.

    if not blocks and page_text.strip():
        blocks = [page_text.strip()]

    return blocks


# -----------------------------------------
# 5. CREATE GEMINI EXTRACTION PROMPT
# -----------------------------------------

def build_extraction_prompt(
    block: str,
    entity_fields: list[str]
) -> str:

    fields = ", ".join(entity_fields)

    prompt = f"""
    Extract the following entities from the PDF text:

    {fields}

    Instructions:

    1. Extract only the requested information.
    2. Do not invent or guess values.
    3. If an entity is unavailable, return NOT FOUND.
    4. Preserve dates, invoice numbers and amounts.
    5. Return each entity in this format:

       ENTITY NAME | extracted value

    6. Do not return Markdown tables or explanations.

    PDF CONTENT:

    {block}
    """

    return prompt


# -----------------------------------------
# 6. PARSE GEMINI RESPONSE
# -----------------------------------------

def parse_entity_response(
    response_text: str,
    entity_fields: list[str]
) -> dict[str, str]:

    field_mapping = {
        field.casefold(): field
        for field in entity_fields
    }

    extracted = {
        field: ""
        for field in entity_fields
    }

    for line in (response_text or "").splitlines():

        line = line.replace("**", "").strip()
        line = line.lstrip("-• ").strip()

        if "|" not in line:
            continue

        entity_type, entity_value = line.split("|", 1)

        entity_type = (
            entity_type.strip()
            .strip("*")
            .casefold()
        )

        entity_value = entity_value.strip().strip("*")

        if entity_type not in field_mapping:
            continue

        if entity_value.casefold() in {
            "not found",
            "not available",
            "n/a",
            "none",
            "null"
        }:
            entity_value = ""

        extracted[field_mapping[entity_type]] = entity_value

    return extracted


# -----------------------------------------
# 7. EXTRACT ENTITIES FROM PDF USING GEMINI
# -----------------------------------------

def extract_entities_from_pdf(
    pdf_path: str | Path,
    entity_fields: list[str] | None = None,
    model_name: str | None = None,
    api_key: str | None = None
):

    fields = entity_fields or DEFAULT_ENTITY_FIELDS

    if not fields:
        raise ValueError("Entity fields cannot be empty.")

    configure_gemini(api_key)

    model = create_model(model_name)

    pages = load_pdf_pages(pdf_path)

    all_entities = []

    for page in pages:

        page_content = page["text"]

        blocks = split_into_blocks(page_content)

        for block_number, block in enumerate(blocks, start=1):

            prompt = build_extraction_prompt(
                block,
                fields
            )

            # Start a separate chat for each block.

            conversation = model.start_chat(
                history=[]
            )

            response = conversation.send_message(prompt)

            if not response.text:
                raise RuntimeError(
                    f"Gemini returned an empty response "
                    f"for page {page['page']}."
                )

            extracted_entities = parse_entity_response(
                response.text,
                fields
            )

            for entity_type, entity_value in extracted_entities.items():

                all_entities.append({
                    "Page": page["page"],
                    "Block": block_number,
                    "Entity Type": entity_type,
                    "Entity Value": entity_value
                })

    # Convert results into DataFrame.

    page_df = pd.DataFrame(
        all_entities,
        columns=[
            "Page",
            "Block",
            "Entity Type",
            "Entity Value"
        ]
    )

    # Consolidate extracted values.

    summary_rows = []

    for field in fields:

        values = page_df.loc[
            page_df["Entity Type"] == field,
            "Entity Value"
        ].tolist()

        unique_values = []

        for value in values:

            if value and value not in unique_values:
                unique_values.append(value)

        summary_rows.append({
            "Entity Type": field,
            "Entity Value": " | ".join(unique_values)
        })

    summary_df = pd.DataFrame(summary_rows)

    return summary_df, page_df


# -----------------------------------------
# 8. EXPORT EXTRACTED ENTITIES TO EXCEL
# -----------------------------------------

def export_to_excel(
    summary_df: pd.DataFrame,
    page_df: pd.DataFrame,
    output_path: str | Path
) -> Path:

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with pd.ExcelWriter(
        output_path,
        engine="openpyxl"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Entities from PDF",
            index=False
        )

        page_df.to_excel(
            writer,
            sheet_name="Page-wise Results",
            index=False
        )

    return output_path
