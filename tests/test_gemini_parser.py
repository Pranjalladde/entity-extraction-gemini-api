
import unittest

from src.entity_project.gemini_extractor import (
    parse_gemini_response
)


class TestGeminiParser(unittest.TestCase):

    def test_parse_json(self):
        result = parse_gemini_response(
            '{"Booking No":"038VC9102909",'
            '"Vessel name":"MSC HEIDI"}',
            ["Booking No", "Vessel name"]
        )

        self.assertEqual(
            result["Booking No"],
            "038VC9102909"
        )

        self.assertEqual(
            result["Vessel name"],
            "MSC HEIDI"
        )

    def test_missing_field(self):
        result = parse_gemini_response(
            '{"Booking No":"ABC123"}',
            ["Booking No", "Address"]
        )

        self.assertEqual(result["Address"], "")

    def test_markdown_json(self):
        response = (
            '```json\n{"SCAC code":"MSCU"}\n```'
        )

        result = parse_gemini_response(
            response,
            ["SCAC code"]
        )

        self.assertEqual(
            result["SCAC code"],
            "MSCU"
        )

    def test_field_value_text(self):
        result = parse_gemini_response(
            "Vessel name: MSC HEIDI",
            ["Vessel name"]
        )

        self.assertEqual(
            result["Vessel name"],
            "MSC HEIDI"
        )


if __name__ == "__main__":
    unittest.main()
