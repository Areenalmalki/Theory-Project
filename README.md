# NFA to DFA Conversion Tool — CSC339 Course Project

Converts a Nondeterministic Finite Automaton (NFA, with or without ε-moves) into an
equivalent Deterministic Finite Automaton (DFA) using the **Subset Construction Algorithm**,
and shows the DFA states, transition table, initial/accepting states and a state diagram.

---

## 1. Requirements

| What | Why |
|------|-----|
| **Python 3.9 or newer** | the program itself |
| Python packages: `streamlit`, `graphviz`, `pandas` | user interface, diagrams, tables |
| **Graphviz program** (recommended) | draws the diagrams as PNG/SVG |

### Step 1 – install the Python packages

Open a terminal (Command Prompt / PowerShell on Windows) **inside the project folder** and run:

```bash
pip install -r requirements.txt
```

(If `pip` is not found, use `python -m pip install -r requirements.txt`, or `py -m pip ...` on Windows.)

### Step 2 – install the Graphviz program

The `graphviz` Python package needs the Graphviz `dot` program:

- **Windows:** download the installer from <https://graphviz.org/download/> and, during setup, choose
  **"Add Graphviz to the system PATH"**. Close and reopen the terminal afterwards.
- **macOS:** `brew install graphviz`
- **Ubuntu / Debian:** `sudo apt install graphviz`

Check it with `dot -V`.

> If Graphviz is not installed, the app still works: the diagrams are drawn in the browser
> instead (only the PNG/SVG download buttons are unavailable).

---

## 2. Running the project

### Graphical interface (main tool)

```bash
streamlit run app.py
```

The browser opens automatically at **http://localhost:8501**
(if it does not, open that address yourself; use `python -m streamlit run app.py` if `streamlit` is not found).

1. Choose an example NFA from the sidebar, upload a JSON file, or type your own NFA.
2. Press **▶ Convert to DFA**.
3. View the DFA states, initial and accepting states, transition table, step-by-step trace and state diagram.
4. Optionally type strings in **Test strings** to run them on both the NFA and the DFA.

Stop the server with `Ctrl + C` in the terminal.

### Command line (optional)

```bash
python main.py examples/test2_textbook_N4.json
python main.py examples/*.json --out output --check 01 1101
python main.py examples/test3_second_last_is_1.json --short     # names A, B, C …
```

Prints the NFA, every step of the subset construction and the DFA transition table,
and saves NFA/DFA diagrams as PNG files in the `output/` folder.

### Automated tests

```bash
python -m unittest discover -s tests -v
```

Checks every example DFA against its NFA on all strings of length 0–10, against the
expected language, and against the textbook DFA (11 tests).

---

## 3. Entering an NFA

In the interface:

| Field | Example |
|-------|---------|
| States Q | `q0, q1, q2` |
| Alphabet Σ | `0, 1` |
| Initial state | `q0` |
| Accepting states F | `q2` |
| Transitions (one per line) | `q0, 0 -> q0, q1`<br>`q0, 1 -> q0`<br>`q1, 1 -> q2` |

- Use `eps` (or `ε`, `epsilon`, `λ`) for empty moves, e.g. `q0, eps -> q1`.
- A missing rule means the transition goes to the empty set ∅.
- Lines starting with `#` are comments.

JSON format (files in `examples/`):

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

---

## 4. Project structure

```
NFA_to_DFA_Tool/
├── app.py                  Streamlit graphical user interface
├── automata.py             NFA/DFA classes + subset construction algorithm
├── visualize.py            Graphviz state diagrams
├── main.py                 command-line version
├── requirements.txt
├── Project_Report.pdf      project report
├── examples/               5 test NFAs (JSON)
├── tests/                  automated tests
└── docs/
    ├── screenshots/        screenshots of the tool
    ├── diagrams/           NFA and DFA diagrams of every test case
    └── sample_output.txt   command-line output for all examples
```

## 5. Test NFAs

| File | Language | DFA states |
|------|----------|-----------|
| test1_ends_with_01 | strings over {0,1} ending with 01 | 3 |
| test2_textbook_N4 | Sipser Example 1.41 (ε-move, dead state) | 6 |
| test3_second_last_is_1 | second-to-last symbol is 1 | 4 |
| test4_unary_mod2_or_mod3 | 0^k, k multiple of 2 or 3 (ε-NFA) | 7 |
| test5_contains_aba | strings over {a,b} containing aba | 6 |
