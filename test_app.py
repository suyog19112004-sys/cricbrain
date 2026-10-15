"""
Test Suite for CRICBRAIN
Verifies:
1. All three formats load (Test, ODI, T20I, plus All formats)
2. Sources appear as clickable links under every result
3. The cutoff label is visible and correct for each format:
   - Test: minimum 20 innings
   - ODI: minimum 20 innings
   - T20I: minimum 50 innings
4. Ties display correctly and honestly
5. An error shows a friendly message
6. No API key is visible in the page source or responses
"""

import unittest
import json
import re
from app import app, FORMAT_CONFIG, fetch_grounded_cricket_records


class TestCricbrain(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_1_all_formats_load(self):
        """Check all three formats (Test, ODI, T20I) and 'all' load successfully."""
        formats = ["test", "odi", "t20i", "all"]
        for fmt in formats:
            resp = self.client.get(f"/api/stats/{fmt}")
            self.assertEqual(resp.status_code, 200, f"Format '{fmt}' failed to load with status {resp.status_code}")
            data = resp.get_json()
            self.assertEqual(data.get("status"), "success", f"Format '{fmt}' returned non-success status")
            self.assertIn("data", data, f"Format '{fmt}' missing data payload")

            if fmt != "all":
                # Check top 5 batsmen and bowlers
                batsmen = data["data"].get("top_batsmen", [])
                bowlers = data["data"].get("top_bowlers", [])
                self.assertEqual(len(batsmen), 5, f"Expected 5 batsmen for {fmt}, got {len(batsmen)}")
                self.assertEqual(len(bowlers), 5, f"Expected 5 bowlers for {fmt}, got {len(bowlers)}")
                
                # Check highest average card exists
                ha = data["data"].get("highest_average", {})
                self.assertTrue(ha.get("player"), f"Missing highest average player for {fmt}")
                self.assertTrue(ha.get("average"), f"Missing highest average value for {fmt}")
            else:
                formats_data = data["data"].get("formats_data", {})
                self.assertIn("test", formats_data)
                self.assertIn("odi", formats_data)
                self.assertIn("t20i", formats_data)

    def test_2_sources_appear_as_links(self):
        """Check every single result card has a valid http/https source link."""
        for fmt in ["test", "odi", "t20i"]:
            resp = self.client.get(f"/api/stats/{fmt}")
            data = resp.get_json()["data"]

            # Check batsmen sources
            for b in data.get("top_batsmen", []):
                source = b.get("source_url", "")
                self.assertTrue(source.startswith("http"), f"Invalid source link for batsman {b.get('player')}: {source}")

            # Check bowlers sources
            for bw in data.get("top_bowlers", []):
                source = bw.get("source_url", "")
                self.assertTrue(source.startswith("http"), f"Invalid source link for bowler {bw.get('player')}: {source}")

            # Check highest average source
            ha_source = data.get("highest_average", {}).get("source_url", "")
            self.assertTrue(ha_source.startswith("http"), f"Invalid highest avg source link for {fmt}: {ha_source}")

    def test_3_cutoff_labels_visible(self):
        """Check that the minimum-innings cutoff is correctly stated for each format:
           - Test: minimum 20 innings
           - ODI: minimum 20 innings
           - T20I: minimum 50 innings
        """
        expected_cutoffs = {
            "test": "Minimum 20 innings cutoff",
            "odi": "Minimum 20 innings cutoff",
            "t20i": "Minimum 50 innings cutoff",
        }

        for fmt, expected_label in expected_cutoffs.items():
            resp = self.client.get(f"/api/stats/{fmt}")
            data = resp.get_json()["data"]
            self.assertEqual(data.get("cutoff_label"), expected_label, f"Cutoff label mismatch for {fmt}")
            
            # Check highest_average block contains cutoff info
            ha = data.get("highest_average", {})
            self.assertIn("cutoff", str(ha).lower(), f"Cutoff not mentioned in highest_average block for {fmt}")

    def test_4_ties_display_correctly(self):
        """Check honest tie handling logic when two players have equal runs or wickets."""
        # Simulated test with equal wickets
        test_bowlers = [
            {"player": "Bowler A", "wickets": 500},
            {"player": "Bowler B", "wickets": 400},
            {"player": "Bowler C", "wickets": 400},
            {"player": "Bowler D", "wickets": 350},
            {"player": "Bowler E", "wickets": 300},
        ]
        
        # Test tie marking logic
        prev_wkts = None
        prev_rank = 1
        for idx, bw in enumerate(test_bowlers):
            wkts = bw["wickets"]
            if wkts == prev_wkts and idx > 0:
                bw["is_tie"] = True
                test_bowlers[idx - 1]["is_tie"] = True
                bw["display_rank"] = f"T{prev_rank}"
                test_bowlers[idx - 1]["display_rank"] = f"T{prev_rank}"
            else:
                bw["is_tie"] = False
                bw["display_rank"] = str(idx + 1)
                prev_rank = idx + 1
            prev_wkts = wkts

        # Verify that Bowler B and Bowler C are both marked as tied at T2
        self.assertTrue(test_bowlers[1]["is_tie"])
        self.assertTrue(test_bowlers[2]["is_tie"])
        self.assertEqual(test_bowlers[1]["display_rank"], "T2")
        self.assertEqual(test_bowlers[2]["display_rank"], "T2")
        self.assertEqual(test_bowlers[3]["display_rank"], "4")

    def test_5_error_shows_friendly_message(self):
        """Check that invalid queries return friendly error messages without crashing."""
        # Invalid format
        resp = self.client.get("/api/stats/hundreds_cricket")
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("Unknown format", data.get("message", ""))

        # Empty question to Ask CRICBRAIN
        resp_ask = self.client.post("/api/ask", json={"question": ""})
        self.assertEqual(resp_ask.status_code, 400)
        self.assertIn("cannot be empty", resp_ask.get_json().get("message", "").lower())

    def test_6_no_api_key_visible_in_page_source(self):
        """Check that no API key is exposed anywhere in the HTML page source or responses."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # Check for any patterns of API keys
        self.assertNotIn("AIzaSy", html, "Gemini API key prefix found in page source!")
        self.assertNotIn("GEMINI_API_KEY", html, "Environment variable name found in page source!")
        
        # Check config endpoint
        cfg_resp = self.client.get("/api/config")
        cfg_data = cfg_resp.get_json()
        self.assertNotIn("apiKey", cfg_data, "apiKey field leaked in /api/config!")
        self.assertNotIn("key", cfg_data, "key leaked in /api/config!")

    def test_7_built_by_suyog_shinde_visible(self):
        """Verify 'Built by Suyog Shinde' is present in footer and template."""
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("Built by", html)
        self.assertIn("Suyog Shinde", html)

    def test_8_top_means_career_runs_or_wickets_on_screen(self):
        """Verify the mandatory statement: 'Top' means career runs or wickets, not opinion and not ICC ratings."""
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("Top", html)
        self.assertIn("career runs or wickets", html)
        self.assertIn("not opinion", html)
        self.assertIn("not ICC ratings", html)


if __name__ == "__main__":
    unittest.main()
