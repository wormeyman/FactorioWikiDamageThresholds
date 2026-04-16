# Steel Plate Productivity Thresholds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `factorio_productivity.py` that computes productivity breakpoint tables for Factorio Space Age productivity researches, starting with Steel Plate Productivity, and generate `WikiArticles/SteelPlateProductivityResearch.txt` for the wiki.

**Architecture:** New standalone file `factorio_productivity.py` mirrors the structure of `factorio_thresholds.py` - top-level data dicts (`MACHINES`, `MODULES`, `RESEARCHES`), core math helpers, and dual-mode output (`print_text` / `print_wiki_table`). Rows appear only at levels where a configuration first reaches the 300% productivity cap (plus level 0 as baseline). Capped cells use rowspan merging through the end of the table, identical to the damage table pattern.

**Tech Stack:** Python 3 stdlib only (`math`, `sys`). MediaWiki template syntax for wiki output.

---

## File Structure

- **Create:** `factorio_productivity.py` - all data, math, and output logic for productivity researches
- **Create:** `WikiArticles/SteelPlateProductivityResearch.txt` - generated wiki markup (paste into wiki)
- **Modify:** `CLAUDE.md` - update stale file paths and add new file entries

---

### Task 1: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Replace the Repository Overview section**

Replace the entire Repository Overview section (lines 7-13) with the following updated content that fixes stale paths and adds new file entries:

```
## Repository Overview

This is a content repository for contributions to the [Factorio Wiki](https://wiki.factorio.com/). It contains:

- **`WikiArticles/StrongerExplosivesResearch.txt`** - MediaWiki markup source for the "Stronger explosives (research)" wiki page
- **`WikiArticles/ArtilleryShellDamageResearch.txt`** - MediaWiki markup source for the "Artillery shell damage (research)" wiki page
- **`FactorioAsteroidDamageCalculator.xlsx`** - Excel export of a Google Sheet used to calculate asteroid damage thresholds. The Google Sheet is the source of truth; the .xlsx export is unreliable. The `Calculator` tab has a `Research Level Required` summary table (columns G-O, rows 15-38).
- **`factorio_thresholds.py`** - Source of truth for damage threshold calculations. Covers Stronger Explosives (asteroids, biters, spawners), Physical Projectile (gun turret vs Small/Medium asteroids), Laser Weapons (laser turret vs Small/Medium asteroids), and Artillery Shell Damage (enemies). Run with `python3 factorio_thresholds.py [tree] [--wiki]`.
- **`factorio_productivity.py`** - Source of truth for productivity threshold calculations. Covers Steel Plate Productivity (foundry and electric furnace, various module configs). Run with `python3 factorio_productivity.py [research] [--wiki]`.
- **`WikiArticles/SteelPlateProductivityResearch.txt`** - MediaWiki markup source for the "Steel plate productivity (research)" wiki page thresholds section.
- **`WikiArticles/enemies_wiki.json`** - Factorio wiki API response for the Enemies page. Extract wikitext via `data['parse']['wikitext']['*']`. Contains HP and resistance data for biters, spawners, and worms.
- **`WikiArticles/Technologies.json`** - Factorio wiki API response for the Technologies page. Contains infinite research data, pricing formulas, and interesting breakpoints.
```

- [ ] **Step 2: Verify the file looks correct**

```bash
head -20 CLAUDE.md
```

Expected: Repository Overview section shows `WikiArticles/` prefix on all JSON and TXT files, and lists both `factorio_thresholds.py` and `factorio_productivity.py`.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with correct WikiArticles/ paths and new file entries"
```

---

### Task 2: Create `factorio_productivity.py` - data, helpers, and core math

**Files:**
- Create: `factorio_productivity.py`

- [ ] **Step 1: Write the verification test first**

```bash
python3 -c "
from factorio_productivity import (
    total_prod, min_level_to_cap, _si, _sp_cumulative_costs, MACHINES, MODULES
)
print('imports OK')
"
```

Expected: `ModuleNotFoundError: No module named 'factorio_productivity'`
This confirms we're starting from scratch.

- [ ] **Step 2: Create `factorio_productivity.py` with data dicts, helpers, and core math**

Create `/Users/ericjohnson/Documents/GitHub/FactorioWikiDamageThresholds/factorio_productivity.py` with this complete content:

```python
#!/usr/bin/env python3
"""
Factorio productivity threshold calculator.

For each research level at which a new configuration first reaches the
300% productivity cap, shows the current productivity bonus for every
machine x module configuration. Outputs plain text or MediaWiki markup.

Usage:
    python3 factorio_productivity.py [research] [--wiki]

    research: steel_plate  (default: all)
    --wiki: MediaWiki markup  (default: text)
"""
import math
import sys

# ---------------------------------------------------------------------------
# Machines: base productivity bonus and module slot count
# ---------------------------------------------------------------------------

MACHINES = {
    'Foundry':          {'base_prod': 0.50, 'module_slots': 4},
    'Electric furnace': {'base_prod': 0.00, 'module_slots': 2},
}

# ---------------------------------------------------------------------------
# Modules: productivity bonus per module slot.
# 'No modules' has 0.00 per-module bonus; 0.00 x any slot count = 0.
# ---------------------------------------------------------------------------

MODULES = {
    'No modules':              0.00,
    'Prod module 3':           0.10,
    'Legendary Prod module 2': 0.15,
    'Legendary Prod module 3': 0.25,
}

# ---------------------------------------------------------------------------
# SI suffix formatter (independent copy; files intentionally kept separate)
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def total_prod(base: float, slots: int, module_bonus: float,
               level: int, bonus_per_level: float) -> float:
    """Total productivity bonus at a given research level (fraction; 1.0 = 100%)."""
    return base + slots * module_bonus + level * bonus_per_level


def min_level_to_cap(base: float, slots: int, module_bonus: float,
                     bonus_per_level: float, cap: float) -> int:
    """Minimum research level to reach the productivity cap.

    Uses epsilon subtraction before ceil to avoid floating-point boundary
    errors (e.g. 2.1 / 0.1 = 20.999...998 in binary floating point).
    True non-integer ratios are always at least ~2e-4 away from an integer
    boundary for the values used here, so 1e-9 is safe.
    """
    needed = cap - base - slots * module_bonus
    if needed <= 0:
        return 0
    return math.ceil(needed / bonus_per_level - 1e-9)

# ---------------------------------------------------------------------------
# Cumulative research cost functions
# ---------------------------------------------------------------------------

def _sp_cumulative_costs(max_lvl: int = 30) -> dict:
    """Cumulative science pack cost to reach each Steel Plate Productivity level.

    Cost per level N: round(1000 x 1.5^N) packs
    (Automation + Logistic + Chemical + Production science packs).
    Returns: {level: SI-formatted string} with '-' for level 0.
    """
    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += round(1000 * 1.5 ** lvl)
        result[lvl] = _si(total)
    return result

# ---------------------------------------------------------------------------
# Research definitions
# ---------------------------------------------------------------------------

RESEARCHES = {
    'steel_plate': {
        'name': 'Steel Plate Productivity',
        'tech_name': 'Steel plate productivity (research)',
        'bonus_per_level': 0.10,
        'cumulative_costs': _sp_cumulative_costs(),
        'max_level': 30,
        'cap': 3.00,
        'machines': ['Foundry', 'Electric furnace'],
        'module_configs': [
            'No modules',
            'Prod module 3',
            'Legendary Prod module 2',
            'Legendary Prod module 3',
        ],
    },
}
```

**Do not add `if __name__ == '__main__'` yet** - that comes in Task 4.

- [ ] **Step 3: Verify core math against all known breakpoints**

```bash
python3 -c "
from factorio_productivity import total_prod, min_level_to_cap, _si, _sp_cumulative_costs

# total_prod: spot-check known cap levels (value should be exactly 300% when rounded)
assert int(round(total_prod(0.5, 4, 0.25, 15, 0.1) * 100)) == 300, 'Foundry+LP3 cap at 15'
assert int(round(total_prod(0.5, 4, 0.15, 19, 0.1) * 100)) == 300, 'Foundry+LP2 cap at 19'
assert int(round(total_prod(0.5, 4, 0.10, 21, 0.1) * 100)) == 300, 'Foundry+NP3 cap at 21'
assert int(round(total_prod(0.5, 4, 0.00, 25, 0.1) * 100)) == 300, 'Foundry+none cap at 25'
assert int(round(total_prod(0.0, 2, 0.25, 25, 0.1) * 100)) == 300, 'EFurn+LP3 cap at 25'
assert int(round(total_prod(0.0, 2, 0.15, 27, 0.1) * 100)) == 300, 'EFurn+LP2 cap at 27'
assert int(round(total_prod(0.0, 2, 0.10, 28, 0.1) * 100)) == 300, 'EFurn+NP3 cap at 28'
assert int(round(total_prod(0.0, 2, 0.00, 30, 0.1) * 100)) == 300, 'EFurn+none cap at 30'

# total_prod: check level 0 baseline values from design spec table
assert int(round(total_prod(0.5, 4, 0.00,  0, 0.1) * 100)) ==  50, 'Foundry+none at 0'
assert int(round(total_prod(0.5, 4, 0.10,  0, 0.1) * 100)) ==  90, 'Foundry+NP3 at 0'
assert int(round(total_prod(0.5, 4, 0.15,  0, 0.1) * 100)) == 110, 'Foundry+LP2 at 0'
assert int(round(total_prod(0.5, 4, 0.25,  0, 0.1) * 100)) == 150, 'Foundry+LP3 at 0'
assert int(round(total_prod(0.0, 2, 0.00,  0, 0.1) * 100)) ==   0, 'EFurn+none at 0'
assert int(round(total_prod(0.0, 2, 0.10,  0, 0.1) * 100)) ==  20, 'EFurn+NP3 at 0'
assert int(round(total_prod(0.0, 2, 0.15,  0, 0.1) * 100)) ==  30, 'EFurn+LP2 at 0'
assert int(round(total_prod(0.0, 2, 0.25,  0, 0.1) * 100)) ==  50, 'EFurn+LP3 at 0'

# min_level_to_cap: all 8 configurations
assert min_level_to_cap(0.5, 4, 0.25, 0.1, 3.0) == 15, f'got {min_level_to_cap(0.5, 4, 0.25, 0.1, 3.0)}'
assert min_level_to_cap(0.5, 4, 0.15, 0.1, 3.0) == 19, f'got {min_level_to_cap(0.5, 4, 0.15, 0.1, 3.0)}'
assert min_level_to_cap(0.5, 4, 0.10, 0.1, 3.0) == 21, f'got {min_level_to_cap(0.5, 4, 0.10, 0.1, 3.0)}'
assert min_level_to_cap(0.5, 4, 0.00, 0.1, 3.0) == 25, f'got {min_level_to_cap(0.5, 4, 0.00, 0.1, 3.0)}'
assert min_level_to_cap(0.0, 2, 0.25, 0.1, 3.0) == 25, f'got {min_level_to_cap(0.0, 2, 0.25, 0.1, 3.0)}'
assert min_level_to_cap(0.0, 2, 0.15, 0.1, 3.0) == 27, f'got {min_level_to_cap(0.0, 2, 0.15, 0.1, 3.0)}'
assert min_level_to_cap(0.0, 2, 0.10, 0.1, 3.0) == 28, f'got {min_level_to_cap(0.0, 2, 0.10, 0.1, 3.0)}'
assert min_level_to_cap(0.0, 2, 0.00, 0.1, 3.0) == 30, f'got {min_level_to_cap(0.0, 2, 0.00, 0.1, 3.0)}'

# _si: spot-check a few values
assert _si(1500)   == '1.5k',   f'got {_si(1500)}'
assert _si(3750)   == '3.75k',  f'got {_si(3750)}'
assert _si(999)    == '999',    f'got {_si(999)}'
assert _si(1000)   == '1k',     f'got {_si(1000)}'
assert _si(1000000) == '1M',    f'got {_si(1000000)}'

# _sp_cumulative_costs: level 0 is '-', level 1 is '1.5k', level 2 is '3.75k'
costs = _sp_cumulative_costs()
assert costs[0] == '-',      f'got {costs[0]}'
assert costs[1] == '1.5k',   f'got {costs[1]}'
assert costs[2] == '3.75k',  f'got {costs[2]}'

print('PASS')
"
```

Expected: `PASS`

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add factorio_productivity.py with data dicts and core math"
```

---

### Task 3: Add `build_columns`, `find_breakpoints`, and `print_text`

**Files:**
- Modify: `factorio_productivity.py` - append after `RESEARCHES` dict

- [ ] **Step 1: Append column building, breakpoints, and text output to `factorio_productivity.py`**

Add this block at the end of the file (after the `RESEARCHES` dict, before any `if __name__` block):

```python
# ---------------------------------------------------------------------------
# Column building and breakpoint detection
# ---------------------------------------------------------------------------

def build_columns(research: dict) -> list:
    """Return flat list of column dicts for the given research.

    One column per (machine x module_config) combination, ordered:
    Foundry configs first, then Electric furnace configs.
    Within each machine: in the order listed in research['module_configs'].
    """
    cols = []
    for machine_name in research['machines']:
        machine = MACHINES[machine_name]
        for config_name in research['module_configs']:
            cols.append({
                'machine':      machine_name,
                'config':       config_name,
                'label':        f'{machine_name} / {config_name}',
                'base_prod':    machine['base_prod'],
                'slots':        machine['module_slots'],
                'module_bonus': MODULES[config_name],
            })
    return cols


def find_breakpoints(research: dict) -> list:
    """Levels at which at least one column first reaches the productivity cap.

    Always includes level 0 as the baseline row.
    Capped at research['max_level'] so no row exceeds the table end.
    Returns a sorted list of unique levels.
    """
    cols = build_columns(research)
    cap = research['cap']
    bpl = research['bonus_per_level']
    max_level = research['max_level']
    cap_levels = set()
    for col in cols:
        lvl = min_level_to_cap(
            col['base_prod'], col['slots'], col['module_bonus'], bpl, cap)
        cap_levels.add(min(lvl, max_level))
    return sorted({0} | cap_levels)

# ---------------------------------------------------------------------------
# Text output
# ---------------------------------------------------------------------------

def print_text(research: dict) -> None:
    """Print a plain text summary of productivity % at each breakpoint level."""
    cols = build_columns(research)
    bpl = research['bonus_per_level']
    breakpoints = find_breakpoints(research)
    max_level = research['max_level']
    cap = research['cap']

    print(f'\n=== {research["name"]} (max level {max_level}) ===')

    w = 8
    labels = [c['label'] for c in cols]
    hdr = f"{'Level':>8}  " + '  '.join(f'{lb[:w]:>{w}}' for lb in labels)
    print(hdr)
    print('-' * len(hdr))

    n_bps = len(breakpoints)
    for i, lvl in enumerate(breakpoints):
        next_lvl = breakpoints[i + 1] if i + 1 < n_bps else max_level + 1
        end = next_lvl - 1
        lvl_str = str(lvl) if end == lvl else f'{lvl}-{end}'
        vals = []
        for c in cols:
            p = int(round(min(
                total_prod(c['base_prod'], c['slots'], c['module_bonus'], lvl, bpl),
                cap) * 100))
            vals.append(f'{p}%')
        row = f'{lvl_str:>8}  ' + '  '.join(f'{v:>{w}}' for v in vals)
        print(row)
```

- [ ] **Step 2: Verify breakpoints and text output**

```bash
python3 -c "
from factorio_productivity import find_breakpoints, RESEARCHES

bps = find_breakpoints(RESEARCHES['steel_plate'])
assert bps == [0, 15, 19, 21, 25, 27, 28, 30], f'got {bps}'
print('breakpoints PASS:', bps)
"
```

Expected: `breakpoints PASS: [0, 15, 19, 21, 25, 27, 28, 30]`

- [ ] **Step 3: Check text output matches design spec table**

```bash
python3 factorio_productivity.py steel_plate
```

Expected output (column widths may vary slightly):

```
=== Steel Plate Productivity (max level 30) ===
   Level  Foundry  Foundry  Foundry  Foundry  Electri  Electri  Electri  Electri
            /  No   / Prod    / Leg    / Leg     /  No   / Prod    / Leg    / Leg
--------  ------  ------  ------  ------  ------  ------  ------  ------
       0     50%     90%    110%    150%      0%     20%     30%     50%
    1-14  ...varies...
      15    200%    240%    260%    300%    150%    170%    180%    200%
   16-18  ...varies...
      19    240%    280%    300%    300%    190%    210%    220%    240%
   20-20  ...varies...
      21    260%    300%    300%    300%    210%    230%    240%    260%
   22-24  ...varies...
      25    300%    300%    300%    300%    250%    270%    280%    300%
   26-26  ...varies...
      27    300%    300%    300%    300%    270%    290%    300%    300%
      28    300%    300%    300%    300%    280%    300%    300%    300%
   29-29  ...varies...
      30    300%    300%    300%    300%    300%    300%    300%    300%
```

Key values to confirm (match the design spec table exactly):
- Level 0 row: `50%  90%  110%  150%  0%  20%  30%  50%`
- Level 15 row: `200%  240%  260%  300%  150%  170%  180%  200%`
- Level 19 row: `240%  280%  300%  300%  190%  210%  220%  240%`
- Level 21 row: `260%  300%  300%  300%  210%  230%  240%  260%`
- Level 25 row: `300%  300%  300%  300%  250%  270%  280%  300%`
- Level 27 row: `300%  300%  300%  300%  270%  290%  300%  300%`
- Level 28 row: `300%  300%  300%  300%  280%  300%  300%  300%`
- Level 30 row: `300%  300%  300%  300%  300%  300%  300%  300%`

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add build_columns, find_breakpoints, and print_text to factorio_productivity.py"
```

---

### Task 4: Add `print_wiki_table` and CLI entry point

**Files:**
- Modify: `factorio_productivity.py` - append wiki output function and `__main__` block

- [ ] **Step 1: Append wiki output and CLI to `factorio_productivity.py`**

Add this block at the end of the file (after `print_text`):

```python
# ---------------------------------------------------------------------------
# Wiki output
# ---------------------------------------------------------------------------

# Icon markup for machine group headers (row 1 of 2-row header)
_MACHINE_ICONS = {
    'Foundry':          '{{Icon|Foundry}}',
    'Electric furnace': '{{Icon|Electric furnace}}',
}

# Icon markup for module config sub-headers (row 2 of 2-row header).
# Legendary quality icon syntax verified against https://wiki.factorio.com/Template:Icon
_MODULE_ICONS = {
    'No modules':              '-',
    'Prod module 3':           '{{Icon|Productivity module 3}}',
    'Legendary Prod module 2': '{{Icon|Productivity module 2|legendary}}',
    'Legendary Prod module 3': '{{Icon|Productivity module 3|legendary}}',
}


def print_wiki_table(research: dict) -> None:
    """Emit a MediaWiki table showing productivity % at each breakpoint level.

    Structure:
    - 2-row header: machine group icons (row 1) + module config icons (row 2)
    - Data rows: one per breakpoint level (levels where any config first hits cap)
    - Level 0 always included as baseline; last row gets '+' suffix
    - Non-capped cells: plain text percentage (e.g. '150%'), rowspan=1
    - Capped cells (300%): bold text, rowspan covers all remaining rows
    """
    cols = build_columns(research)
    bpl = research['bonus_per_level']
    breakpoints = find_breakpoints(research)
    max_level = research['max_level']
    cap = research['cap']
    cap_int = int(round(cap * 100))
    n_cols = len(cols)
    n_bps = len(breakpoints)
    tech_name = research['tech_name']
    cumulative_costs = research['cumulative_costs']
    n_configs = len(research['module_configs'])

    def display_pct(ci: int, lvl: int) -> int:
        c = cols[ci]
        p = total_prod(c['base_prod'], c['slots'], c['module_bonus'], lvl, bpl)
        return int(round(min(p, cap) * 100))

    print(f'<!-- {research["name"]} productivity thresholds -->')
    print('{| class="wikitable" style="text-align:center;"')

    # --- 2-row header ---
    # Row 1: Level (rowspan=2) | Cost (rowspan=2) | machine group headers
    machine_header_cells = []
    for m_name in research['machines']:
        machine_header_cells.append(
            f'colspan="{n_configs}" | {_MACHINE_ICONS[m_name]} {m_name}')
    print(f'! rowspan="2" | Level'
          f' !! rowspan="2" | Cumulative<br>research cost'
          f' !! ' + ' !! '.join(machine_header_cells))
    print('|-')

    # Row 2: module config icons repeated for each machine
    config_cells = []
    for _ in research['machines']:
        for cfg in research['module_configs']:
            config_cells.append(_MODULE_ICONS[cfg])
    print('! ' + ' !! '.join(config_cells))
    print('|-')

    # --- Data rows ---
    # capped[ci] tracks whether column ci has already reached 300%.
    # When a column first caps, emit it with rowspan = remaining rows.
    # On subsequent rows, skip capped columns (covered by the earlier rowspan).
    capped = [False] * n_cols

    for bi, lvl in enumerate(breakpoints):
        is_last_row = (bi == n_bps - 1)
        n_rows_remaining = n_bps - bi  # rows from this one to end, inclusive

        # Level cell: last row gets '+' suffix
        if is_last_row:
            lvl_str = f'{{{{Icontech|{tech_name}|{lvl}}}}}+'
        else:
            lvl_str = f'{{{{Icontech|{tech_name}|{lvl}}}}}'
        cost_val = cumulative_costs.get(lvl, '?')

        print('|- style="vertical-align:top;"')
        print(f'! style="vertical-align:middle;" | {lvl_str}')
        print(f'| {cost_val}')

        for ci in range(n_cols):
            if capped[ci]:
                continue  # cell is covered by rowspan from the row it first capped

            val = display_pct(ci, lvl)

            if val >= cap_int:
                # First time this column hits cap: bold, rowspan through end of table
                capped[ci] = True
                cell = f"'''{val}%'''"
                if n_rows_remaining > 1:
                    print(f'| rowspan="{n_rows_remaining}" | {cell}')
                else:
                    print(f'| {cell}')
            else:
                # Not yet capped: plain text, no merging (value differs at each row)
                print(f'| {val}%')

    print('|}')


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    args = sys.argv[1:]
    wiki = '--wiki' in args
    research_args = [a for a in args if not a.startswith('--')]

    if research_args:
        unknown = [a for a in research_args if a not in RESEARCHES]
        if unknown:
            print(f'Unknown research(es): {unknown}', file=sys.stderr)
            print(f'Available: {list(RESEARCHES)}', file=sys.stderr)
            sys.exit(1)
        selected = [RESEARCHES[a] for a in research_args]
    else:
        selected = list(RESEARCHES.values())

    for research in selected:
        if wiki:
            print_wiki_table(research)
        else:
            print_text(research)
```

- [ ] **Step 2: Smoke-test wiki output**

```bash
python3 factorio_productivity.py steel_plate --wiki 2>&1 | head -20
```

Expected: Output begins with `<!-- Steel Plate Productivity productivity thresholds -->`, then `{| class="wikitable"`, then two header rows, then `|-` data rows. No Python errors.

- [ ] **Step 3: Verify rowspan correctness on key cells**

```bash
python3 factorio_productivity.py steel_plate --wiki 2>&1 | grep -n "rowspan\|300%\|Icontech"
```

Verify by inspection:
- Level 15 row: Foundry/LP3 column emits `rowspan="7" | '''300%'''` (covers rows bi=1 through bi=7, i.e. 7 remaining rows)
- Level 19 row: Foundry/LP2 column emits `rowspan="6" | '''300%'''`
- Level 21 row: Foundry/NP3 column emits `rowspan="5" | '''300%'''`
- Level 25 row: Foundry/no-mod and EFurn/LP3 each emit `rowspan="4" | '''300%'''`
- Level 27 row: EFurn/LP2 emits `rowspan="3" | '''300%'''`
- Level 28 row: EFurn/NP3 emits `rowspan="2" | '''300%'''`
- Level 30 row: EFurn/no-mod emits `'''300%'''` (no rowspan needed, last row)
- Level 30 row ends with `|}` on the final line

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add print_wiki_table and CLI entry point to factorio_productivity.py"
```

---

### Task 5: Generate output file and verify

**Files:**
- Create: `WikiArticles/SteelPlateProductivityResearch.txt`

- [ ] **Step 1: Generate the wiki markup**

```bash
python3 factorio_productivity.py steel_plate --wiki > WikiArticles/SteelPlateProductivityResearch.txt
```

- [ ] **Step 2: Prepend the thresholds section header and intro paragraph**

Open `WikiArticles/SteelPlateProductivityResearch.txt` and prepend the following two lines before the `<!-- Steel Plate Productivity` comment:

```
== Thresholds ==
The table below shows the total productivity bonus at key research levels for [[Steel plate productivity (research)]]{{SA}}, for each machine and module configuration. Productivity is capped at 300%; cells shown in '''bold''' indicate that the configuration has reached the cap at that level and will not improve further with additional research.

```

The file should now start with `== Thresholds ==` and end with `|}`.

- [ ] **Step 3: Verify the file structure**

```bash
head -5 WikiArticles/SteelPlateProductivityResearch.txt
tail -3 WikiArticles/SteelPlateProductivityResearch.txt
```

Expected head:
```
== Thresholds ==
The table below shows the total productivity bonus at key research levels...

<!-- Steel Plate Productivity productivity thresholds -->
{| class="wikitable" style="text-align:center;"
```

Expected tail:
```
| '''300%'''
|}
```

- [ ] **Step 4: Cross-check known wiki breakpoints**

The Technologies wiki page states two breakpoints for Steel Plate Productivity:
- "Level 15: Foundries filled with legendary productivity modules reach the 300% productivity cap."
- "Level 25: Foundries reach the 300% productivity cap with no modules."

```bash
python3 -c "
from factorio_productivity import min_level_to_cap
# Foundry + legendary prod 3 (25% x 4 slots)
assert min_level_to_cap(0.5, 4, 0.25, 0.1, 3.0) == 15, 'should be 15'
# Foundry + no modules
assert min_level_to_cap(0.5, 4, 0.00, 0.1, 3.0) == 25, 'should be 25'
print('Wiki breakpoint cross-check PASS')
"
```

Expected: `Wiki breakpoint cross-check PASS`

- [ ] **Step 5: Commit**

```bash
git add WikiArticles/SteelPlateProductivityResearch.txt
git commit -m "feat: generate SteelPlateProductivityResearch.txt wiki thresholds table"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| New `factorio_productivity.py` with MACHINES, MODULES, RESEARCHES dicts | Task 2 |
| `total_prod`, `min_level_to_cap` functions | Task 2 |
| `_si` helper (independent copy) | Task 2 |
| `_sp_cumulative_costs` (1000 × 1.5^N) | Task 2 |
| `build_columns`, `find_breakpoints` | Task 3 |
| `print_text` output | Task 3 |
| `print_wiki_table` with 2-row header, rowspan merging | Task 4 |
| Machine icons in header (`{{Icon|Foundry}}` etc.) | Task 4 |
| Module config icons in header | Task 4 |
| Level cells: `{{Icontech|...}}` with `+` on last row | Task 4 |
| Capped cells bold with rowspan | Task 4 |
| CLI: `python3 factorio_productivity.py steel_plate [--wiki]` | Task 4 |
| `WikiArticles/SteelPlateProductivityResearch.txt` with intro + table | Task 5 |
| Cross-check against known wiki breakpoints (15 and 25) | Task 5 |
| CLAUDE.md path updates | Task 1 |

**Placeholder scan:** No TBDs. All code blocks are complete and runnable. All expected outputs are specified.

**Type consistency:**
- `build_columns` returns list of dicts with keys: `machine`, `config`, `label`, `base_prod`, `slots`, `module_bonus` - all consumed consistently in `print_text` and `print_wiki_table`.
- `find_breakpoints` returns `list[int]` - iterated as `(bi, lvl)` in both text and wiki output.
- `_sp_cumulative_costs` returns `{int: str}` - accessed via `.get(lvl, '?')` in `print_wiki_table`.
- `RESEARCHES['steel_plate']` keys (`cumulative_costs`, `cap`, `machines`, `module_configs`, `tech_name`, `bonus_per_level`, `max_level`) all referenced consistently across Tasks 2, 3, and 4.
- `display_pct(ci, lvl)` is a closure inside `print_wiki_table` - defined and used in Task 4 only, no cross-task naming conflicts.
