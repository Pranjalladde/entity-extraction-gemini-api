from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from entity_extraction.pipeline import (
    DEFAULT_ENTITY_FIELDS,
    export_to_excel,
    extract_entities_from_pdf,
)

st.set_page_config(page_title="Gemini PDF Entity Extractor", page_icon="📄")
st.title("Entity Extraction from PDF using Google Gemini")
st.write(
    "Upload a PDF and extract business-specific fields such as vessel name, "
    "ETD, invoice details, shipper/exporter, total CIF, and purchase order number."
)
st.warning(
    "A Gemini API key is required. Store it only in your local .env file; "
    "never paste it into source code or commit it to GitHub."
)

fields_text = st.text_area(
    "Entity fields (one per line)",
    value="\n".join(DEFAULT_ENTITY_FIELDS),
    height=170,
)
uploaded_pdf = st.file_uploader("Choose a PDF document", type=["pdf"])

if uploaded_pdf is not None and st.button("Extract entities", type="primary"):
    fields = [line.strip() for line in fields_text.splitlines() if line.strip()]
    if not fields:
        st.error("Enter at least one entity field.")
    else:
        pdf_path: Path | None = None
        xlsx_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                temp.write(uploaded_pdf.getvalue())
                pdf_path = Path(temp.name)

            with st.spinner("Reading PDF and extracting fields with Gemini..."):
                summary_df, page_df = extract_entities_from_pdf(
                    pdf_path=pdf_path,
                    entity_fields=fields,
                )

            st.success("Extraction completed.")
            st.subheader("Extracted entities")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            with st.expander("View page-wise extraction details"):
                st.dataframe(page_df, use_container_width=True, hide_index=True)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as output:
                xlsx_path = Path(output.name)
            export_to_excel(summary_df, page_df, xlsx_path)
            st.download_button(
                "Download Excel workbook",
                data=xlsx_path.read_bytes(),
                file_name="extracted_entities.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as exc:
            st.error(f"Extraction failed: {exc}")
        finally:
            if pdf_path is not None:
                pdf_path.unlink(missing_ok=True)
            if xlsx_path is not None:
                xlsx_path.unlink(missing_ok=True)

st.caption(
    "Scanned or image-only PDFs may require OCR before text extraction. "
    "Review Gemini's extracted values before using them in business workflows."
)
