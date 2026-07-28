"""Unit tests for USCIRF country-page excerpt cleanup."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from archive_download import uscirf_page_to_excerpt  # noqa: E402

FIXTURE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Religious Freedom Conditions in Exampleland | USCIRF</title>
<script>window.analytics = true;</script>
<style>.nav { display:block; }</style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <header>
    <nav>
      <div class="user-account">User account menu</div>
      <ul class="mega-menu">
        <li>Afghanistan</li><li>Algeria</li><li>Azerbaijan</li>
        <li>Burma</li><li>China</li><li>Cuba</li><li>Egypt</li>
        <li>Eritrea</li><li>India</li><li>Indonesia</li><li>Iran</li>
        <li>Iraq</li><li>Kazakhstan</li><li>Kyrgyzstan</li><li>Libya</li>
        <li>Malaysia</li><li>Nicaragua</li><li>Nigeria</li>
        <li>North Korea</li><li>Pakistan</li><li>Qatar</li><li>Russia</li>
        <li>Saudi Arabia</li><li>Syria</li><li>Tajikistan</li>
        <li>Turkey</li><li>Turkmenistan</li><li>Uzbekistan</li><li>Vietnam</li>
      </ul>
    </nav>
  </header>
  <div id="main" class="container">
    <a id="main-content"></a>
    <div class="full-content">
      <p>Advising Government</p>
      <p>Religious communities in Exampleland face persecution when they refuse
      to submit to state control over religious affairs. Authorities detain
      house church Protestants and restrict religious freedom nationwide.</p>
    </div>
  </div>
  <footer>Contact Us</footer>
  <noscript>Enable JavaScript</noscript>
</body>
</html>
"""

PROSE = (
    "Religious communities in Exampleland face persecution when they refuse "
    "to submit to state control over religious affairs"
)


class TestUscirfArchiveExcerpt(unittest.TestCase):
    def test_strips_skip_link_and_keeps_prose(self):
        excerpt = uscirf_page_to_excerpt(FIXTURE_HTML)
        self.assertNotIn("Skip to main content", excerpt)
        self.assertNotIn("User account menu", excerpt)
        self.assertNotIn("Advising Government", excerpt)
        self.assertIn(PROSE, excerpt)
        self.assertTrue(excerpt.startswith("Religious communities"))

    def test_rejects_empty(self):
        self.assertEqual(uscirf_page_to_excerpt(""), "")


if __name__ == "__main__":
    unittest.main()
