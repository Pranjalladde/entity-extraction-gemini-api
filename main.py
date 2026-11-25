from __future__ import annotations
import argparse
from entity_extraction.pipeline import DEFAULT_ENTITY_FIELDS, export_to_excel, extract_entities_from_pdf

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract business fields from a PDF using Gemini API.")
    parser.add_argument("pdf", help="Path to a text-based PDF")
    parser.add_argument("--output", default="extracted_entities.xlsx")
    parser.add_argument("--model", default=None)
    parser.add_argument("--fields", nargs="+", default=DEFAULT_ENTITY_FIELDS)
    args = parser.parse_args()
    summary, pagewise = extract_entities_from_pdf(args.pdf, args.fields, args.model)
    output = export_to_excel(summary, pagewise, args.output)
    print(summary.to_string(index=False))
    print(f"\nSaved Excel workbook: {output.resolve()}")

if __name__ == "__main__":
    main()
