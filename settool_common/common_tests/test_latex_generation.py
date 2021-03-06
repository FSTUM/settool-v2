import unittest

from settool_common.templatetags import latex


class LatexAuxTest(unittest.TestCase):
    def test_escape_latex_empty(self):
        self.assertEqual("{}", latex.latex_escape(""))

    def test_escape_latex_replacements(self):
        replacements = [
            (" ", "\\ "),
            ("&", "\\&"),
            ("%", "\\%"),
            ("$", "\\$"),
            ("#", "\\#"),
            ("_", "\\_"),
            ("{", "\\{"),
            ("}", "\\}"),
            ("\\", "\\textbackslash "),
            ("~", "\\textasciitilde "),
            ("^", "\\textasciicircum "),
        ]
        for input_str, replacement_str in replacements:
            self.assertEqual(replacement_str, latex.latex_escape(input_str))
