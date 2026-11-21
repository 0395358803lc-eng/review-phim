"""Strict parse: Qwen freeform output cannot silently become YES."""
import unittest
from stage5.qwen_provider import parse_visual_verdict
class ProviderParsingTests(unittest.TestCase):
    def test_whole_token_yes_no_uncertain(self):
        self.assertEqual(parse_visual_verdict(" YES "),"YES")
        self.assertEqual(parse_visual_verdict("No."),"NO")
        self.assertEqual(parse_visual_verdict("UNCERTAIN"),"UNCERTAIN")
    def test_explanatory_or_mixed_output_fails_closed(self):
        self.assertEqual(parse_visual_verdict("YES I can see it."),"UNCERTAIN")
        self.assertEqual(parse_visual_verdict("NO but maybe YES"),"UNCERTAIN")
        self.assertEqual(parse_visual_verdict(""),"UNCERTAIN")
if __name__=="__main__":unittest.main()
