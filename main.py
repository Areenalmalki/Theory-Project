"""
main.py  -  command-line version of the NFA -> DFA Conversion Tool.

Usage
    python main.py examples/test1_ends_with_01.json
    python main.py examples/test2_textbook_N4.json --short --out output
    python main.py examples/*.json --check "abba" "ab"

For the graphical interface run:   streamlit run app.py
"""

import argparse
import os
import sys

from automata import EPSILON, NFA, AutomatonError, subset_construction
from visualize import dfa_to_graph, graphviz_available, nfa_to_graph, render


def describe_nfa(nfa: NFA) -> str:
    lines = [
        f"  Q  = {{{', '.join(nfa.states)}}}",
        f"  Σ  = {{{', '.join(nfa.alphabet)}}}",
        f"  q0 = {nfa.start}",
        f"  F  = {{{', '.join(q for q in nfa.states if q in nfa.accepting)}}}",
        "  δ  :",
    ]
    for src in nfa.states:
        for sym in nfa.alphabet + [EPSILON]:
            d = nfa.transitions.get((src, sym))
            if d:
                lines.append(f"       δ({src}, {sym}) = {{{', '.join(sorted(d, key=nfa.states.index))}}}")
    return "\n".join(lines)


def process(path: str, short: bool, out_dir: str, words) -> None:
    nfa = NFA.from_json_file(path)
    base = os.path.splitext(os.path.basename(path))[0]
    print("=" * 70)
    print(f"Input file: {path}")
    print("-" * 70)
    print("NFA")
    print(describe_nfa(nfa))

    dfa = subset_construction(nfa)

    print("-" * 70)
    print("Subset construction steps")
    for s in dfa.steps:
        print("  " + s)

    print("-" * 70)
    print(f"DFA  ({len(dfa.states)} reachable states)")
    print("  States     :", ", ".join(dfa.name(s, short) for s in dfa.states))
    print("  Initial    :", dfa.name(dfa.start, short))
    print("  Accepting  :", ", ".join(dfa.name(s, short) for s in dfa.states
                                     if s in dfa.accepting) or "none")
    print("\nTransition table   (→ initial, * accepting)")
    print(dfa.table_text(short))

    for w in words:
        print(f"\n  '{w}':  NFA {'accepts' if nfa.accepts(w) else 'rejects'}"
              f",  DFA {'accepts' if dfa.accepts(w) else 'rejects'}")

    if out_dir:
        if graphviz_available():
            os.makedirs(out_dir, exist_ok=True)
            p1 = render(nfa_to_graph(nfa), os.path.join(out_dir, base + "_nfa"))
            p2 = render(dfa_to_graph(dfa, short), os.path.join(out_dir, base + "_dfa"))
            print(f"\nDiagrams saved: {p1}, {p2}")
        else:
            print("\n[!] Graphviz 'dot' not found - diagrams not saved. See README.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert an NFA (JSON) to an equivalent DFA.")
    ap.add_argument("files", nargs="+", help="NFA JSON file(s)")
    ap.add_argument("--short", action="store_true",
                    help="name DFA states A, B, C ... instead of {q0,q1}")
    ap.add_argument("--out", default="output",
                    help="folder for PNG diagrams (use '' to skip)")
    ap.add_argument("--check", nargs="*", default=[], metavar="WORD",
                    help="words to test on both the NFA and the DFA")
    args = ap.parse_args()

    for f in args.files:
        try:
            process(f, args.short, args.out, args.check)
        except (AutomatonError, OSError, ValueError) as exc:
            print(f"Error in {f}: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
