"""
app.py  -  Graphical user interface for the NFA -> DFA Conversion Tool.

Run with:   streamlit run app.py
Then open the address shown in the terminal (normally http://localhost:8501).
"""

import glob
import json
import os

import pandas as pd
import streamlit as st

from automata import NFA, AutomatonError, subset_construction
from visualize import dfa_to_graph, graphviz_available, nfa_to_graph, to_bytes

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE_FILES = sorted(glob.glob(os.path.join(HERE, "examples", "*.json")))
HAS_DOT = graphviz_available()

st.set_page_config(page_title="NFA → DFA Converter", page_icon="🔁", layout="wide")


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def load_into_form(nfa: NFA) -> None:
    st.session_state.f_states = ", ".join(nfa.states)
    st.session_state.f_alphabet = ", ".join(nfa.alphabet)
    st.session_state.f_start = nfa.start
    st.session_state.f_accept = ", ".join(q for q in nfa.states if q in nfa.accepting)
    st.session_state.f_trans = nfa.transitions_as_text()
    st.session_state.pop("dfa", None)


def example_label(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("name", os.path.basename(path))


def on_example_change() -> None:
    choice = st.session_state.example_choice
    if choice == "— empty —":
        for k in ("f_states", "f_alphabet", "f_start", "f_accept", "f_trans"):
            st.session_state[k] = ""
        st.session_state.pop("dfa", None)
    else:
        load_into_form(NFA.from_json_file(EXAMPLES[choice]))


def show_graph(graph, key: str) -> None:
    if HAS_DOT:
        st.image(to_bytes(graph, "png"), use_container_width=False)
        c1, c2 = st.columns(2)
        c1.download_button("⬇ PNG", to_bytes(graph, "png"), f"{key}.png", "image/png",
                           key=f"{key}_png")
        c2.download_button("⬇ SVG", to_bytes(graph, "svg"), f"{key}.svg",
                           "image/svg+xml", key=f"{key}_svg")
    else:  # Graphviz program not installed: let the browser draw it
        st.graphviz_chart(graph.source)


EXAMPLES = {example_label(p): p for p in EXAMPLE_FILES}

# first run: pre-load example 1 so the page is never empty
if "f_states" not in st.session_state:
    if EXAMPLE_FILES:
        load_into_form(NFA.from_json_file(EXAMPLE_FILES[0]))
    else:
        on_example_change()

# --------------------------------------------------------------------------- #
#  sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("📂 Load an NFA")
    st.selectbox("Example NFAs", ["— empty —"] + list(EXAMPLES),
                 index=1 if EXAMPLES else 0,
                 key="example_choice", on_change=on_example_change)

    up = st.file_uploader("…or upload a JSON file", type="json")
    if up is not None and st.session_state.get("_last_upload") != up.file_id:
        try:
            load_into_form(NFA.from_dict(json.load(up)))
            st.session_state._last_upload = up.file_id
            st.success("NFA loaded from file.")
            st.rerun()
        except (AutomatonError, ValueError) as exc:
            st.error(f"Invalid file: {exc}")

    st.divider()
    st.header("⚙ Display")
    short = st.toggle("Rename DFA states A, B, C …", value=False,
                      help="Show short names; the subset of NFA states is still displayed.")
    st.divider()
    st.caption("**Input format for transitions** – one rule per line:\n\n"
               "`state, symbol -> next1, next2`\n\n"
               "Use `eps` (or `ε`) for ε-moves. Missing rules mean δ = ∅. "
               "Lines starting with `#` are comments.")
    if not HAS_DOT:
        st.warning("Graphviz program not found – diagrams are drawn in the "
                   "browser and cannot be downloaded. See README.")

# --------------------------------------------------------------------------- #
#  main area
# --------------------------------------------------------------------------- #
st.title("🔁 NFA → DFA Conversion Tool")
st.caption("CSC339 – Theory of Computation · Subset Construction Algorithm")

left, right = st.columns([1, 1.25], gap="large")

with left:
    st.subheader("1 · Enter the NFA")
    st.text_input("States  Q", key="f_states", placeholder="q0, q1, q2")
    st.text_input("Alphabet  Σ", key="f_alphabet", placeholder="0, 1")
    c1, c2 = st.columns(2)
    c1.text_input("Initial state  q₀", key="f_start", placeholder="q0")
    c2.text_input("Accepting states  F", key="f_accept", placeholder="q2")
    st.text_area("Transition function  δ", key="f_trans", height=210,
                 placeholder="q0, 0 -> q0, q1\nq0, 1 -> q0\nq1, 1 -> q2")

    nfa, error = None, None
    try:
        nfa = NFA.from_text(st.session_state.f_states, st.session_state.f_alphabet,
                            st.session_state.f_start, st.session_state.f_accept,
                            st.session_state.f_trans)
    except AutomatonError as exc:
        error = str(exc)

    if error:
        st.error(error)

    if st.button("▶ Convert to DFA", type="primary", use_container_width=True,
                 disabled=nfa is None):
        st.session_state.dfa = subset_construction(nfa)
        st.session_state.dfa_nfa = nfa.to_dict()

    if nfa is not None:
        st.download_button("💾 Save this NFA as JSON",
                           json.dumps(nfa.to_dict(), indent=2, ensure_ascii=False),
                           "nfa.json", "application/json", use_container_width=True)

with right:
    st.subheader("NFA state diagram")
    if nfa is not None:
        show_graph(nfa_to_graph(nfa), "nfa")
    else:
        st.info("Fix the input to see the NFA diagram.")

# --------------------------------------------------------------------------- #
#  results
# --------------------------------------------------------------------------- #
dfa = st.session_state.get("dfa")
if dfa is not None and nfa is not None and st.session_state.get("dfa_nfa") != nfa.to_dict():
    st.warning("The NFA was edited – press **Convert to DFA** again to update the result.")

if dfa is not None:
    st.divider()
    st.subheader("2 · Resulting DFA")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("DFA states", len(dfa.states))
    m2.metric("Initial state", dfa.name(dfa.start, short))
    m3.metric("Accepting states", len(dfa.accepting))
    m4.metric("Dead state ∅", "yes" if frozenset() in dfa.states else "no")

    st.markdown("**States  Q′:**  " + ",  ".join(f"`{dfa.name(s, short)}`" for s in dfa.states))
    st.markdown("**Initial state  q₀′:**  " + f"`{dfa.name(dfa.start, short)}`")
    st.markdown("**Accepting states  F′:**  " + (",  ".join(
        f"`{dfa.name(s, short)}`" for s in dfa.states if s in dfa.accepting) or "none"))

    t1, t2 = st.columns([1, 1.25], gap="large")
    with t1:
        st.markdown("**Transition table**  (→ initial, * accepting)")
        st.dataframe(pd.DataFrame(dfa.transition_table(short)),
                     hide_index=True, use_container_width=True)
        with st.expander("Subset construction – step by step", expanded=False):
            st.code("\n".join(dfa.steps), language=None)
        st.download_button("💾 Download DFA as JSON",
                           json.dumps(dfa.to_dict(short), indent=2, ensure_ascii=False),
                           "dfa.json", "application/json")
    with t2:
        st.markdown("**DFA state diagram**")
        show_graph(dfa_to_graph(dfa, short), "dfa")

    st.divider()
    st.subheader("3 · Test strings")
    words = st.text_input("Enter strings separated by spaces (write `ε` for the empty string)",
                          value="", key="words", placeholder="01 1101 ε 10")
    if words.strip():
        sim = NFA.from_dict(st.session_state.dfa_nfa)
        rows = []
        for w in words.split():
            w = "" if w in ("ε", "eps") else w
            bad = [c for c in w if c not in dfa.alphabet]
            if bad:
                rows.append({"string": w or "ε", "NFA": "—", "DFA": "—",
                             "DFA path": f"symbol '{bad[0]}' not in Σ", "agree": "—"})
                continue
            n_ok, d_ok = sim.accepts(w), dfa.accepts(w)
            path = " → ".join(dfa.name(s, short) for s in dfa.run(w))
            rows.append({"string": w or "ε",
                         "NFA": "✅ accept" if n_ok else "❌ reject",
                         "DFA": "✅ accept" if d_ok else "❌ reject",
                         "DFA path": path, "agree": "✔" if n_ok == d_ok else "✘"})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
