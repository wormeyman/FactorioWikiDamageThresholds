# Steel Plate Productivity Thresholds - Design Spec

**Date:** 2026-04-16
**Status:** Approved

## Overview

Add a `== Thresholds ==` section to the Steel Plate Productivity (research) wiki page showing the current productivity bonus at each research level for each machine and module configuration. Table ends when all configurations reach the 300% cap. Mirrors the structure of the existing damage research threshold tables.

Also update `CLAUDE.md` to reflect the current `WikiArticles/` folder structure.

## Productivity Formula

```
total_prod = base_prod + module_prod + research_bonus
module_prod = module_slots * bonus_per_module
research_bonus = 0.10 * level
cap = 3.00 (300%)
min_level_to_cap = ceil((3.00 - base_prod - module_prod) / 0.10)
```

No overkill factor. No rounding per-hit. Pure additive stacking.

## Machine Data

| Machine | Base productivity | Module slots |
|---|---|---|
| Foundry | 50% (for metallurgical recipes) | 4 |
| Electric furnace | 0% | 2 |

Foundry base productivity verified against known wiki breakpoints: level 25 with no modules = 50% + 250% = 300% ✓.

## Module Data

| Module | Productivity per module |
|---|---|
| Productivity module 3 (normal) | +10% |
| Productivity module 2 (legendary) | +15% |
| Productivity module 3 (legendary) | +25% |

Four configurations are shown per machine: no modules, all slots filled with each of the three module types above.

## Research Data

- Tech name: `Steel plate productivity (research)`
- Bonus per level: +10%
- Cost per level: `1,000 × 1.5^N` science packs (Automation + Logistic + Chemical + Production)
- Cumulative cost to reach level N: `sum(1000 × 1.5^k for k in 1..N)`
- No useful effect beyond level 30 (300% cap hit by all configurations at or before level 30)

## Table Structure

Rows = research levels at which at least one configuration first reaches 300%. Level 0 always included as baseline. Level 30 is the final row (last configuration caps here); its level cell gets a `+` suffix.

Columns:
1. Level - `{{Icontech|Steel plate productivity (research)|N}}`
2. Cumulative research cost
3-10. One column per (machine × module config), ordered: Foundry configs first, then Electric furnace configs. Within each machine: no modules, NP3, LP2, LP3.

Cells show the current total productivity % as plain text (e.g. `150%`). Once a configuration reaches 300%, its cell uses rowspan to merge downward through all remaining rows - identical to the rowspan merging used in damage tables for shot counts that don't change.

### Computed breakpoint levels

| Level | Foundry (no mod) | Foundry (4×NP3) | Foundry (4×LP2) | Foundry (4×LP3) | E.Furn (no mod) | E.Furn (2×NP3) | E.Furn (2×LP2) | E.Furn (2×LP3) |
|---|---|---|---|---|---|---|---|---|
| 0 | 50% | 90% | 110% | 150% | 0% | 20% | 30% | 50% |
| 15 | 200% | 240% | 260% | **300%** | 150% | 170% | 180% | 200% |
| 19 | 240% | 280% | **300%** | merged | 190% | 210% | 220% | 240% |
| 21 | 260% | **300%** | merged | merged | 210% | 230% | 240% | 260% |
| 25 | **300%** | merged | merged | merged | 250% | 270% | 280% | **300%** |
| 27 | merged | merged | merged | merged | 270% | 290% | **300%** | merged |
| 28 | merged | merged | merged | merged | 280% | **300%** | merged | merged |
| 30 | merged | merged | merged | merged | **300%** | merged | merged | merged |

## Output

Generated MediaWiki markup saved to `WikiArticles/SteelPlateProductivityResearch.txt`. The file begins with a `== Thresholds ==` header and intro paragraph, followed by the wiki table.

Script usage: `python3 factorio_productivity.py steel_plate [--wiki]`

## New File: `factorio_productivity.py`

Architecture mirrors `factorio_thresholds.py` with three top-level data dicts and generic output functions.

### Data dicts

```python
MACHINES = {
    'Foundry': {'base_prod': 0.50, 'module_slots': 4},
    'Electric furnace': {'base_prod': 0.00, 'module_slots': 2},
}

MODULES = {
    'No modules':              0.00,  # per-module bonus; 0.00 × any slot count = 0
    'Prod module 3':           0.10,
    'Legendary Prod module 2': 0.15,
    'Legendary Prod module 3': 0.25,
}
```

### Research dict entry

```python
RESEARCHES = {
    'steel_plate': {
        'name': 'Steel Plate Productivity',
        'tech_name': 'Steel plate productivity (research)',
        'bonus_per_level': 0.10,
        'cost_fn': _sp_cumulative_costs,
        'max_level': 30,
        'machines': ['Foundry', 'Electric furnace'],
        'module_configs': [
            'No modules',
            'Prod module 3',
            'Legendary Prod module 2',
            'Legendary Prod module 3',
        ],
        'cap': 3.00,
    }
}
```

### Key functions

```python
def total_prod(base: float, slots: int, module_bonus: float, level: int,
               bonus_per_level: float) -> float:
    """Total productivity bonus at a given research level."""
    return base + slots * module_bonus + level * bonus_per_level


def min_level_to_cap(base: float, slots: int, module_bonus: float,
                     bonus_per_level: float, cap: float) -> int:
    """Minimum research level to reach the productivity cap."""
    return math.ceil((cap - base - slots * module_bonus) / bonus_per_level)


def find_breakpoints(research: dict) -> list[int]:
    """Levels at which at least one column first reaches cap. Always includes 0."""
    ...


def _sp_cumulative_costs(max_lvl: int = 30) -> dict:
    """Cumulative science pack cost to reach each level.
    Cost per level: 1000 * 1.5^N.
    """
    ...
```

### Wiki table format

- Caption: `Productivity bonus at each research level`
- 2-row header: `Level (rowspan=2) | Cost (rowspan=2) | Foundry (colspan=4) | Electric furnace (colspan=4)`
- Second header row: module config icons/names
- Data cells: plain text percentage (e.g. `150%`); `300%` cells use rowspan merging
- Level cells: `{{Icontech|Steel plate productivity (research)|N}}`; last row appends `+`

## CLAUDE.md Updates

The following paths in `CLAUDE.md` are stale and must be updated to reflect the current `WikiArticles/` subfolder:

| Old path | New path |
|---|---|
| `StrongerExplosivesResearch.txt` | `WikiArticles/StrongerExplosivesResearch.txt` |
| `enemies_wiki.json` | `WikiArticles/enemies_wiki.json` |

Also add entries for the new files:
- `WikiArticles/Technologies.json` - Factorio wiki API response for the Technologies page
- `WikiArticles/ArtilleryShellDamageResearch.txt` - generated wiki markup for artillery shell damage
- `factorio_productivity.py` - source of truth for productivity threshold calculations
- `WikiArticles/SteelPlateProductivityResearch.txt` - generated wiki markup for steel plate productivity
