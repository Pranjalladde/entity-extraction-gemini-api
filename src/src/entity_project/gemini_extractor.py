from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


def load_project_environment() -> None:
    """Load .env from the repository root, if it exists."""
    repository_root = Path(__file__).resolve().parents[2]
    load_dotenv(repository_root / ".env")


def create_gemini_client(api_key: str | None = None):
    """Create a Gemini client. The API key is read from .env or environment."""
    load_project_environment()
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and add "
            "your own private Gemini API key."
        )

    try:
        from google import genai
    except ImportError as exc:
        raise ImportError(
            "Google Gen AI SDK is missing. Run: pip install -r requirements.txt"
        ) from exc

    return genai.Client(api_key=key)


def build_extraction_prompt(
    document_name: str,
    text_block: str,
    requested_fields: list[str],
) -> str:
    fields = json.dumps(requested_fields, ensure_ascii=False)
    return f"""
You extract structured information from shipping and logistics documents.

Document: {document_name}

Requested fields:
{fields}

Return exactly one valid JSON object. Use the requested field names as keys
and string values as their extracted values.

Rules:
- Extract only what is present in the supplied text.
- Do not guess or invent information.
- Use an empty string when a field is absent from this text block.
- Preserve booking references, waybill numbers, vessel names, dates, ports,
  addresses, order numbers and codes as written.
- Do not include Markdown fences or explanatory text.

PDF text:
<<<
{text_block}
>>>
""".strip()


def parse_gemini_response(response_text: str, requested_fields: list[str]) -> dict[str, str]:
    """Parse JSON (or simple field: value fallback) into requested fields."""
    text = (response_text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {}
        for line in text.splitlines():
            cleaned = line.replace("**", "").strip().lstrip("-• ")
            if ":" in cleaned:
                key, value = cleaned.split(":", 1)
                payload[key.strip()] = value.strip()

    if not isinstance(payload, dict):
        raise ValueError("Gemini response was not a JSON object or field/value list.")

    requested_map = {field.casefold(): field for field in requested_fields}
    result = {field: "" for field in requested_fields}

    for key, value in payload.items():
        canonical = requested_map.get(str(key).strip().casefold())
        if canonical is None:
            continue

        if value is None:
            value_text = ""
        elif isinstance(value, (dict, list)):
            value_text = json.dumps(value, ensure_ascii=False)
        else:
            value_text = str(value).strip()

        if value_text.casefold() in {
            "not found", "not provided", "not available", "n/a", "none", "null"
        }:
            value_text = ""

        result[canonical] = value_text

    return result


def extract_entities_from_pages(
    document_name: str,
    pages: list[dict[str, Any]],
    requested_fields: list[str],
    client: Any | None = None,
    model_name: str | None = None,
) -> list[dict[str, Any]]:
    """Use Gemini to extract requested business fields page-by-page/block-by-block."""
    if not requested_fields:
        raise ValueError("At least one requested field is required.")

    if client is None:
        client = create_gemini_client()

    load_project_environment()
    selected_model = model_name or os.getenv(
        "GEMINI_MODEL", DEFAULT_GEMINI_MODEL
    )

    try:
        from google.genai import types
    except ImportError as exc:
        raise ImportError("Install google-genai to call Gemini.") from exc

    rows: list[dict[str, Any]] = []

    for page in pages:
        blocks = re.split(r"\n\s*\n", page["text"])
        blocks = [block.strip() for block in blocks if block.strip()]
        if not blocks and page["text"].strip():
            blocks = [page["text"].strip()]

        for block_number, block in enumerate(blocks, start=1):
            prompt = build_extraction_prompt(
                document_name, block, requested_fields
            )
            response = client.models.generate_content(
                model=selected_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=1,
                    top_k=1,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                ),
            )

            response_text = getattr(response, "text", None)
            if not response_text:
                raise RuntimeError(
                    f"Gemini returned an empty response for {document_name}, "
                    f"page {page['page']}."
                )

            extracted = parse_gemini_response(response_text, requested_fields)
            for entity_type, entity_value in extracted.items():
                if entity_value:
                    rows.append({
                        "Document": document_name,
                        "Page": page["page"],
                        "Block": block_number,
                        "Entity Type": entity_type,
                        "Entity Value": entity_value,
                        "Source": "Gemini",
                    })

    return rows
