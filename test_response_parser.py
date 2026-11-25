import unittest
from entity_extraction.pipeline import DEFAULT_ENTITY_FIELDS, parse_entity_response

class ParserTests(unittest.TestCase):
    def test_pipe_separated_values(self):
        result = parse_entity_response("VESSEL | MV BLUE OCEAN\nTOTAL CIF | USD 12500", DEFAULT_ENTITY_FIELDS)
        self.assertEqual(result["VESSEL"], "MV BLUE OCEAN")
        self.assertEqual(result["TOTAL CIF"], "USD 12500")
    def test_not_found_becomes_empty(self):
        self.assertEqual(parse_entity_response("VESSEL | NOT FOUND", ["VESSEL"])["VESSEL"], "")

if __name__ == "__main__": unittest.main()
