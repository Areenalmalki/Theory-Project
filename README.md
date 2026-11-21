# NFA to DFA Conversion Tool
CSC339 – Theory of Computation, Course Project

This tool converts an NFA (including NFAs with ε-transitions) into an equivalent DFA using the subset construction algorithm. It shows the DFA states, the initial and accepting states, the transition table, and a state diagram of the result.

## Requirements

- Python 3.9 or newer
- The Python packages listed in `requirements.txt` (streamlit, graphviz, pandas)
- Graphviz, which is used to draw the diagrams

## Installation

Open a terminal inside the project folder:

```bash
cd Theory-Project
```

Install the Python packages:

```bash
python3 -m pip install -r requirements.txt
```

Install Graphviz:

- macOS: `brew install graphviz`
- Windows: download it from https://graphviz.org/download/ and tick "Add Graphviz to the system PATH" during setup
- Linux: `sudo apt install graphviz`

You can check that Graphviz is installed with `dot -V`.

## How to run

### Graphical interface

```bash
python3 -m streamlit run app.py
```

The interface opens in your browser at http://localhost:8501.

1. Pick one of the example NFAs from the sidebar, or type your own NFA.
2. Click **Convert to DFA**.
3. The DFA states, transition table and state diagram are shown below.
4. You can also enter strings in the test section to check them on both the NFA and the DFA.

Press `Ctrl + C` in the terminal to stop it.

### Tests

```bash
python3 -m unittest discover -s tests -v
```

## Entering an NFA

In the interface, write each transition on its own line:

```
q0, 0 -> q0, q1
q0, 1 -> q0
q1, 1 -> q2
```

Write `eps` for an ε-transition, for example `q0, eps -> q1`. A transition that is not written goes to the empty set.

The example NFAs in `examples/` are stored as JSON files like this:

```json
{
  "states": ["q0", "q1", "q2"],
  "alphabet": ["0", "1"],
  "start": "q0",
  "accepting": ["q2"],
  "transitions": {
    "q0": {"0": ["q0", "q1"], "1": ["q0"]},
    "q1": {"1": ["q2"]}
  }
}
```

## Files

- `automata.py`: NFA and DFA classes and the subset construction algorithm
- `app.py`: the graphical interface
- `visualize.py`: draws the state diagrams
- `examples/`: the five test NFAs
- `tests/`: automated tests
- `docs/`: screenshots and diagrams used in the report
- `Project_Report.pdf`: the project report

## Test cases

| File | Language | DFA states |
|------|----------|-----------|
| test1_ends_with_01 | strings over {0,1} ending with 01 | 3 |
| test2_textbook_N4 | textbook example N4 (has an ε-transition) | 6 |
| test3_second_last_is_1 | second symbol from the end is 1 | 4 |
| test4_unary_mod2_or_mod3 | 0^k where k is a multiple of 2 or 3 | 7 |
| test5_contains_aba | strings over {a,b} that contain aba | 6 |
