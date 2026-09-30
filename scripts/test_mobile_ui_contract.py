#!/usr/bin/env python3
"""Static regression test for the mobile viewport/touch/safe-area contract.

Per HANDOFF.md ("Harden Mobile Viewport, Touch, and Text-Scaling
Reliability"), this inspects the actual `index.html`/`style.css` text —
it does not run a browser or JS engine — and fails if any of the following
regress: the non-zoom-disabling viewport meta tag, broad
`touch-action: manipulation` coverage, safe-area-inset handling on the app
shell and full-viewport overlays, the legacy-vh-then-dvh override order for
key vertical sizing, the `#board` short-landscape/enlarged-text scroll
escape, and the absence of rules that would truncate or globally suppress
enlarged text.

Run with:
    python3 -m unittest scripts/test_mobile_ui_contract.py
    python3 -m unittest scripts.test_mobile_ui_contract
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class MobileUIContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
        raw_css = (REPO_ROOT / "style.css").read_text(encoding="utf-8")
        # Structural checks below key off selector/rule boundaries; strip
        # comments first so a `/* ... */` block preceding a rule can never be
        # mistaken for part of its selector list.
        cls.css = re.sub(r"/\*.*?\*/", "", raw_css, flags=re.DOTALL)

    # ── Viewport metadata ────────────────────────────────────────────────

    def test_viewport_meta_has_cover_and_device_width_without_disabling_zoom(self):
        match = re.search(
            r'<meta\s+name="viewport"\s+content="([^"]+)"',
            self.html,
        )
        self.assertIsNotNone(match, "viewport meta tag not found")
        content = match.group(1)
        self.assertIn("width=device-width", content)
        self.assertIn("initial-scale=1.0", content)
        self.assertIn("viewport-fit=cover", content)
        self.assertNotIn("user-scalable", content)
        self.assertNotIn("maximum-scale", content)

    def test_no_zoom_disabling_directive_anywhere(self):
        for source_name, text in (("index.html", self.html), ("style.css", self.css)):
            self.assertNotIn("user-scalable", text, source_name)
            self.assertNotIn("maximum-scale", text, source_name)

    # ── touch-action coverage ────────────────────────────────────────────

    def test_touch_action_manipulation_covers_all_real_tap_targets(self):
        match = re.search(
            r"([^{}]+)\{\s*touch-action:\s*manipulation;\s*\}",
            self.css,
        )
        self.assertIsNotNone(match, "no `touch-action: manipulation` rule found")
        selectors = {s.strip() for s in match.group(1).split(",")}
        # Every element main.js attaches a real `click` listener to: slots,
        # bank tiles, shuffle/backspace, ordinary buttons, hard-mode/timer
        # toggle rows, word rows (clicking a row forwards to its slot), the
        # timer display (toggles Hide Timer), and the two dismiss-on-click
        # modal backdrops plus the completion overlay itself.
        required = {
            "button", ".slot", ".tile", ".shuffle-btn", ".backspace-btn",
            ".toggle-row", ".word-row", "#timer-display", ".modal-backdrop",
            "#completion",
        }
        missing = required - selectors
        self.assertFalse(missing, f"touch-action rule is missing selectors: {missing}")

    def test_touch_action_does_not_disable_scrolling_regions(self):
        # The scrollable modal card and the board's own internal-scroll
        # region must never be neutralized by touch-action, whether via a
        # page-wide touch-action: none/pan-* rule or by being added to the
        # manipulation selector list themselves.
        self.assertNotIn("touch-action: none", self.css)
        self.assertNotIn("touch-action: pan-x", self.css)
        match = re.search(
            r"([^{}]+)\{\s*touch-action:\s*manipulation;\s*\}",
            self.css,
        )
        selectors = {s.strip() for s in match.group(1).split(",")}
        self.assertNotIn(".modal-card", selectors)
        self.assertNotIn("#board", selectors)

    # ── Safe-area handling ───────────────────────────────────────────────

    def test_app_shell_and_overlays_apply_all_four_safe_area_insets(self):
        safe_area_props = [
            "safe-area-inset-top",
            "safe-area-inset-right",
            "safe-area-inset-bottom",
            "safe-area-inset-left",
        ]
        for prop in safe_area_props:
            self.assertIn(prop, self.css, f"missing {prop} usage")

        app_rule = self._extract_rule("#app")
        for prop in safe_area_props:
            self.assertIn(prop, app_rule, f"#app is missing {prop}")

        for selector in ("#pregame", ".modal", "#completion"):
            rule = self._extract_rule(selector)
            for prop in safe_area_props:
                self.assertIn(prop, rule, f"{selector} is missing {prop}")

    def test_app_shell_preserves_ordinary_gutter_fallback_before_safe_area(self):
        app_rule = self._extract_rule("#app")
        fallback_index = app_rule.find("padding: 0 16px;")
        env_index = app_rule.find("env(safe-area-inset-top)")
        self.assertNotEqual(fallback_index, -1, "#app lost its plain 16px gutter fallback")
        self.assertNotEqual(env_index, -1, "#app has no env()-based safe-area override")
        self.assertLess(
            fallback_index,
            env_index,
            "the env()-based #app padding must come after (override) the plain fallback",
        )

    # ── Dynamic viewport / legacy vh fallback order ──────────────────────

    def test_html_body_has_legacy_percent_fallback_before_dvh_override(self):
        fallback_index = self.css.find("height: 100%;")
        supports_index = self.css.find("@supports (height: 100dvh)")
        dvh_index = self.css.find("html, body { height: 100dvh; }")
        self.assertNotEqual(fallback_index, -1, "legacy `height: 100%` fallback missing")
        self.assertNotEqual(supports_index, -1, "no `@supports (height: 100dvh)` override")
        self.assertNotEqual(dvh_index, -1, "no dvh override for html, body")
        self.assertLess(fallback_index, supports_index)
        self.assertGreater(dvh_index, supports_index)

    def test_key_vh_sizing_has_dvh_override_inside_supports_block(self):
        # There must be a second @supports (height: 100dvh) block (beyond the
        # html/body one) carrying dvh overrides for the vh-based clamp()
        # values used by --slot-h, #board, .word-row, and #bank-area.
        supports_blocks = re.findall(
            r"@supports \(height: 100dvh\) \{(.*?)\n\}",
            self.css,
            flags=re.DOTALL,
        )
        self.assertGreaterEqual(
            len(supports_blocks), 2, "expected a dedicated dvh override block for vh sizing"
        )
        sizing_block = supports_blocks[-1]
        for needle in ("--slot-h", "dvh", "#board", ".word-row", "#bank-area"):
            self.assertIn(needle, sizing_block, f"dvh sizing override missing {needle!r}")

    def test_every_vh_value_in_the_stylesheet_has_a_paired_dvh_override(self):
        # Every genuine `vh` length in style.css (outside any @supports
        # block) must have an exact `dvh` twin somewhere inside a
        # `@supports (height: 100dvh)` block, so a newly added vh-based rule
        # can't silently regress by shipping without a modern override. Only
        # bare digit+vh tokens count: this must not match `dvh`/`svh`/`lvh`
        # unit tokens (a digit is never immediately followed by `d`/`s`/`l`
        # before `vh` in those), and must not match `vw` at all — width-based
        # sizing is explicitly not part of this contract.
        vh_tokens = re.findall(r"\d+(?:\.\d+)?vh\b", self.css)
        # Known, named uses per the bounded correction: slot height, modal
        # max-height, board padding (x2: top and bottom clamp), word-row
        # margin, slot font-size, bank-area padding.
        self.assertEqual(
            len(vh_tokens),
            7,
            f"expected exactly 7 vh tokens (6 named uses, #board has two clamp() vh values), found {vh_tokens}",
        )

        supports_bodies = "\n".join(
            re.findall(
                r"@supports \(height: 100dvh\) \{(.*?)\n\}",
                self.css,
                flags=re.DOTALL,
            )
        )
        for token in vh_tokens:
            dvh_token = token[:-2] + "dvh"
            self.assertIn(
                dvh_token,
                supports_bodies,
                f"vh value {token!r} has no matching {dvh_token!r} inside an @supports (height: 100dvh) block",
            )

    def test_vw_sizing_is_not_treated_as_a_vh_style_defect(self):
        # --tile-sz is deliberately width-based (vw) so bank tiles track
        # viewport width, not the collapsing/expanding toolbar height; it
        # must not be forced into the vh/dvh pairing contract above.
        self.assertIn("vw", self.css)
        self.assertIn("--tile-sz", self.css)

    # ── Short-landscape / narrow-height escape ───────────────────────────

    def test_board_no_longer_hard_clips_with_overflow_hidden(self):
        board_rule = self._extract_rule("#board", occurrence=0)
        self.assertNotIn(
            "overflow: hidden",
            board_rule,
            "#board must not silently clip rows with overflow: hidden",
        )
        self.assertIn("overflow-y: auto", board_rule)

    def test_narrow_height_media_query_escape_exists(self):
        media_match = re.search(
            r"@media \(max-height: 500px\) \{(.*?)\n\}\n",
            self.css,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(media_match, "no short-landscape/narrow-height media query found")
        body = media_match.group(1)
        self.assertIn("overflow-y: auto", body)
        self.assertIn("#app", body)
        self.assertIn("height: auto", body)
        self.assertIn("#board", body)
        self.assertIn("flex: none", body)

    # ── Text-scaling resilience ──────────────────────────────────────────

    def test_no_global_text_size_adjust_suppression(self):
        self.assertNotIn("text-size-adjust", self.css)

    def test_no_text_truncation_via_ellipsis(self):
        self.assertNotIn("text-overflow", self.css)

    # ── helpers ───────────────────────────────────────────────────────────

    def _extract_rule(self, selector, occurrence=None):
        """Return the raw declaration block text for a rule whose selector
        list contains `selector` as one comma-separated entry.

        A selector can legitimately appear in more than one rule (e.g.
        `#completion` has its own layout rule and also appears in the shared
        `touch-action: manipulation` selector list). With `occurrence=None`
        (the default), returns the match with the most declaration content —
        a selector's dedicated definition is reliably larger than its
        incidental appearance in a shared one-declaration utility rule. Pass
        an explicit `occurrence` index only when file order, not size, is
        the meaningful distinction (e.g. the base rule vs. a later
        media-query override of the same selector)."""
        pattern = re.compile(
            r"(^|\})\s*([^{}]+)\{([^{}]*)\}",
            flags=re.MULTILINE,
        )
        matches = []
        for m in pattern.finditer(self.css):
            selectors = {s.strip() for s in m.group(2).split(",")}
            if selector in selectors:
                matches.append(m.group(0))
        self.assertGreater(len(matches), 0, f"no rule found for selector {selector!r}")
        if occurrence is not None:
            self.assertGreater(len(matches), occurrence, f"no rule #{occurrence} for {selector!r}")
            return matches[occurrence]
        return max(matches, key=len)


if __name__ == "__main__":
    unittest.main()
