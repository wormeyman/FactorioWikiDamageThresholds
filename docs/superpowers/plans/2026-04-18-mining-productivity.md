# Mining Productivity Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `factorio_mining.py` that generates a MediaWiki thresholds table for Mining Productivity (research), showing miners needed per full belt at research levels 0-110 (steps of 10).

**Architecture:** New standalone file (`factorio_mining.py`) with data constants, a cost formula function, a core `miners_needed` calculation, and text/wiki output functions. 4 wiki tables (one per belt type), each with 3 data columns (Electric mining drill, Big mining drill, Big mining drill + quad stacking). No test framework in this project - verification is done by running the script and checking spot values.

**Tech Stack:** Python 3, `math.ceil`, `sys.argv`, MediaWiki markup

---

## Files

- **Create:** `factorio_mining.py`
- **Create (generated):** `WikiArticles/MiningProductivityResearch.txt`
- **Modify:** `CLAUDE.md` (add factorio_mining.py entry + verification commands)
- **Modify:** `README.md` (add mining productivity entry)

---

### Task 1: Scaffold factorio_mining.py with data model and core math

**Files:**
- Create: `factorio_mining.py`

- [ ] **Step 1: Create the file with constants and core functions**

Create `factorio_mining.py`:

```python
#!/usr/bin/env python3
"""
Factorio mining productivity threshold calculator.

Shows how many mining drills are needed to fully saturate each belt type
at each research level (0, 10, 20, ..., 110). Outputs plain text or MediaWiki markup.

Usage:
    python3 factorio_mining.py [--wiki]

    --wiki: MediaWiki markup  (default: text)
"""
import math
import sys

STACK_SIZE = 4  # Quad stacking from Gleba research

# (display_name, base_speed items/s, stacking)
MINERS = [
    ('Electric mining drill', 0.5, False),
    ('Big mining drill',      2.5, False),
    ('Big mining drill',      2.5, True),   # with quad stacking
]

# (display_name, lane_speed items/s per lane, space_age)
BELTS = [
    ('Transport belt',         7.5,  False),
    ('Fast transport belt',    15.0, False),
    ('Express transport belt', 22.5, False),
    ('Turbo transport belt',   30.0, True),
]

LEVELS = list(range(0, 111, 10))

TECH_NAME = 'Mining productivity (research)'


def _si(n: float) -> str:
    """Format a number with SI suffix (k, M, G, T), dropping trailing zeros."""
    n = int(round(n))
    if n < 1_000:
        return str(n)
    if n < 1_000_000:
        return f'{n / 1_000:.2f}'.rstrip('0').rstrip('.') + 'k'
    if n < 1_000_000_000:
        return f'{n / 1_000_000:.3f}'.rstrip('0').rstrip('.') + 'M'
    if n < 1_000_000_000_000:
        return f'{n / 1_000_000_000:.3f}'.rstrip('0').rstrip('.') + 'G'
    return f'{n / 1_000_000_000_000:.3f}'.rstrip('0').rstrip('.') + 'T'


def cumulative_cost(level: int) -> str:
    """Cumulative Space Age research cost through a given level, as SI string.

    Level 1: 250 (Automation + Logistic)
    Level 2: 750 (+ 500 Chemical)
    Level N>=3: 750 + 500*(N-2)*(N-1)  [arithmetic: 1000*(N-2) per level]
    """
    if level == 0:
        return '-'
    if level == 1:
        return _si(250)
    cost = 750 + 500 * (level - 2) * (level - 1)
    return _si(cost)


def miners_needed(lane_speed: float, base_speed: float, level: int,
                  stacking: bool = False) -> int:
    """Total drills for both lanes of a belt at a given research level.

    Miners deposit on one side only, so both-lane total = ceil(lane * 2 / speed).
    With stacking, the belt lane capacity is multiplied by STACK_SIZE.
    """
    effective_lane = lane_speed * (STACK_SIZE if stacking else 1)
    effective_miner = base_speed * (1 + 0.1 * level)
    return math.ceil(effective_lane * 2 / effective_miner)


if __name__ == '__main__':
    pass
```

- [ ] **Step 2: Verify core math with spot checks**

Run:
```bash
python3 -c "
from factorio_mining import miners_needed, cumulative_cost

# Level 0, Yellow lane (7.5/s), EMD (0.5/s): ceil(7.5*2/0.5) = 30
assert miners_needed(7.5, 0.5, 0) == 30, miners_needed(7.5, 0.5, 0)

# Level 110, Green/Turbo lane (30/s), BMD (2.5/s): ceil(30*2/(2.5*12)) = ceil(2.0) = 2
assert miners_needed(30.0, 2.5, 110) == 2, miners_needed(30.0, 2.5, 110)

# Level 20, Yellow lane, BMD: ceil(7.5*2/(2.5*3)) = ceil(2.0) = 2
assert miners_needed(7.5, 2.5, 20) == 2, miners_needed(7.5, 2.5, 20)

# Level 110, Yellow, BMD+stacking: ceil(7.5*4*2/(2.5*12)) = ceil(2.0) = 2
assert miners_needed(7.5, 2.5, 110, stacking=True) == 2, miners_needed(7.5, 2.5, 110, stacking=True)

# Cost checks
assert cumulative_cost(0) == '-'
assert cumulative_cost(1) == '250'
assert cumulative_cost(2) == '750'   # 250+500
assert cumulative_cost(3) == '1.75k' # 250+500+1000
assert cumulative_cost(10) == '36.75k'  # 750 + 500*8*9

print('All checks passed')
"
```

Expected output: `All checks passed`

- [ ] **Step 3: Commit**

```bash
git add factorio_mining.py
git commit -m "feat: scaffold factorio_mining.py with data model and core math"
```

---

### Task 2: Implement text output

**Files:**
- Modify: `factorio_mining.py`

- [ ] **Step 1: Add print_text function and CLI**

Replace the `if __name__ == '__main__': pass` block with:

```python
def print_text() -> None:
    """Print plain-text tables for all belt types."""
    for belt_name, lane_speed, sa in BELTS:
        sa_tag = ' [SA]' if sa else ''
        total = lane_speed * 2
        stacked_total = total * STACK_SIZE
        print(f'\n=== {belt_name}{sa_tag} ({total:.0f}/s, stacked {stacked_total:.0f}/s) ===')
        headers = [
            'EMD / No modules',
            'BMD / No modules',
            'BMD / No modules + stack',
        ]
        w = 26
        hdr = f"{'Level':>6}  {'Cost':>8}  " + '  '.join(f'{h[:w]:>{w}}' for h in headers)
        print(hdr)
        print('-' * len(hdr))
        for lvl in LEVELS:
            vals = [miners_needed(lane_speed, m[1], lvl, m[2]) for m in MINERS]
            cost = cumulative_cost(lvl)
            row = f'{lvl:>6}  {cost:>8}  ' + '  '.join(f'{v:>{w}}' for v in vals)
            print(row)


if __name__ == '__main__':
    args = sys.argv[1:]
    wiki = '--wiki' in args
    if wiki:
        print('(wiki output not yet implemented)')
    else:
        print_text()
```

- [ ] **Step 2: Run and visually verify text output**

Run:
```bash
python3 factorio_mining.py
```

Expected: 4 tables printed. Spot-check Yellow belt level 0 EMD = 30, level 110 BMD = 2, level 110 BMD+stack = 2.

- [ ] **Step 3: Commit**

```bash
git add factorio_mining.py
git commit -m "feat: add text output to factorio_mining.py"
```

---

### Task 3: Implement wiki table output

**Files:**
- Modify: `factorio_mining.py`

- [ ] **Step 1: Add wiki icon maps and print_wiki_table function**

Add after the `print_text` function (before `if __name__ == '__main__':`):

```python
_MINER_ICONS = {
    'Electric mining drill': '{{Icon|Electric mining drill}}',
    'Big mining drill':      '{{Icon|Big mining drill|space-age=yes}}',
}

_BELT_ICONS = {
    'Transport belt':         '{{Icon|Transport belt}}',
    'Fast transport belt':    '{{Icon|Fast transport belt}}',
    'Express transport belt': '{{Icon|Express transport belt}}',
    'Turbo transport belt':   '{{Icon|Turbo transport belt|space-age=yes}}',
}


def print_wiki_table(belt_name: str, lane_speed: float, sa: bool) -> None:
    """Emit a single MediaWiki wikitable for one belt type."""
    n_miners = len(MINERS)
    n_levels = len(LEVELS)
    sa_tag = '{{SA}}' if sa else ''
    belt_icon = _BELT_ICONS[belt_name]
    emd_icon = _MINER_ICONS['Electric mining drill']
    bmd_icon = _MINER_ICONS['Big mining drill']

    print(f'=== {belt_icon} {belt_name}{sa_tag} ===')
    print(f'<!-- Mining productivity thresholds: {belt_name} -->')
    print('{| class="wikitable" style="text-align:center;"')

    # 2-row header: EMD gets rowspan=2 (single config), BMD gets colspan=2
    print(
        f'! rowspan="2" | Level'
        f' !! rowspan="2" | Cumulative<br>research cost'
        f' !! rowspan="2" | {emd_icon} Electric mining drill<br>No modules'
        f' !! colspan="2" | {bmd_icon} Big mining drill'
    )
    print('|-')
    print('! No modules !! No modules +<br>quad stacking')
    print('|-')

    # Precompute all values
    col_values = [
        [miners_needed(lane_speed, base_speed, lvl, stacking) for lvl in LEVELS]
        for _, base_speed, stacking in MINERS
    ]

    # Floor = value at level 110 (last row); rowspan starts at first row reaching it
    floor_row = []
    for col in col_values:
        floor_val = col[-1]
        floor_row.append(next(ri for ri, v in enumerate(col) if v == floor_val))

    floored = [False] * n_miners

    for ri, lvl in enumerate(LEVELS):
        is_last = (ri == n_levels - 1)
        lvl_cell = f'{{{{Icontech|{TECH_NAME}|{lvl}}}}}' + ('+' if is_last else '')
        cost_cell = cumulative_cost(lvl)

        print('|- style="vertical-align:top;"')
        print(f'! style="vertical-align:middle;" | {lvl_cell}')
        print(f'| {cost_cell}')

        for mi in range(n_miners):
            if floored[mi]:
                continue  # covered by rowspan from first floor row

            val = col_values[mi][ri]
            if ri == floor_row[mi]:
                floored[mi] = True
                rows_remaining = n_levels - ri
                cell = f"'''{val}'''"
                if rows_remaining > 1:
                    print(f'| rowspan="{rows_remaining}" | {cell}')
                else:
                    print(f'| {cell}')
            else:
                print(f'| {val}')

    print('|}')
    print()
```

- [ ] **Step 2: Add print_wiki function and update CLI**

Add after `print_wiki_table`:

```python
def print_wiki() -> None:
    """Emit the full MediaWiki article section for all belt types."""
    print('== Thresholds ==')
    print(
        'The table below shows the number of mining drills needed to fully saturate'
        ' both lanes of each belt type at key [[Mining productivity (research)]]{{SA}} levels.'
        ' Miners deposit ore on one side of the belt only; values shown are total drills'
        ' for both sides. The quad stacking column requires the belt stacking research'
        ' from [[Gleba]] and shows drills needed to fill a belt whose lane capacity'
        ' is 4\u00d7 higher; the miner\'s output speed is unchanged.'
    )
    print()
    for belt_name, lane_speed, sa in BELTS:
        print_wiki_table(belt_name, lane_speed, sa)
```

Then update `if __name__ == '__main__':`:

```python
if __name__ == '__main__':
    args = sys.argv[1:]
    wiki = '--wiki' in args
    if wiki:
        print_wiki()
    else:
        print_text()
```

- [ ] **Step 3: Run wiki output and visually verify**

Run:
```bash
python3 factorio_mining.py --wiki | head -60
```

Expected: intro paragraph, then `=== {{Icon|Transport belt}} Transport belt ===`, followed by the wikitable with 2-row header and data rows. Check that:
- Level 0 EMD Yellow shows `30`
- Level 110 BMD Green (turbo) shows `'''2'''` (bold, rowspan applied)
- Last row level shows `{{Icontech|Mining productivity (research)|110}}+`

- [ ] **Step 4: Commit**

```bash
git add factorio_mining.py
git commit -m "feat: add wiki output to factorio_mining.py"
```

---

### Task 4: Generate WikiArticles/MiningProductivityResearch.txt

**Files:**
- Create (generated): `WikiArticles/MiningProductivityResearch.txt`

- [ ] **Step 1: Generate the file**

```bash
python3 factorio_mining.py --wiki > WikiArticles/MiningProductivityResearch.txt
```

- [ ] **Step 2: Verify the file**

```bash
head -30 WikiArticles/MiningProductivityResearch.txt
wc -l WikiArticles/MiningProductivityResearch.txt
```

Expected: starts with `== Thresholds ==`, around 200-250 lines total (4 tables × ~55 lines each + intro).

- [ ] **Step 3: Commit**

```bash
git add WikiArticles/MiningProductivityResearch.txt
git commit -m "feat: generate Mining Productivity Research wiki article"
```

---

### Task 5: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add factorio_mining.py to Repository Overview**

In `CLAUDE.md`, find the Repository Overview section. After the `factorio_productivity.py` entry, add:

```
- **`factorio_mining.py`** - Source of truth for mining productivity threshold calculations. Shows how many mining drills are needed to fully saturate each belt type (Transport, Fast transport, Express transport, Turbo transport) at each research level. Supports Electric mining drill and Big mining drill, with and without quad belt stacking (Gleba research). Run with `python3 factorio_mining.py [--wiki]`.
- **`WikiArticles/MiningProductivityResearch.txt`** - MediaWiki markup source for the "Mining productivity (research)" wiki page thresholds section.
```

- [ ] **Step 2: Add verification commands**

In `CLAUDE.md`, find the Verification section. Add after the existing verification commands:

```
python3 factorio_mining.py
# Level 0, Yellow belt, EMD: 30 drills
# Level 110, Turbo belt, BMD: 2 drills
# Level 110, Yellow belt, BMD+stacking: 2 drills

python3 factorio_mining.py --wiki > WikiArticles/MiningProductivityResearch.txt
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add factorio_mining.py to CLAUDE.md"
```

---

### Task 6: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Check current README structure**

```bash
cat README.md
```

- [ ] **Step 2: Add mining productivity entry**

In `README.md`, after the closing ` ``` ` of the `factorio_productivity.py` block (after line 49), add:

```markdown

### `factorio_mining.py` - Mining productivity threshold tables

Shows how many mining drills are needed to fully saturate each belt type at each research level.

```bash
# Text output
python3 factorio_mining.py

# Regenerate wiki article
python3 factorio_mining.py --wiki > WikiArticles/MiningProductivityResearch.txt
```
```

Then in the Wiki Articles table (after the `RocketPartProductivityResearch.txt` row), add:

```markdown
| `WikiArticles/MiningProductivityResearch.txt` | Mining productivity (research) - Thresholds section |
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add Mining Productivity to README"
```

---

### Task 7: Final verification

- [ ] **Step 1: Run full regression check**

```bash
python3 factorio_mining.py
python3 factorio_productivity.py
```

Both should produce clean output with no errors.

- [ ] **Step 2: Regenerate wiki file and verify it matches committed version**

```bash
python3 factorio_mining.py --wiki > /tmp/mining_check.txt
diff WikiArticles/MiningProductivityResearch.txt /tmp/mining_check.txt
```

Expected: no diff (committed file matches fresh generation).

- [ ] **Step 3: Push branch and open PR**

```bash
git push -u origin feat/mining-productivity
gh pr create --title "feat: Mining Productivity Research wiki article" --body "$(cat <<'EOF'
## Summary
- Adds `factorio_mining.py` to calculate miners-per-full-belt thresholds for Mining Productivity (research)
- 4 wiki tables (Transport / Fast transport / Express transport / Turbo transport belt)
- 3 columns per table: Electric mining drill, Big mining drill, Big mining drill + quad stacking
- Research levels 0-110 in steps of 10
- Generates `WikiArticles/MiningProductivityResearch.txt`
- Updates CLAUDE.md and README.md per maintenance rules

## Test plan
- [ ] `python3 factorio_mining.py` produces clean text output
- [ ] Level 0 Yellow belt EMD = 30 drills
- [ ] Level 110 Turbo belt BMD = 2 drills (bold, rowspan to end of table)
- [ ] `python3 factorio_mining.py --wiki > WikiArticles/MiningProductivityResearch.txt` matches committed file
- [ ] `python3 factorio_productivity.py` still works (no regressions)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
