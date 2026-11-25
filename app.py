from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.entity_project.workflow import (
    PDF1_DEFAULT_FIELDS,
    PDF2_DEFAULT_FIELDS,
    run_project,
)


st.set_page_config(
    page_title="PDF Entity Extraction & Matching",
    page_icon="📄",
    layout="wide",
)

st.title("Entity Extraction & Matching from PDFs using GenAI")
st.write(
    "Upload two related PDFs, extract shipping entities with Gemini, run "
    "Hugging Face BERT NER, and compare values across the documents."
)

st.info(
    "Gemini API access is required. Add GEMINI_API_KEY to your local .env file. "
    "The key is never included in this app or repository."
)

left, right = st.columns(2)
with left:
    pdf1 = st.file_uploader("PDF 1 — OBOL document", type=["pdf"], key="pdf1")
with right:
    pdf2 = st.file_uploader("PDF 2 — Sea Waybill document", type=["pdf"], key="pdf2")

with st.expander("Edit entity fields", expanded=False):
    left, right = st.columns(2)
    with left:
        fields1_text = st.text_area(
            "PDF 1 fields, one per line",
            value="\n".join(PDF1_DEFAULT_FIELDS),
        )
    with right:
        fields2_text = st.text_area(
            "PDF 2 fields, one per line",
            value="\n".join(PDF2_DEFAULT_FIELDS),
        )

if st.button("Extract and compare", type="primary", disabled=not (pdf1 and pdf2)):
    fields1 = [line.strip() for line in fields1_text.splitlines() if line.strip()]
    fields2 = [line.strip() for line in fields2_text.splitlines() if line.strip()]

    temp_files: list[Path] = []
    try:
        for uploaded in (pdf1, pdf2):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                temp.write(uploaded.getvalue())
                temp_files.append(Path(temp.name))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
            output_path = Path(temp.name)
            temp_files.append(output_path)

        with st.spinner(
            "Extracting PDF text, calling Gemini, running Hugging Face NER, "
            "and comparing values..."
        ):
            result = run_project(
                temp_files[0],
                temp_files[1],
                output_path=output_path,
                pdf1_fields=fields1,
                pdf2_fields=fields2,
            )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("PDF 1 — Gemini extraction")
            st.dataframe(
                pd.DataFrame(result["pdf1_entities"]),
                use_container_width=True,
                hide_index=True,
            )
        with col2:
            st.subheader("PDF 2 — Gemini extraction")
            st.dataframe(
                pd.DataFrame(result["pdf2_entities"]),
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("Hugging Face BERT NER")
        st.dataframe(
            pd.DataFrame(result["huggingface_entities"]),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Entity matching")
        st.dataframe(
            pd.DataFrame(result["comparisons"]),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Excel report",
            data=output_path.read_bytes(),
            file_name="entity_extraction_comparison.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as exc:
        st.error(f"Processing failed: {exc}")
    finally:
        for path in temp_files:
            path.unlink(missing_ok=True)

st.caption(
    "Hugging Face NER uses a public pretrained BERT checkpoint for general "
    "person/organisation/location recognition. It is not a custom fine-tuned "
    "shipping-document model. Similarity candidates should be reviewed manually."
)
