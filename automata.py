# automata.py
# NFA and DFA classes, and the subset construction algorithm.
#
# NFA: N = (Q, Σ, δ, q0, F), where δ can also have ε-moves.
# DFA: each state is a set of NFA states.
#   start state        = E({q0})
#   δ'(R, a)           = E(move(R, a))
#   accepting states   = sets that contain at least one state of F
# We only build the states we can reach from the start state.

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Set, Tuple

# Symbols that the user may type to mean "epsilon" (the empty string).
EPSILON = "ε"
EPSILON_ALIASES = {"ε", "eps", "epsilon", "e", "λ", "lambda", ""}


class AutomatonError(ValueError):
    """Raised when an automaton specification is invalid."""


def _norm_symbol(sym: str) -> str:
    """Map every accepted spelling of epsilon to the single EPSILON symbol."""
    s = sym.strip()
    return EPSILON if s.lower() in EPSILON_ALIASES else s


#  NFA

@dataclass
class NFA:
    states: List[str]
    alphabet: List[str]
    start: str
    accepting: Set[str]
    # (state, symbol) -> set of next states ; symbol may be EPSILON
    transitions: Dict[Tuple[str, str], Set[str]] = field(default_factory=dict)

    #  validation
    def validate(self) -> None:
        if not self.states:
            raise AutomatonError("The set of states Q is empty.")
        if len(set(self.states)) != len(self.states):
            raise AutomatonError("Duplicate state names in Q.")
        if not self.alphabet:
            raise AutomatonError("The input alphabet Σ is empty.")
        if EPSILON in self.alphabet:
            raise AutomatonError("ε must not be part of the alphabet Σ "
                                 "(use it only inside transitions).")
        if len(set(self.alphabet)) != len(self.alphabet):
            raise AutomatonError("Duplicate symbols in Σ.")
        q = set(self.states)
        if self.start not in q:
            raise AutomatonError(f"Initial state '{self.start}' is not in Q.")
        bad = self.accepting - q
        if bad:
            raise AutomatonError(f"Accepting state(s) {sorted(bad)} not in Q.")
        sigma = set(self.alphabet) | {EPSILON}
        for (src, sym), dsts in self.transitions.items():
            if src not in q:
                raise AutomatonError(f"Transition from unknown state '{src}'.")
            if sym not in sigma:
                raise AutomatonError(
                    f"Transition δ({src}, {sym}) uses symbol '{sym}' "
                    f"that is not in Σ.")
            for d in dsts:
                if d not in q:
                    raise AutomatonError(
                        f"Transition δ({src}, {sym}) goes to unknown state '{d}'.")

    @property
    def has_epsilon(self) -> bool:
        return any(sym == EPSILON and dsts
                   for (_, sym), dsts in self.transitions.items())

    # core NFA operations
    def move(self, states: Iterable[str], symbol: str) -> Set[str]:
        """∪ δ(r, symbol) for r in states."""
        out: Set[str] = set()
        for r in states:
            out |= self.transitions.get((r, symbol), set())
        return out

    def epsilon_closure(self, states: Iterable[str]) -> FrozenSet[str]:
        """E(R): every state reachable from R using 0 or more ε-moves."""
        closure = set(states)
        stack = list(closure)
        while stack:
            r = stack.pop()
            for nxt in self.transitions.get((r, EPSILON), set()):
                if nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)
        return frozenset(closure)

    def accepts(self, word: str) -> bool:
        """Direct NFA simulation (used to verify the generated DFA)."""
        current = self.epsilon_closure({self.start})
        for ch in word:
            current = self.epsilon_closure(self.move(current, ch))
            if not current:
                return False
        return bool(current & self.accepting)

    #  (de)serialisation
    @classmethod
    def from_dict(cls, data: dict) -> "NFA":
        try:
            states = [str(s).strip() for s in data["states"]]
            alphabet = [str(a).strip() for a in data["alphabet"]]
            start = str(data["start"]).strip()
            accepting = {str(s).strip() for s in data["accepting"]}
            raw = data.get("transitions", {})
        except KeyError as exc:
            raise AutomatonError(f"Missing field: {exc}") from None

        trans: Dict[Tuple[str, str], Set[str]] = {}
        # Format: {"q0": {"a": ["q0","q1"], "ε": ["q2"]}, ...}
        for src, row in raw.items():
            for sym, dsts in row.items():
                if isinstance(dsts, str):
                    dsts = [dsts]
                key = (str(src).strip(), _norm_symbol(str(sym)))
                trans.setdefault(key, set()).update(str(d).strip() for d in dsts)
        nfa = cls(states, alphabet, start, accepting, trans)
        nfa.validate()
        return nfa

    def to_dict(self) -> dict:
        rows: Dict[str, Dict[str, List[str]]] = {}
        for (src, sym), dsts in self.transitions.items():
            if dsts:
                rows.setdefault(src, {})[sym] = sorted(dsts)
        return {
            "states": self.states,
            "alphabet": self.alphabet,
            "start": self.start,
            "accepting": sorted(self.accepting),
            "transitions": rows,
        }

    @classmethod
    def from_json_file(cls, path: str) -> "NFA":
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    @classmethod
    def from_text(cls, states: str, alphabet: str, start: str,
                  accepting: str, transitions: str) -> "NFA":
        # Reads the NFA from the text boxes in the interface.
        # Lists can be separated by commas or spaces.
        # Each transition goes on its own line, like:  q0, a -> q0, q1
        # Empty lines and lines that start with # are skipped.
        def split(s: str) -> List[str]:
            return [t for t in s.replace(",", " ").split() if t]

        trans: Dict[Tuple[str, str], Set[str]] = {}
        for n, line in enumerate(transitions.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" not in line:
                raise AutomatonError(
                    f"Line {n}: expected 'state, symbol -> s1, s2'  got '{line}'")
            left, right = line.split("->", 1)
            parts = [p.strip() for p in left.split(",")]
            if len(parts) != 2 or not parts[0]:
                raise AutomatonError(
                    f"Line {n}: left side must be 'state, symbol'  got '{left.strip()}'")
            src, sym = parts[0], _norm_symbol(parts[1])
            dsts = split(right)
            if right.strip() in {"∅", "{}", "-"}:
                dsts = []
            trans.setdefault((src, sym), set()).update(dsts)

        nfa = cls(split(states), split(alphabet), start.strip(),
                  set(split(accepting)), trans)
        nfa.validate()
        return nfa

    def transitions_as_text(self) -> str:
        lines = []
        for src in self.states:
            for sym in self.alphabet + [EPSILON]:
                dsts = self.transitions.get((src, sym))
                if dsts:
                    s = "eps" if sym == EPSILON else sym
                    lines.append(f"{src}, {s} -> {', '.join(sorted(dsts, key=self.states.index))}")
        return "\n".join(lines)



#  DFA

@dataclass
class DFA:
    states: List[FrozenSet[str]]                # in discovery (BFS) order
    alphabet: List[str]
    start: FrozenSet[str]
    accepting: Set[FrozenSet[str]]
    transitions: Dict[Tuple[FrozenSet[str], str], FrozenSet[str]]
    nfa_order: List[str]                        # to print sets nicely
    steps: List[str] = field(default_factory=list)  # trace for the UI

    #  naming helpers
    def set_name(self, s: FrozenSet[str]) -> str:
        if not s:
            return "∅"
        order = {q: i for i, q in enumerate(self.nfa_order)}
        return "{" + ",".join(sorted(s, key=lambda q: order.get(q, 10**9))) + "}"

    def name(self, s: FrozenSet[str]) -> str:
        return self.set_name(s)

    # behaviour
    def accepts(self, word: str) -> bool:
        cur = self.start
        for ch in word:
            if ch not in self.alphabet:
                return False
            cur = self.transitions[(cur, ch)]
        return cur in self.accepting

    def run(self, word: str) -> List[FrozenSet[str]]:
        """Sequence of DFA states visited while reading `word`"""
        path = [self.start]
        cur = self.start
        for ch in word:
            cur = self.transitions[(cur, ch)]
            path.append(cur)
        return path

    def transition_table(self) -> List[Dict[str, str]]:
        """Rows ready for display: marks → start and * accepting"""
        rows = []
        for s in self.states:
            mark = ("→" if s == self.start else "") + ("*" if s in self.accepting else "")
            row = {"": mark, "DFA state": self.name(s)}
            for a in self.alphabet:
                row[a] = self.name(self.transitions[(s, a)])
            rows.append(row)
        return rows



#  Subset Construction

def subset_construction(nfa: NFA) -> DFA:
    # Converts the NFA to a DFA using subset construction.
    # 1. The start state is E({q0}).
    # 2. Take a state R from the queue. For each symbol a,
    #    U = E(move(R, a)). If U is new, add it to the queue.
    # 3. A DFA state is accepting if it has a state from F.
    # We only expand states from the queue, so we get the reachable
    # states only. If ∅ shows up, it is the dead state.
    nfa.validate()
    steps: List[str] = []
    fmt = lambda s: "∅" if not s else "{" + ",".join(
        sorted(s, key=nfa.states.index)) + "}"

    start = nfa.epsilon_closure({nfa.start})
    steps.append(f"Start state: E({{{nfa.start}}}) = {fmt(start)}")

    dfa_states: List[FrozenSet[str]] = [start]
    seen: Set[FrozenSet[str]] = {start}
    queue: deque = deque([start])
    delta: Dict[Tuple[FrozenSet[str], str], FrozenSet[str]] = {}

    while queue:
        R = queue.popleft()
        for a in nfa.alphabet:
            moved = nfa.move(R, a)
            U = nfa.epsilon_closure(moved)
            delta[(R, a)] = U
            new = U not in seen
            if new:
                seen.add(U)
                dfa_states.append(U)
                queue.append(U)
            if nfa.has_epsilon:
                steps.append(f"δ'({fmt(R)}, {a}) = E({fmt(moved)}) = {fmt(U)}"
                             + ("   ← new state" if new else ""))
            else:
                steps.append(f"δ'({fmt(R)}, {a}) = {fmt(U)}"
                             + ("   ← new state" if new else ""))

    accepting = {S for S in dfa_states if S & nfa.accepting}
    steps.append("Accepting states (contain a state of F = "
                 f"{fmt(nfa.accepting)}): "
                 + (", ".join(fmt(S) for S in dfa_states if S in accepting) or "none"))

    return DFA(dfa_states, list(nfa.alphabet), start, accepting, delta,
               list(nfa.states), steps)
