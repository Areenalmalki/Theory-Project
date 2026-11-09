"""
Automated validation of the NFA -> DFA conversion.

For every example NFA we check that:
  1. The DFA is well-formed (total transition function, start/accepting inside Q').
  2. The DFA accepts EXACTLY the same strings as the NFA for every string up to
     length 10 (brute force over Σ^0 ... Σ^10).
  3. When the example states its language as a regular expression, the DFA
     also agrees with that independent definition.
  4. Hand-computed expected results (state count, textbook DFA) match.

Run from the project folder:   python -m unittest discover -s tests -v
"""

import glob
import itertools
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from automata import NFA, AutomatonError, subset_construction  # noqa: E402

EXAMPLES = sorted(glob.glob(os.path.join(ROOT, "examples", "*.json")))
MAX_LEN = 10


def all_words(alphabet, max_len):
    for n in range(max_len + 1):
        for t in itertools.product(alphabet, repeat=n):
            yield "".join(t)


class TestExamples(unittest.TestCase):

    def test_examples_exist(self):
        self.assertGreaterEqual(len(EXAMPLES), 3, "need at least three test NFAs")

    def test_dfa_equivalent_to_nfa(self):
        for path in EXAMPLES:
            with self.subTest(example=os.path.basename(path)):
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                nfa = NFA.from_dict(data)
                dfa = subset_construction(nfa)

                # 1. well-formed DFA
                self.assertIn(dfa.start, dfa.states)
                self.assertTrue(dfa.accepting <= set(dfa.states))
                for s in dfa.states:
                    for a in dfa.alphabet:
                        self.assertIn((s, a), dfa.transitions)
                        self.assertIn(dfa.transitions[(s, a)], dfa.states)

                # 2 + 3. same language
                rx = data.get("language_regex")
                for w in all_words(nfa.alphabet, MAX_LEN):
                    self.assertEqual(nfa.accepts(w), dfa.accepts(w), f"word '{w}'")
                    if rx is not None:
                        self.assertEqual(bool(re.fullmatch(rx, w)), dfa.accepts(w),
                                         f"regex disagrees on '{w}'")


class TestExpectedResults(unittest.TestCase):

    def load(self, name):
        return subset_construction(
            NFA.from_json_file(os.path.join(ROOT, "examples", name)))

    def test1_ends_with_01(self):
        dfa = self.load("test1_ends_with_01.json")
        self.assertEqual(len(dfa.states), 3)
        self.assertEqual(dfa.set_name(dfa.start), "{q0}")
        self.assertEqual({dfa.set_name(s) for s in dfa.accepting}, {"{q0,q2}"})

    def test2_matches_textbook(self):
        """Sipser Example 1.41: reachable DFA for N4."""
        dfa = self.load("test2_textbook_N4.json")
        n = dfa.set_name
        table = {(n(s), a): n(dfa.transitions[(s, a)])
                 for s in dfa.states for a in dfa.alphabet}
        expected = {
            ("{1,3}", "a"): "{1,3}",     ("{1,3}", "b"): "{2}",
            ("{2}", "a"): "{2,3}",       ("{2}", "b"): "{3}",
            ("{2,3}", "a"): "{1,2,3}",   ("{2,3}", "b"): "{3}",
            ("{3}", "a"): "{1,3}",       ("{3}", "b"): "∅",
            ("{1,2,3}", "a"): "{1,2,3}", ("{1,2,3}", "b"): "{2,3}",
            ("∅", "a"): "∅",             ("∅", "b"): "∅",
        }
        self.assertEqual(table, expected)
        self.assertEqual(n(dfa.start), "{1,3}")
        self.assertEqual({n(s) for s in dfa.accepting}, {"{1,3}", "{1,2,3}"})

    def test3_second_last(self):
        self.assertEqual(len(self.load("test3_second_last_is_1.json").states), 4)

    def test4_unary(self):
        dfa = self.load("test4_unary_mod2_or_mod3.json")
        self.assertEqual(len(dfa.states), 7)
        for k in range(30):
            self.assertEqual(dfa.accepts("0" * k), k % 2 == 0 or k % 3 == 0)

    def test5_contains_aba(self):
        dfa = self.load("test5_contains_aba.json")
        self.assertTrue(dfa.accepts("bbabab"))
        self.assertFalse(dfa.accepts("abba"))


class TestInputHandling(unittest.TestCase):

    def test_text_format(self):
        nfa = NFA.from_text("q0 q1 q2", "0,1", "q0", "q2",
                            "q0, 0 -> q0, q1\nq0, 1 -> q0\n# comment\nq1, 1 -> q2")
        self.assertTrue(subset_construction(nfa).accepts("1101"))

    def test_epsilon_aliases(self):
        for alias in ("eps", "ε", "epsilon", "λ"):
            nfa = NFA.from_text("a b", "x", "a", "b", f"a, {alias} -> b")
            self.assertTrue(nfa.accepts(""))

    def test_invalid_inputs(self):
        with self.assertRaises(AutomatonError):
            NFA.from_text("q0", "a", "q9", "q0", "")          # bad start
        with self.assertRaises(AutomatonError):
            NFA.from_text("q0", "a", "q0", "q5", "")          # bad accept
        with self.assertRaises(AutomatonError):
            NFA.from_text("q0", "a", "q0", "q0", "q0, b -> q0")  # symbol not in Σ
        with self.assertRaises(AutomatonError):
            NFA.from_text("q0", "a", "q0", "q0", "q0, a -> q7")  # unknown target
        with self.assertRaises(AutomatonError):
            NFA.from_text("q0", "a", "q0", "q0", "q0 a q0")      # no arrow

    def test_only_reachable_states(self):
        # q2 is unreachable, so {q2} must NOT appear in the DFA
        nfa = NFA.from_text("q0 q1 q2", "a", "q0", "q1",
                            "q0, a -> q1\nq2, a -> q2")
        names = {subset_construction(nfa).set_name(s)
                 for s in subset_construction(nfa).states}
        self.assertEqual(names, {"{q0}", "{q1}", "∅"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
