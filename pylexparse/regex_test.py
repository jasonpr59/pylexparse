"""Unit tests for regex."""
import unittest

import matcher
import nfa
import regex

def match(regex_string, candidate):
    pattern = regex.parse_regex(regex_string)
    nfa = matcher.pattern_to_nfa(pattern)
    return bool(nfa.match(candidate))

class TestRegex(unittest.TestCase):
    def test_smoke(self):
        """Smoketests until I write some better unit tests."""
        self.assertFalse(match('[bm]e*(at|f{4})', 'beef'))
        self.assertTrue(match('[bm]e*(at|f{4})', 'beeeeeeeeffff'))
        self.assertTrue(match('[bm]e*(at|f{4})', 'meat'))
        self.assertFalse(match('[bm]e*(at|f{4})', 'beaffff'))

if __name__ == '__main__':
    unittest.main()
