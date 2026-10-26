"""
Automated unit tests for Quick Expander core components.
Includes tests for Dynamic Variables, Snippet CRUD, Categories, and Multi-Candidate matching.
"""

import sys
import os
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import ConfigManager
from app.variables import resolve_variables
from app.engine import ExpansionEngine


class TestQuickExpander(unittest.TestCase):
    def setUp(self):
        self.config_mgr = ConfigManager()

    def test_variable_resolution(self):
        # Date resolution
        text, offset = resolve_variables("Today is {{date}}")
        self.assertNotIn("{{date}}", text)
        self.assertIn("-", text)
        self.assertEqual(offset, 0)

        # Custom date
        text, _ = resolve_variables("{{date:%Y/%m/%d}}")
        self.assertRegex(text, r"^\d{4}/\d{2}/\d{2}$")

        # Time resolution
        text, _ = resolve_variables("Time: {{time}}")
        self.assertNotIn("{{time}}", text)
        self.assertIn(":", text)

        # UUID
        text, _ = resolve_variables("UUID: {{uuid}}")
        self.assertNotIn("{{uuid}}", text)
        self.assertEqual(len(text), 6 + 36)

        # Cursor position
        text, offset = resolve_variables("Hello {{cursor}}World")
        self.assertEqual(text, "Hello World")
        self.assertEqual(offset, 5)

    def test_snippets_crud_and_categories(self):
        # Add category
        cat_name = "测试分类"
        self.config_mgr.add_category(cat_name)
        self.assertIn(cat_name, self.config_mgr.get_categories())

        # Add snippet with category
        rule = self.config_mgr.add_snippet("test_trig", "test_repl", "Test Rule", category=cat_name)
        rule_id = rule["id"]
        self.assertEqual(rule["category"], cat_name)
        self.assertTrue(any(s["id"] == rule_id for s in self.config_mgr.snippets))

        # Rename category
        self.config_mgr.rename_category(cat_name, "新测试分类")
        self.assertIn("新测试分类", self.config_mgr.get_categories())
        updated_rule = next(s for s in self.config_mgr.snippets if s["id"] == rule_id)
        self.assertEqual(updated_rule["category"], "新测试分类")

        # Delete category
        self.config_mgr.delete_category("新测试分类")
        self.assertNotIn("新测试分类", self.config_mgr.get_categories())

        # Clean up snippet
        self.config_mgr.delete_snippet(rule_id)
        self.assertFalse(any(s["id"] == rule_id for s in self.config_mgr.snippets))

    def test_default_snippet_411(self):
        rule_411 = next((s for s in self.config_mgr.snippets if s["trigger"] == "411"), None)
        self.assertIsNotNone(rule_411, "Rule 411 should be in snippets")
        self.assertTrue(bool(rule_411["replacement"]))
        self.assertTrue(rule_411["enabled"])

    def test_multi_candidate_logic(self):
        engine = ExpansionEngine(self.config_mgr)

        # Add second 411 rule
        rule_alt = self.config_mgr.add_snippet("411", "4118888888", "VIP 专号")
        try:
            candidates_shown = []
            engine.on_show_candidates = lambda c, t: candidates_shown.append((t, len(c)))

            engine.buffer = "test 411"
            engine._check_and_expand()

            # Multiple candidates should trigger on_show_candidates
            self.assertTrue(engine.candidate_mode)
            self.assertGreaterEqual(len(engine.active_candidates), 2)
            self.assertEqual(len(candidates_shown), 1)
            self.assertEqual(candidates_shown[0][0], "411")
        finally:
            self.config_mgr.delete_snippet(rule_alt["id"])

    def test_strict_case_matching(self):
        engine = ExpansionEngine(self.config_mgr)

        # Test 1: Case-sensitive rule (StrictGisTest -> Gis123456)
        rule_gis = self.config_mgr.add_snippet("StrictGisTest", "Gis123456", "GIS 系统", match_case=True)
        try:
            # 1a: Exact case 'StrictGisTest' should trigger
            engine.is_expanding = False
            engine.buffer = "StrictGisTest"
            engine._check_and_expand()
            self.assertTrue(engine.is_expanding, "Exact case 'StrictGisTest' should match and expand")

            # 1b: Lowercase 'strictgistest' should NOT trigger
            engine.is_expanding = False
            engine.buffer = "strictgistest"
            engine._check_and_expand()
            self.assertFalse(engine.is_expanding, "Lowercase 'strictgistest' should NOT match when match_case=True")

            # 1c: All-uppercase 'STRICTGISTEST' should NOT trigger
            engine.is_expanding = False
            engine.buffer = "STRICTGISTEST"
            engine._check_and_expand()
            self.assertFalse(engine.is_expanding, "Uppercase 'STRICTGISTEST' should NOT match when match_case=True")
        finally:
            self.config_mgr.delete_snippet(rule_gis["id"])

        # Test 2: Case-insensitive rule (when match_case=False)
        rule_loose = self.config_mgr.add_snippet("caseInsensitiveTest", "success", match_case=False)
        try:
            engine.is_expanding = False
            engine.buffer = "caseinsensitivetest"
            engine._check_and_expand()
            self.assertTrue(engine.is_expanding, "Lowercase input should match when match_case=False")
        finally:
            self.config_mgr.delete_snippet(rule_loose["id"])


if __name__ == "__main__":
    unittest.main()

