import unittest

from services.speaking_scoring import calculate_speaking_scores, normalize_german


class SpeakingScoringTests(unittest.TestCase):
    def test_normalize_keeps_german_characters(self):
        self.assertEqual(normalize_german("Grüße, STRASSE!"), "grüsse strasse")

    def test_matching_transcript_scores_high(self):
        text = "Guten Morgen, wie geht es Ihnen? Mir geht es gut, danke."
        result = calculate_speaking_scores(text, text, 6.3, pause_count=1, intonation_variation=0.24)
        self.assertGreaterEqual(result["totalScore"], 90)
        self.assertEqual(result["accuracyScore"], 100)

    def test_missing_transcript_does_not_fabricate_score(self):
        result = calculate_speaking_scores("Guten Morgen", "", 3)
        self.assertEqual(result["totalScore"], 0)
        self.assertEqual(result["pronunciationScore"], 0)

    def test_incomplete_transcript_is_penalized(self):
        result = calculate_speaking_scores(
            "Ich hätte gern eine Suppe und ein Glas Wasser bitte",
            "Ich hätte gern Wasser",
            8,
            pause_count=3,
            intonation_variation=0.1,
        )
        self.assertLess(result["totalScore"], 70)
        self.assertTrue(result["missingWords"])


if __name__ == "__main__":
    unittest.main()
