# Processing Unit Productivity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Processing unit productivity research to `factorio_productivity.py` and generate the wiki article `WikiArticles/ProcessingUnitProductivityResearch.txt`.

**Architecture:** Refactor the one-off `_sp_cumulative_costs` function into a generic `_cumulative_costs(cost_base, max_lvl, multiplier)` helper, update `steel_plate` to call it, then add Assembling machine 3 + Electromagnetic plant as machines and wire up the `processing_unit` research entry. No new files are created in the source; one new wiki output file is generated.

**Tech Stack:** Python 3, MediaWiki markup, `factorio_productivity.py` (single-file script)

---

### Task 1: Replace `_sp_cumulative_costs` with generic `_cumulative_costs`

**Files:**
- Modify: `factorio_productivity.py:84-96` (replace function)
- Modify: `factorio_productivity.py:107` (update steel_plate reference)

- [ ] **Step 1: Replace the function**

In `factorio_productivity.py`, replace lines 84-96 (the entire `_sp_cumulative_costs` function) with:

```python
def _cumulative_costs(cost_base: int, max_lvl: int, multiplier: float = 1.5) -> dict:
    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += round(cost_base * multiplier ** lvl)
        result[lvl] = _si(total)
    return result
```

- [ ] **Step 2: Update the steel_plate reference**

In `factorio_productivity.py`, find the `steel_plate` entry in `RESEARCHES` (around line 107). Change:

```python
'cumulative_costs': _sp_cumulative_costs(),
```

to:

```python
'cumulative_costs': _cumulative_costs(1000, 30),
```

- [ ] **Step 3: Verify steel_plate output is unchanged**

Run:
```bash
python3 factorio_productivity.py steel_plate
```

Expected output (spot-check key rows):
```
=== Steel Plate Productivity (max level 30) ===
   Level  Foundry  ...
       0    50%  ...
      10   150%  ...
      15   200%  ...
      30   300%  ...
```

The full breakpoint row set must still be `0, 10, 15, 19, 20, 21, 25, 27, 28, 30`.

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "refactor: replace _sp_cumulative_costs with generic _cumulative_costs"
```

---

### Task 2: Add Assembling machine 3 to MACHINES and `_MACHINE_ICONS`

**Files:**
- Modify: `factorio_productivity.py:22-25` (MACHINES dict)
- Modify: `factorio_productivity.py:213-216` (_MACHINE_ICONS dict)

- [ ] **Step 1: Add to MACHINES**

In `factorio_productivity.py`, find the `MACHINES` dict (around line 22). Add the new entry after `'Electric furnace'`:

```python
MACHINES = {
    'Foundry':              {'base_prod': 0.50, 'module_slots': 4},
    'Electric furnace':     {'base_prod': 0.00, 'module_slots': 2},
    'Assembling machine 3': {'base_prod': 0.00, 'module_slots': 4},
    'Electromagnetic plant':{'base_prod': 0.50, 'module_slots': 5},
}
```

- [ ] **Step 2: Add to `_MACHINE_ICONS`**

In `factorio_productivity.py`, find `_MACHINE_ICONS` (around line 213). Add the two new entries:

```python
_MACHINE_ICONS = {
    'Foundry':               '{{Icon|Foundry}}',
    'Electric furnace':      '{{Icon|Electric furnace}}',
    'Assembling machine 3':  '{{Icon|Assembling machine 3}}',
    'Electromagnetic plant': '{{Icon|Electromagnetic plant}}',
}
```

- [ ] **Step 3: Verify no regression**

Run:
```bash
python3 factorio_productivity.py steel_plate
```

Expected: identical output to Task 1 Step 3. No errors about missing machine icons.

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add Assembling machine 3 and Electromagnetic plant to MACHINES and icons"
```

---

### Task 3: Add `processing_unit` to RESEARCHES

**Files:**
- Modify: `factorio_productivity.py:102-127` (RESEARCHES dict)

- [ ] **Step 1: Add the research entry**

In `factorio_productivity.py`, find the closing `}` of the `RESEARCHES` dict (around line 127). Add the `processing_unit` key after the existing `steel_plate` entry, leaving `steel_plate` untouched:

```python
    'processing_unit': {
        'name': 'Processing Unit Productivity',
        'tech_name': 'Processing unit productivity (research)',
        'bonus_per_level': 0.10,
        'cumulative_costs': _cumulative_costs(1000, 30),
        'max_level': 30,
        'cap': 3.00,
        'intro': (
            "== Thresholds ==\n"
            "The table below shows the total productivity bonus at key research levels"
            " for [[Processing unit productivity (research)]]{{SA}}, for each machine and"
            " module configuration. Productivity is capped at 300%; cells shown in"
            " '''bold''' indicate that the configuration has reached the cap at that"
            " level and will not improve further with additional research.\n"
        ),
        'notable_levels': [10, 20],
        'machines': ['Assembling machine 3', 'Electromagnetic plant'],
        'module_configs': [
            'No modules',
            'Prod module 3',
            'Legendary Prod module 2',
            'Legendary Prod module 3',
        ],
    },
}
```

- [ ] **Step 2: Verify breakpoints and values**

Run:
```bash
python3 factorio_productivity.py processing_unit
```

Expected row set: `0, 10, 13, 18, 20, 24, 25, 26, 30`

Spot-check these values:

| Level | AM3+none | AM3+LP3 | EM+none | EM+LP3 |
|-------|----------|---------|---------|--------|
| 0     | 0%       | 100%    | 50%     | 175%   |
| 10    | 100%     | 200%    | 150%    | 275%   |
| 13    | 130%     | 230%    | 180%    | **300%** |
| 20    | 200%     | **300%**| 250%    | **300%** |
| 30    | **300%** | **300%**| **300%**| **300%** |

- [ ] **Step 3: Verify steel_plate is still unaffected**

Run:
```bash
python3 factorio_productivity.py steel_plate
```

Expected: same output as before (breakpoints `0, 10, 15, 19, 20, 21, 25, 27, 28, 30`).

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add processing_unit research to factorio_productivity.py"
```

---

### Task 4: Generate wiki output file

**Files:**
- Create: `WikiArticles/ProcessingUnitProductivityResearch.txt`

- [ ] **Step 1: Generate the file**

```bash
python3 factorio_productivity.py processing_unit --wiki > WikiArticles/ProcessingUnitProductivityResearch.txt
```

- [ ] **Step 2: Spot-check the output**

```bash
head -30 WikiArticles/ProcessingUnitProductivityResearch.txt
```

Expected: starts with `== Thresholds ==` intro paragraph, then `<!-- Processing Unit Productivity productivity thresholds -->`, then `{| class="wikitable"`, then a 2-row header with `{{Icon|Assembling machine 3}}` and `{{Icon|Electromagnetic plant}}` group headers.

Also verify the first bold cap cell appears at level 13 (EM plant + LP3 column):
```bash
grep "300%" WikiArticles/ProcessingUnitProductivityResearch.txt | head -5
```

Expected: first `'''300%'''` appears in the level-13 row.

- [ ] **Step 3: Verify `--wiki` on steel_plate still produces the same output**

```bash
python3 factorio_productivity.py steel_plate --wiki | head -5
```

Expected: `== Thresholds ==` intro for steel plate, no errors.

- [ ] **Step 4: Commit**

```bash
git add WikiArticles/ProcessingUnitProductivityResearch.txt factorio_productivity.py
git commit -m "feat: generate ProcessingUnitProductivityResearch wiki article"
```
