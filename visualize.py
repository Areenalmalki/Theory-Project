"""
visualize.py
------------
Builds Graphviz state diagrams for the NFA (input) and the DFA (output).

Conventions used in the drawings
    * an arrow coming from nowhere points to the initial state
    * double circle  = accepting state
    * edges between the same pair of states are merged: label "a, b"
    * the dead state ∅ is drawn dashed / grey so it is easy to spot
"""

from __future__ import annotations

import shutil
from collections import defaultdict
from typing import Dict, Tuple

import graphviz

from automata import DFA, EPSILON, NFA

FONT = "Helvetica"


def graphviz_available() -> bool:
    """True if the Graphviz 'dot' program is installed (needed for PNG/SVG files)."""
    return shutil.which("dot") is not None


def _base_graph(name: str) -> graphviz.Digraph:
    g = graphviz.Digraph(name, format="png")
    g.attr(rankdir="LR", bgcolor="white", pad="0.3", nodesep="0.5", ranksep="0.7")
    g.attr("node", fontname=FONT, fontsize="13", style="filled",
           fillcolor="#EAF2FB", color="#1F4E79", penwidth="1.5")
    g.attr("edge", fontname=FONT, fontsize="12", color="#333333", arrowsize="0.8")
    g.node("__start__", shape="none", label="", width="0", height="0")
    return g


def nfa_to_graph(nfa: NFA) -> graphviz.Digraph:
    g = _base_graph("NFA")
    for q in nfa.states:
        g.node(q, q, shape="doublecircle" if q in nfa.accepting else "circle")
    g.edge("__start__", nfa.start, label="start")

    labels: Dict[Tuple[str, str], list] = defaultdict(list)
    for (src, sym), dsts in nfa.transitions.items():
        for d in dsts:
            labels[(src, d)].append(sym)
    order = nfa.alphabet + [EPSILON]
    for (src, d), syms in labels.items():
        syms = sorted(set(syms), key=order.index)
        g.edge(src, d, label=", ".join(syms))
    return g


def dfa_to_graph(dfa: DFA, short_names: bool = False) -> graphviz.Digraph:
    g = _base_graph("DFA")
    names = dfa.short_names()
    node_id = {s: f"s{i}" for i, s in enumerate(dfa.states)}

    for s in dfa.states:
        if short_names:
            label = names[s] if not s else f"{names[s]}\n{dfa.set_name(s)}"
        else:
            label = dfa.set_name(s)
        attrs = {"shape": "doublecircle" if s in dfa.accepting else "circle"}
        if not s:  # dead / trap state
            attrs.update(style="filled,dashed", fillcolor="#F2F2F2", color="#888888")
        elif s in dfa.accepting:
            attrs.update(fillcolor="#DDF0DD", color="#2E7D32")
        g.node(node_id[s], label, **attrs)

    g.edge("__start__", node_id[dfa.start], label="start")

    labels: Dict[Tuple[str, str], list] = defaultdict(list)
    for (src, a), dst in dfa.transitions.items():
        labels[(node_id[src], node_id[dst])].append(a)
    for (u, v), syms in labels.items():
        syms = sorted(syms, key=dfa.alphabet.index)
        g.edge(u, v, label=", ".join(syms))
    return g


def render(graph: graphviz.Digraph, out_path_no_ext: str, fmt: str = "png") -> str:
    """Write the diagram to disk (requires Graphviz). Returns the file path."""
    graph.format = fmt
    return graph.render(out_path_no_ext, cleanup=True)


def to_bytes(graph: graphviz.Digraph, fmt: str = "png") -> bytes:
    """Render in memory (requires Graphviz)."""
    return graph.pipe(format=fmt)
