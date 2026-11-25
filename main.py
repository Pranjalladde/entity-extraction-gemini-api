from __future__ import annotations

import argparse

from src.entity_project.workflow import (
    PDF1_DEFAULT_FIELDS,
    PDF2_DEFAULT_FIELDS,
    run_project,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract and compare entities from two PDF documents."
    )
    parser.add_argument("pdf1", help="First PDF (for example, OBOL)")
    parser.add_argument("pdf2", help="Second PDF (for example, Sea Waybill)")
    parser.add_argument(
        "--output",
        default="entity_extraction_comparison.xlsx",
        help="Excel report output path",
    )
    parser.add_argument("--gemini-model", default=None)
    parser.add_argument("--hf-model", default=None)
    args = parser.parse_args()

    result = run_project(
        args.pdf1,
        args.pdf2,
        output_path=args.output,
        pdf1_fields=PDF1_DEFAULT_FIELDS,
        pdf2_fields=PDF2_DEFAULT_FIELDS,
        gemini_model=args.gemini_model,
        hf_model=args.hf_model,
    )

    print("\nPDF 1 - Gemini entities")
    for row in result["pdf1_entities"]:
        print(f"{row['Entity Type']}: {row['Entity Value']}")

    print("\nPDF 2 - Gemini entities")
    for row in result["pdf2_entities"]:
        print(f"{row['Entity Type']}: {row['Entity Value']}")

    print("\nCross-document matching")
    for row in result["comparisons"]:
        print(
            f"{row['PDF 1 Value']} <-> {row['PDF 2 Value']} | "
            f"{row['Match Result']} | {row['Similarity (%)']}%"
        )

    print(f"\nExcel report saved to: {result['output_path']}")


if __name__ == "__main__":
    main()
