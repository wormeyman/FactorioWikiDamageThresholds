# Rocket Part Productivity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Rocket Part Productivity research to `factorio_productivity.py`, generate the wiki article, and update `README.md`.

**Architecture:** Single-machine research (Rocket silo, 0% base, 4 slots) following the exact same pattern as `rocket_fuel`. The only structural difference is cost base 2000 instead of 1000 and Cryogenic science pack instead of Agricultural. One new entry in `MACHINES`, one icon entry, one research dict entry.

**Tech Stack:** Python 3 (stdlib only), MediaWiki markup

---

### Task 1: Add Rocket silo to MACHINES and _MACHINE_ICONS

**Files:**
- Modify: `factorio_productivity.py`

- [ ] **Step 1: Add Rocket silo to the MACHINES dict**

In `factorio_productivity.py`, the `MACHINES` dict ends at line 30 with `'Cryogenic plant'`. Add the new entry after it:

```python
MACHINES = {
    'Foundry':               {'base_prod': 0.50, 'module_slots': 4},
    'Electric furnace':      {'base_prod': 0.00, 'module_slots': 2},
    'Assembling machine 3':  {'base_prod': 0.00, 'module_slots': 4},
    'Electromagnetic plant': {'base_prod': 0.50, 'module_slots': 5},
    'Chemical plant':        {'base_prod': 0.00, 'module_slots': 3},
    'Biochamber':            {'base_prod': 0.50, 'module_slots': 4},
    'Cryogenic plant':       {'base_prod': 0.00, 'module_slots': 8},
    'Rocket silo':           {'base_prod': 0.00, 'module_slots': 4},
}
```

- [ ] **Step 2: Add Rocket silo to _MACHINE_ICONS**

In `factorio_productivity.py`, the `_MACHINE_ICONS` dict (around line 316) ends with `'Cryogenic plant'`. Add:

```python
_MACHINE_ICONS = {
    'Foundry':               '{{Icon|Foundry|space-age=yes}}',
    'Electric furnace':      '{{Icon|Electric furnace}}',
    'Assembling machine 3':  '{{Icon|Assembling machine 3}}',
    'Electromagnetic plant': '{{Icon|Electromagnetic plant}}',
    'Chemical plant':        '{{Icon|Chemical plant}}',
    'Biochamber':            '{{Icon|Biochamber|space-age=yes}}',
    'Cryogenic plant':       '{{Icon|Cryogenic plant|space-age=yes}}',
    'Rocket silo':           '{{Icon|Rocket silo}}',
}
```

- [ ] **Step 3: Verify the script still runs cleanly**

```bash
python3 factorio_productivity.py
```

Expected: all existing researches print without error. No output changes to existing researches.

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add Rocket silo to MACHINES and machine icons"
```

---

### Task 2: Add rocket_part research definition

**Files:**
- Modify: `factorio_productivity.py`

- [ ] **Step 1: Add the rocket_part entry to RESEARCHES**

In `factorio_productivity.py`, after the `'rocket_fuel'` dict (which ends around line 229), add:

```python
    'rocket_part': {
        'name': 'Rocket Part Productivity',
        'tech_name': 'Rocket part productivity (research)',
        'bonus_per_level': 0.10,
        'cumulative_costs': _cumulative_costs(2000, 30),
        'max_level': 30,
        'cap': 3.00,
        'intro': (
            "== Thresholds ==\n"
            "The table below shows the total productivity bonus at key research levels"
            " for [[Rocket part productivity (research)]]{{SA}}, for each module"
            " configuration. Applies to the [[Rocket part]] recipe (Rocket silo)."
            " Productivity is capped at 300%; cells shown in"
            " '''bold''' indicate that the configuration has reached the cap at that"
            " level and will not improve further with additional research.\n"
        ),
        'notable_levels': [10, 20],
        'machines': ['Rocket silo'],
        'module_configs': [
            'No modules',
            'Prod module 3',
            'Legendary Prod module 2',
            'Legendary Prod module 3',
        ],
    },
```

- [ ] **Step 2: Run text output and verify breakpoints**

```bash
python3 factorio_productivity.py rocket_part
```

Expected output (verify these exact breakpoint rows appear):

```
=== Rocket Part Productivity (max level 30) ===
   Level  Rocket si  Rocket si  Rocket si  Rocket si
-------------------------------------------------------
       0       0%       40%       60%      100%
   10-19     100%      140%      160%      200%
   20-23     200%      240%      260%     300%
   24-25     240%      260%      280%     300%
   26-29     260%      280%      300%     300%
      30+    300%      300%      300%     300%
```

Key checks:
- Level 20 row exists (LP3 caps here)
- Level 24 row exists (LP2 caps here)
- Level 26 row exists (Prod 3 caps here)
- Level 30 row exists (No modules caps here)
- Breakpoints are exactly `[0, 10, 20, 24, 26, 30]`

- [ ] **Step 3: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add Rocket Part Productivity research definition"
```

---

### Task 3: Generate the wiki article

**Files:**
- Create: `WikiArticles/RocketPartProductivityResearch.txt`

- [ ] **Step 1: Generate the wiki markup**

```bash
python3 factorio_productivity.py rocket_part --wiki > WikiArticles/RocketPartProductivityResearch.txt
```

- [ ] **Step 2: Inspect the output**

```bash
cat WikiArticles/RocketPartProductivityResearch.txt
```

Verify:
- Starts with `== Thresholds ==` followed by the intro paragraph
- The intro paragraph uses `[[Rocket part productivity (research)]]{{SA}}` and `[[Rocket part]]` (plain wikilinks, no `{{Icon|...}}` in prose)
- Table header has `{{Icon|Rocket silo}} Rocket silo` spanning 4 columns
- Module sub-header shows `4× {{Icon|...}}` for module configs (except "No modules" which shows `-`)
- Bold `'''300%'''` cells appear with appropriate rowspan values
- Last level row has `+` suffix on the Icontech
- Cumulative costs use larger numbers than other researches (2000 base vs 1000)

- [ ] **Step 3: Commit**

```bash
git add WikiArticles/RocketPartProductivityResearch.txt
git commit -m "feat: generate Rocket Part Productivity wiki article"
```

---

### Task 4: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add text output command to the productivity section**

In `README.md`, the single-research text commands end with `python3 factorio_productivity.py rocket_fuel`. Add after it:

```
python3 factorio_productivity.py rocket_part
```

- [ ] **Step 2: Add wiki regeneration command**

In `README.md`, the wiki regeneration commands end with `python3 factorio_productivity.py rocket_fuel --wiki > WikiArticles/RocketFuelProductivityResearch.txt`. Add after it:

```
python3 factorio_productivity.py rocket_part --wiki > WikiArticles/RocketPartProductivityResearch.txt
```

- [ ] **Step 3: Add wiki articles table row**

In the `## Wiki Articles` table, after the `RocketFuelProductivityResearch.txt` row, add:

```
| `WikiArticles/RocketPartProductivityResearch.txt` | Rocket part productivity (research) - Thresholds section |
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add Rocket Part Productivity to README"
```

---

### Task 5: Update CLAUDE.md verification section

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add rocket_part verification block**

In `CLAUDE.md`, after the `rocket_fuel` verification block, add:

```
python3 factorio_productivity.py rocket_part
# Breakpoints: [0, 10, 20, 24, 26, 30]
# Level 20 / Rocket silo+LP3: 300% (first cap)
# Level 30 / Rocket silo+none: 300% (last cap)

python3 factorio_productivity.py rocket_part --wiki > WikiArticles/RocketPartProductivityResearch.txt
```

Also add the Rocket Part Productivity parameters section (mirrors the other research parameter sections already in CLAUDE.md):

```
Rocket Part Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(2000, 30)` - packs: Automation + Logistic + Chemical + Production + Cryogenic
- Machines: Rocket silo (column order)
- Applies to [[Rocket part]] recipe (Rocket silo)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add Rocket Part Productivity spec to CLAUDE.md"
```

---

### Task 6: Final verification

- [ ] **Step 1: Run all researches to confirm no regressions**

```bash
python3 factorio_productivity.py
```

Expected: all 6 researches print (steel_plate, processing_unit, low_density_structure, plastic_bar, rocket_fuel, rocket_part) without errors.

- [ ] **Step 2: Regenerate all wiki articles and confirm no diffs on existing ones**

```bash
python3 factorio_productivity.py steel_plate --wiki > /tmp/sp.txt && diff /tmp/sp.txt WikiArticles/SteelPlateProductivityResearch.txt
python3 factorio_productivity.py processing_unit --wiki > /tmp/pu.txt && diff /tmp/pu.txt WikiArticles/ProcessingUnitProductivityResearch.txt
python3 factorio_productivity.py low_density_structure --wiki > /tmp/lds.txt && diff /tmp/lds.txt WikiArticles/LowDensityStructureProductivityResearch.txt
python3 factorio_productivity.py plastic_bar --wiki > /tmp/pb.txt && diff /tmp/pb.txt WikiArticles/PlasticBarProductivityResearch.txt
python3 factorio_productivity.py rocket_fuel --wiki > /tmp/rf.txt && diff /tmp/rf.txt WikiArticles/RocketFuelProductivityResearch.txt
```

Expected: all diffs are empty (no output).

- [ ] **Step 3: Confirm rocket_part wiki output is committed and matches**

```bash
python3 factorio_productivity.py rocket_part --wiki > /tmp/rp.txt && diff /tmp/rp.txt WikiArticles/RocketPartProductivityResearch.txt
```

Expected: empty diff.
