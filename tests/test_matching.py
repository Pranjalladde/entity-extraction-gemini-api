
import unittest

from src.entity_project.matching import (
    compare_documents,
    normalize_entity_value,
)


class TestEntityMatching(unittest.TestCase):

    def test_normalization(self):
        result = normalize_entity_value("MEDU-UH 637842")
        self.assertEqual(result, "meduuh637842")

    def test_exact_match(self):
        pdf1 = [
            {
                "Entity Type": "OBOL number",
                "Entity Value": "MEDUUH637842"
            }
        ]

        pdf2 = [
            {
                "Entity Type": "Sea waybill no",
                "Entity Value": "MEDUUH637842"
            }
        ]

        results = compare_documents(pdf1, pdf2)

        self.assertEqual(
            results[0]["Match Result"],
            "Exact match"
        )

        self.assertEqual(
            results[0]["Similarity (%)"],
            100.0
        )

    def test_similar_match(self):
        pdf1 = [
            {
                "Entity Type": "Booking No",
                "Entity Value": "ABC123456"
            }
        ]

        pdf2 = [
            {
                "Entity Type": "Reference",
                "Entity Value": "ABC123457"
            }
        ]

        results = compare_documents(
            pdf1,
            pdf2,
            fuzzy_threshold=0.85
        )

        self.assertEqual(
            results[0]["Match Result"],
            "Similar candidate"
        )

    def test_unmatched_values(self):
        pdf1 = [
            {
                "Entity Type": "Booking No",
                "Entity Value": "ABC123"
            }
        ]

        pdf2 = [
            {
                "Entity Type": "Voyage No",
                "Entity Value": "XYZ987"
            }
        ]

        results = compare_documents(pdf1, pdf2)

        statuses = {
            row["Match Result"] for row in results
        }

        self.assertIn("No match", statuses)
        self.assertIn("Only in PDF 2", statuses)


if __name__ == "__main__":
    unittest.main()
