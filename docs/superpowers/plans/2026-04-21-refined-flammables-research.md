# Refined Flammables Research Tree Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `refined_flammables` tree to `factorio_thresholds.py` that outputs a MediaWiki table showing fluid units (crude oil / light oil) consumed by the Flamethrower turret to destroy behemoth biters and spitters at each research level 0-20.

**Architecture:** The flamethrower is a continuous stream weapon, so "shots to kill" is replaced by "fluid units to kill" via a new `units_per_shot` field on the tree dict. The renderer's `_col_display` function propagates this field (seeded from the tree into each column dict by `build_columns`) and applies `ceil(shots × units_per_shot)` before emitting the cell value. The research multiplier follows the same double-stacking pattern as Physical Projectile research: `rf_mult(level) = rf_single(level)²`.

**Tech Stack:** Python 3, MediaWiki markup, `factorio_thresholds.py` (single-file renderer)

---

### Task 1: Add `units_per_shot` support to the renderer

**Files:**
- Modify: `factorio_thresholds.py:455-488` (`build_columns`)
- Modify: `factorio_thresholds.py:517-524` (`_col_display`)

- [ ] **Step 1: Write a quick sanity-check script to confirm current behaviour before touching anything**

Create a throwaway script (not committed) to pin the existing output of one tree:

```bash
python3 factorio_thresholds.py laser_weapons 2>/dev/null | head -6
```

Expected output (approximate - exact numbers don't matter, just confirm it runs):
```
=== Laser Weapons (laser turret vs asteroids) (max level 20) ===
       Level  Smal  Medi
-------------  ----  ----
           0    27   400
           1    23   334
```

- [ ] **Step 2: Add `units_per_shot` to each column dict in `build_columns`**

In `factorio_thresholds.py`, find `build_columns` (starts at line 455). Inside `cols.append({...})`, add one new key at the end of the dict (after `'hits_per_activation'`):

```python
                'hits_per_activation': target.get('hits_per_activation', 1),
                'units_per_shot':      tree.get('units_per_shot'),
```

The full updated `cols.append` block (lines 473-488) should look like:

```python
                cols.append({
                    'group':               group_name,
                    'target':              target_name,
                    'weapon':              weapon_name,
                    'label':               f'{target_name} / {weapon_name}',
                    'hp':                  target['hp'],
                    'overkill':            overkill,
                    'base_dmg':            base_dmg,
                    'resist':              resist,
                    'header_icon':         header_icon,
                    'data_icon_name':      data_icon_name,
                    'magazine_size':       magazine_size,
                    'round_per_hit':       tree.get('round_per_hit', False),
                    'extra_resists':       extra_resists,
                    'hits_per_activation': target.get('hits_per_activation', 1),
                    'units_per_shot':      tree.get('units_per_shot'),
                })
```

- [ ] **Step 3: Modify `_col_display` to apply `units_per_shot`**

Find `_col_display` (line 517). Replace the entire function body:

```python
def _col_display(col: dict, mult: float) -> int:
    """Display units (magazines, single shots, or fluid units) to kill the target.

    For magazine weapons (magazine_size > 1) this is ceil(bullets / size).
    For fluid weapons (units_per_shot set) this is ceil(shots * units_per_shot).
    Breakpoints are built from display values so rows only split on visible changes.
    """
    shots = _col_shots(col, mult)
    mags = math.ceil(shots / col['magazine_size'])
    upc = col.get('units_per_shot')
    if upc is not None:
        return math.ceil(mags * upc)
    return mags
```

- [ ] **Step 4: Verify existing trees are unaffected**

Run a few existing trees and confirm output is identical to Step 1:

```bash
python3 factorio_thresholds.py laser_weapons 2>/dev/null | head -6
python3 factorio_thresholds.py electric_weapons_damage 2>/dev/null | head -8
```

Both should produce the same output as before (no `units_per_shot` set on those trees → `upc is None` → unchanged path).

- [ ] **Step 5: Commit**

```bash
git add factorio_thresholds.py
git commit -m "feat: add units_per_shot renderer support for fluid-based weapons"
```

---

### Task 2: Add multiplier and cost functions

**Files:**
- Modify: `factorio_thresholds.py` — insert after `_ewd_cumulative_costs` (around line 314), before `TREES = {`

- [ ] **Step 1: Verify the expected multiplier values by hand before writing the function**

At the Python REPL, confirm the lookup table values derived from `data/factorioraw.json`:

```python
# Per-level ammo-damage modifiers from factorioraw.json:
# Levels 1-3: 0.2, levels 4-5: 0.3, level 6: 0.4, levels 7+: 0.2
# Cumulative:
mods = [0.2, 0.2, 0.2, 0.3, 0.3, 0.4]
cum = 0.0
for i, m in enumerate(mods, 1):
    cum += m
    print(f'Level {i}: single={1+cum:.1f}, total={(1+cum)**2:.4f}')
# Expected:
# Level 1: single=1.2, total=1.4400
# Level 2: single=1.4, total=1.9600
# Level 3: single=1.6, total=2.5600
# Level 4: single=1.9, total=3.6100
# Level 5: single=2.2, total=4.8400
# Level 6: single=2.6, total=6.7600
import math
# Level 0 / crude / behemoth biter (3000 HP, no fire resist):
# pulses = ceil(3000 / (3.0 * 1.0)) = 1000
# fluid  = ceil(1000 * 0.8) = 800
print(math.ceil(math.ceil(3000 / (3.0 * 1.0)) * 0.8))   # → 800
# Level 6 / crude:
print(math.ceil(math.ceil(3000 / (3.0 * 6.76)) * 0.8))  # → 119
# Level 6 / light (1.1x):
print(math.ceil(math.ceil(3000 / (3.3 * 6.76)) * 0.8))  # → 109
```

- [ ] **Step 2: Insert `rf_single`, `rf_mult`, and `_rf_cumulative_costs` into the file**

Open `factorio_thresholds.py`. Find the line `TREES = {` (currently line 317). Insert the following block immediately above it, after `_ewd_cumulative_costs`:

```python
_RF = {0: 0.0, 1: 0.2, 2: 0.4, 3: 0.6, 4: 0.9, 5: 1.2, 6: 1.6}


def rf_single(level: int) -> float:
    """Cumulative single-factor bonus (ammo-damage or turret-attack separately).

    Levels 1-3: +0.2/level, levels 4-5: +0.3/level, level 6: +0.4,
    levels 7+: +0.2/level (infinite research).
    """
    if level <= 6:
        return 1.0 + _RF[level]
    return 2.6 + 0.2 * (level - 6)


def rf_mult(level: int) -> float:
    """Refined Flammables total damage multiplier.

    Both ammo-damage and turret-attack each get rf_single independently
    (same pattern as Physical Projectile research). Total = rf_single^2.
    """
    m = rf_single(level)
    return m * m


def _rf_cumulative_costs(max_lvl: int = 20) -> dict:
    """Cumulative total science pack cost to REACH each refined flammables level.

    Levels 1-6: fixed count × pack type count (derived from factorioraw.json).
    Level 7+: 2^(L-7)*1000 packs × 7 types per level (infinite formula).
    """
    _PER_LEVEL = {
        1: 100 * 3,
        2: 200 * 3,
        3: 300 * 4,
        4: 400 * 4,
        5: 500 * 5,
        6: 600 * 6,
    }
    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        if lvl <= 6:
            total += _PER_LEVEL[lvl]
        else:
            total += 7 * (2 ** (lvl - 7)) * 1000
        result[lvl] = _si(total)
    return result


```

- [ ] **Step 3: Spot-check the multiplier function at the command line**

```bash
python3 -c "
from factorio_thresholds import rf_mult, _rf_cumulative_costs
import math
# Multiplier checks
assert abs(rf_mult(0) - 1.0)   < 1e-9, rf_mult(0)
assert abs(rf_mult(1) - 1.44)  < 1e-9, rf_mult(1)
assert abs(rf_mult(3) - 2.56)  < 1e-9, rf_mult(3)
assert abs(rf_mult(6) - 6.76)  < 1e-9, rf_mult(6)
assert abs(rf_mult(7) - 7.84)  < 1e-9, rf_mult(7)
# Fluid unit checks (crude oil, behemoth biter 3000 HP)
def fluid(hp, base, mult): return math.ceil(math.ceil(hp / (base * mult)) * 0.8)
assert fluid(3000, 3.0, rf_mult(0))  == 800,  fluid(3000, 3.0, rf_mult(0))
assert fluid(3000, 3.3, rf_mult(0))  == 728,  fluid(3000, 3.3, rf_mult(0))
assert fluid(3000, 3.0, rf_mult(6))  == 119,  fluid(3000, 3.0, rf_mult(6))
assert fluid(3000, 3.3, rf_mult(6))  == 109,  fluid(3000, 3.3, rf_mult(6))
assert fluid(1500, 3.0, rf_mult(6))  == 60,   fluid(1500, 3.0, rf_mult(6))
# Cost spot-checks
costs = _rf_cumulative_costs()
assert costs[1] == '300',  costs[1]
assert costs[6] == '9.8k', costs[6]
print('All assertions passed.')
"
```

Expected: `All assertions passed.`

- [ ] **Step 4: Commit**

```bash
git add factorio_thresholds.py
git commit -m "feat: add rf_mult and _rf_cumulative_costs for Refined Flammables"
```

---

### Task 3: Add the `refined_flammables` tree entry

**Files:**
- Modify: `factorio_thresholds.py` — add entry to `TREES` dict (after `'electric_weapons_damage'` entry, before closing `}`)

- [ ] **Step 1: Add the tree entry**

Open `factorio_thresholds.py`. Find the closing `}` of `TREES` (the last `}` of the `electric_weapons_damage` entry, around line 447). Add a comma after that entry's closing `}` if missing, then add:

```python
    'refined_flammables': {
        'name': 'Refined Flammables (flamethrower turret vs enemies)',
        'mult_fn': rf_mult,
        'tech_name': 'Refined flammables (research)',
        'cumulative_costs': _rf_cumulative_costs(),
        'caption': 'Fluid units required to destroy enemy',
        'units_per_shot': 0.8,
        'max_level': 20,
        'weapons': [
            ('Crude oil', 3.0, 'fire', '{{Icon|Crude oil}}', 'Crude oil', 1),
            ('Light oil', 3.3, 'fire', '{{Icon|Light oil}}', 'Light oil', 1),
        ],
        'target_groups': [
            ('Enemies', {
                'Behemoth Biter':   BITERS['Behemoth Biter'],
                'Behemoth Spitter': SPITTER_ENEMIES['Behemoth Spitter'],
            }, 1.0),
        ],
        'target_wiki_labels': {
            'Behemoth Biter':  '{{Icon|Behemoth_biter}}',
            'Behemoth Spitter': '{{Icon|Behemoth_spitter}}',
        },
    },
```

- [ ] **Step 2: Run the text output and verify key values**

```bash
python3 factorio_thresholds.py refined_flammables
```

Check the output against these expected values:

| Level range | Crude/Biter | Light/Biter | Crude/Spitter | Light/Spitter |
|-------------|-------------|-------------|---------------|---------------|
| 0 | 800 | 728 | 400 | 364 |
| 1 | 556 | 506 | 278 | 253 |
| 3 | 313 | 285 | 157 | 143 |
| 6 | 119 | 109 | 60 | 55 |
| 10 | 70 | 64 | 35 | 32 |
| 20 | 28 | 26 | 14 | 13 |

If any value is wrong, re-check the `rf_mult` lookup table against the per-level modifier values from `data/factorioraw.json`.

- [ ] **Step 3: Confirm no regressions on other trees**

```bash
python3 factorio_thresholds.py stronger_explosives 2>/dev/null | grep -E "^\s+0\s" | head -3
python3 factorio_thresholds.py electric_weapons_damage 2>/dev/null | grep -E "^\s+0\s" | head -3
```

Both should match their previous output (no changes to those trees' logic).

- [ ] **Step 4: Commit**

```bash
git add factorio_thresholds.py
git commit -m "feat: add Refined Flammables research tree (flamethrower vs behemoth biters/spitters)"
```

---

### Task 4: Generate wiki output file

**Files:**
- Create: `WikiArticles/RefinedFlammablesResearch.txt`

- [ ] **Step 1: Generate the wiki markup**

```bash
python3 factorio_thresholds.py refined_flammables --wiki > WikiArticles/RefinedFlammablesResearch.txt
```

- [ ] **Step 2: Spot-check the generated file**

```bash
head -20 WikiArticles/RefinedFlammablesResearch.txt
```

Expected to see:
- `<!-- Refined Flammables ... -->` comment
- `{| class="wikitable" ...`
- `! colspan="6" | Fluid units required to destroy enemy`
- Header row with `{{Icon|Crude oil}}` and `{{Icon|Light oil}}`
- First data row with `{{Icontech|Refined flammables (research)|0}}`

Also spot-check a mid-table value:

```bash
grep -c "Icontech" WikiArticles/RefinedFlammablesResearch.txt
```

Should be > 0.

- [ ] **Step 3: Commit**

```bash
git add WikiArticles/RefinedFlammablesResearch.txt
git commit -m "feat: generate RefinedFlammablesResearch.txt wiki markup"
```

---

### Task 5: Update CLAUDE.md and README.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Add the new txt file to CLAUDE.md's Repository Overview section**

In `CLAUDE.md`, find the line for `WikiArticles/ElectricWeaponsDamageResearch.txt`. Add a new line after it:

```
- **`WikiArticles/RefinedFlammablesResearch.txt`** - MediaWiki markup source for the "Refined flammables (research)" wiki page thresholds section.
```

- [ ] **Step 2: Add the verification command to CLAUDE.md's Verification section**

In `CLAUDE.md`, find the `python3 factorio_thresholds.py electric_weapons_damage --wiki` block. Add after it:

```
python3 factorio_thresholds.py refined_flammables
# Level 0 / Crude oil / Behemoth Biter:   800
# Level 0 / Light oil / Behemoth Biter:   728
# Level 6 / Crude oil / Behemoth Biter:   119
# Level 20 / Crude oil / Behemoth Biter:  28

python3 factorio_thresholds.py refined_flammables --wiki > WikiArticles/RefinedFlammablesResearch.txt
```

- [ ] **Step 3: Update README.md**

In `README.md`, find where `factorio_thresholds.py` trees are listed. Add `refined_flammables` to the list of available trees, including the `--wiki` command:

```
python3 factorio_thresholds.py refined_flammables --wiki
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: document Refined Flammables tree in CLAUDE.md and README.md"
```

---

### Task 6: Push and open PR

- [ ] **Step 1: Push branch and open PR**

```bash
git push -u origin HEAD
gh pr create \
  --title "feat: add Refined Flammables research tree (flamethrower vs biters/spitters)" \
  --body "$(cat <<'EOF'
## Summary

- Adds \`refined_flammables\` tree to \`factorio_thresholds.py\` covering the Flamethrower turret vs Behemoth Biter and Behemoth Spitter at levels 0-20
- Introduces \`units_per_shot\` field to the tree/column system so the renderer outputs fluid units consumed (crude oil and light oil columns) instead of raw shot counts
- Multiplier follows the same double-stacking pattern as Physical Projectile research: both \`ammo-damage\` and \`turret-attack\` apply independently, so \`rf_mult(level) = rf_single(level)²\`
- Generates \`WikiArticles/RefinedFlammablesResearch.txt\` for wiki upload

## Test plan

- [ ] \`python3 factorio_thresholds.py refined_flammables\` — verify level 0 crude/biter = 800, light/biter = 728
- [ ] \`python3 factorio_thresholds.py refined_flammables --wiki\` — check wikitable structure
- [ ] Run existing trees (laser_weapons, electric_weapons_damage) — confirm no regressions
EOF
)"
```
