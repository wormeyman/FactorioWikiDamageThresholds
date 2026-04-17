# Low Density Structure Productivity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Low density structure productivity research to `factorio_productivity.py`, update the Foundry icon to include `space-age=yes`, and generate the wiki article `WikiArticles/LowDensityStructureProductivityResearch.txt`.

**Architecture:** Two data-only changes to `factorio_productivity.py` (icon tweak + new RESEARCHES entry), followed by generating two wiki output files and updating README.md. No new machines or cost functions needed — both machines and `_cumulative_costs` already exist.

**Tech Stack:** Python 3, MediaWiki markup, `factorio_productivity.py` (single-file script)

---

### Task 1: Update Foundry icon and regenerate SteelPlateProductivityResearch.txt

**Files:**
- Modify: `factorio_productivity.py:234` (`_MACHINE_ICONS` Foundry entry)
- Modify: `WikiArticles/SteelPlateProductivityResearch.txt` (regenerated)

- [ ] **Step 1: Update the Foundry icon**

In `factorio_productivity.py`, find `_MACHINE_ICONS` (around line 233). Change the `Foundry` entry:

```python
_MACHINE_ICONS = {
    'Foundry':               '{{Icon|Foundry|space-age=yes}}',
    'Electric furnace':      '{{Icon|Electric furnace}}',
    'Assembling machine 3':  '{{Icon|Assembling machine 3}}',
    'Electromagnetic plant': '{{Icon|Electromagnetic plant}}',
}
```

- [ ] **Step 2: Verify text output unchanged**

Run:
```bash
python3 factorio_productivity.py steel_plate
```

Expected: identical breakpoints and percentages as before (`0, 10, 15, 19, 20, 21, 25, 27, 28, 30`). The icon change only affects `--wiki` output.

- [ ] **Step 3: Regenerate SteelPlateProductivityResearch.txt**

```bash
python3 factorio_productivity.py steel_plate --wiki > WikiArticles/SteelPlateProductivityResearch.txt
```

- [ ] **Step 4: Verify Foundry icon updated in wiki output**

```bash
grep "Foundry" WikiArticles/SteelPlateProductivityResearch.txt | head -3
```

Expected: `{{Icon|Foundry|space-age=yes}} Foundry` appears in the header row.

- [ ] **Step 5: Commit**

```bash
git add factorio_productivity.py WikiArticles/SteelPlateProductivityResearch.txt
git commit -m "fix: add space-age=yes to Foundry icon and regenerate steel plate wiki"
```

---

### Task 2: Add `low_density_structure` to RESEARCHES

**Files:**
- Modify: `factorio_productivity.py` (RESEARCHES dict, after `processing_unit` entry)

- [ ] **Step 1: Add the research entry**

In `factorio_productivity.py`, find the closing `}` of the `RESEARCHES` dict (after the `processing_unit` entry). Add the new entry:

```python
    'low_density_structure': {
        'name': 'Low Density Structure Productivity',
        'tech_name': 'Low density structure productivity (research)',
        'bonus_per_level': 0.10,
        'cumulative_costs': _cumulative_costs(1000, 30),
        'max_level': 30,
        'cap': 3.00,
        'intro': (
            "== Thresholds ==\n"
            "The table below shows the total productivity bonus at key research levels"
            " for [[Low density structure productivity (research)]]{{SA}}, for each machine and"
            " module configuration. Applies to {{icon|low density structure|}} Low density structure"
            " ({{Icon|Assembling machine 3}}) and {{icon|Casting low density structure|}} Casting"
            " low density structure ({{icon|Foundry|space-age=yes}} Foundry) recipes."
            " Productivity is capped at 300%; cells shown in '''bold''' indicate that the"
            " configuration has reached the cap at that level and will not improve further"
            " with additional research.\n"
        ),
        'notable_levels': [10, 20],
        'machines': ['Assembling machine 3', 'Foundry'],
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
python3 factorio_productivity.py low_density_structure
```

Expected row set: `0, 10, 15, 19, 20, 21, 24, 25, 26, 30`

Spot-check these values:

| Level | AM3+none | AM3+LP3 | Foundry+none | Foundry+LP3 |
|-------|----------|---------|--------------|-------------|
| 0     | 0%       | 100%    | 50%          | 150%        |
| 10    | 100%     | 200%    | 150%         | 250%        |
| 15    | 150%     | 250%    | 200%         | **300%**    |
| 20    | 200%     | **300%**| 250%         | **300%**    |
| 30    | **300%** | **300%**| **300%**     | **300%**    |

- [ ] **Step 3: Verify existing researches unaffected**

Run:
```bash
python3 factorio_productivity.py steel_plate processing_unit
```

Expected: steel_plate breakpoints `0, 10, 15, 19, 20, 21, 25, 27, 28, 30`; processing_unit breakpoints `0, 10, 13, 18, 20, 24, 25, 26, 30`. No errors.

- [ ] **Step 4: Commit**

```bash
git add factorio_productivity.py
git commit -m "feat: add low_density_structure research to factorio_productivity.py"
```

---

### Task 3: Generate wiki article and update docs

**Files:**
- Create: `WikiArticles/LowDensityStructureProductivityResearch.txt`
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Generate the wiki article**

```bash
python3 factorio_productivity.py low_density_structure --wiki > WikiArticles/LowDensityStructureProductivityResearch.txt
```

- [ ] **Step 2: Spot-check the output**

```bash
head -15 WikiArticles/LowDensityStructureProductivityResearch.txt
```

Expected: starts with `== Thresholds ==`, references `{{icon|low density structure|}}` and `{{icon|Casting low density structure|}}` in the intro, then the wikitable with `{{Icon|Assembling machine 3}} Assembling machine 3` and `{{Icon|Foundry|space-age=yes}} Foundry` as group headers.

Verify first bold cap at level 15:
```bash
grep "300%" WikiArticles/LowDensityStructureProductivityResearch.txt | head -3
```

Expected: first `'''300%'''` appears in the level-15 row (Foundry + LP3 column).

- [ ] **Step 3: Update README.md**

In `README.md`, add `low_density_structure` to both the text and `--wiki` command blocks, and add the new file to the Wiki Articles table.

The text output block becomes:
```markdown
# Text output (single research)
python3 factorio_productivity.py steel_plate
python3 factorio_productivity.py processing_unit
python3 factorio_productivity.py low_density_structure
```

The `--wiki` block becomes:
```markdown
# Regenerate wiki articles
python3 factorio_productivity.py steel_plate --wiki > WikiArticles/SteelPlateProductivityResearch.txt
python3 factorio_productivity.py processing_unit --wiki > WikiArticles/ProcessingUnitProductivityResearch.txt
python3 factorio_productivity.py low_density_structure --wiki > WikiArticles/LowDensityStructureProductivityResearch.txt
```

The Wiki Articles table gains:
```markdown
| `WikiArticles/LowDensityStructureProductivityResearch.txt` | Low density structure productivity (research) - Thresholds section |
```

- [ ] **Step 4: Update CLAUDE.md**

In `CLAUDE.md`, update the `factorio_productivity.py` description line to mention Low Density Structure Productivity:

```markdown
- **`factorio_productivity.py`** - Source of truth for productivity threshold calculations. Covers Steel Plate Productivity (foundry and electric furnace), Processing Unit Productivity (assembling machine 3 and electromagnetic plant), and Low Density Structure Productivity (assembling machine 3 and foundry), various module configs. Run with `python3 factorio_productivity.py [research] [--wiki]`.
```

Add the new wiki article file entry after ProcessingUnitProductivityResearch.txt:
```markdown
- **`WikiArticles/LowDensityStructureProductivityResearch.txt`** - MediaWiki markup source for the "Low density structure productivity (research)" wiki page thresholds section.
```

Add LDS parameters to the Productivity Formula section, after Processing Unit Productivity parameters:
```markdown
Low Density Structure Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(1000, 30)` - packs: Automation + Logistic + Chemical + Production + Metallurgic
```

Add LDS verification commands after the processing_unit block:
```markdown
python3 factorio_productivity.py low_density_structure
# Breakpoints: [0, 10, 15, 19, 20, 21, 24, 25, 26, 30]
# Level 10 / AM3+none: 100%
# Level 15 / Foundry+LP3: 300% (first cap)
# Level 30 / AM3+none: 300% (last cap)

python3 factorio_productivity.py low_density_structure --wiki > WikiArticles/LowDensityStructureProductivityResearch.txt
```

- [ ] **Step 5: Commit**

```bash
git add WikiArticles/LowDensityStructureProductivityResearch.txt README.md CLAUDE.md
git commit -m "feat: generate LowDensityStructureProductivity wiki article and update docs"
```
