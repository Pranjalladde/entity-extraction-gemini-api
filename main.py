from __future__ import annotations

import argparse

from entity_extraction.pipeline import (
    DEFAULT_ENTITY_FIELDS,
    export_to_excel,
    extract_entities_from_pdf,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract requested business fields from a PDF using Gemini API."
    )
    parser.add_argument("pdf", help="Path to the input PDF")
    parser.add_argument("--output", default="extracted_entities.xlsx")
    parser.add_argument("--model", default=None)
    parser.add_argument("--fields", nargs="+", default=DEFAULT_ENTITY_FIELDS)
    args = parser.parse_args()

    summary_df, page_df = extract_entities_from_pdf(
        pdf_path=args.pdf,
        entity_fields=args.fields,
        model_name=args.model,
    )
    output = export_to_excel(summary_df, page_df, args.output)
    print("\nExtracted entities:")
    print(summary_df.to_string(index=False))
    print(f"\nExcel workbook saved to: {output.resolve()}")


if __name__ == "__main__":
    main()
