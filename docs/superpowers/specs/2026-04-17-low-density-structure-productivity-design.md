# Low Density Structure Productivity - Design Spec

**Date:** 2026-04-17
**Branch:** LowDensityStructureProductivity

## Summary

Add Low density structure productivity research to `factorio_productivity.py` and generate `WikiArticles/LowDensityStructureProductivityResearch.txt`. Also update the Foundry icon in `_MACHINE_ICONS` to include `space-age=yes`, and regenerate `WikiArticles/SteelPlateProductivityResearch.txt` to pick up that change.

## Research Parameters

| Parameter | Value |
|-----------|-------|
| Tech name | Low density structure productivity (research) |
| Bonus per level | +10% |
| Max level | 30 |
| Productivity cap | 300% |
| Cost per level N | `_cumulative_costs(1000, 30)` |
| Science packs | Automation, Logistic, Chemical, Production, Metallurgic |

## Machines

Both already present in `MACHINES` and `_MACHINE_ICONS` - no additions needed.

| Machine | Base productivity | Module slots | Recipe |
|---------|-------------------|--------------|--------|
| Assembling machine 3 | 0% | 4 | Low density structure |
| Foundry | 50% | 4 | Casting low density structure |

## Icon Update

`_MACHINE_ICONS['Foundry']` changes from `'{{Icon|Foundry}}'` to `'{{Icon|Foundry|space-age=yes}}'`.

Side effect: `SteelPlateProductivityResearch.txt` must be regenerated after this change.

## Module Configurations

- No modules
- Prod module 3 (10% per slot)
- Legendary Prod module 2 (15% per slot)
- Legendary Prod module 3 (25% per slot)

## Notable / Pinned Levels

- Level 10 - Assembling machine 3 + no modules hits 100%
- Level 20 - Assembling machine 3 + no modules hits 200%
- Level 30 - max level (always last row)

## Auto-detected Breakpoints

| Level | Configuration that first caps |
|-------|-------------------------------|
| 15 | Foundry + 4x Legendary Prod 3 |
| 19 | Foundry + 4x Legendary Prod 2 |
| 20 | Assembling machine 3 + 4x Legendary Prod 3 |
| 21 | Foundry + 4x Prod 3 |
| 24 | Assembling machine 3 + 4x Legendary Prod 2 |
| 25 | Foundry + no modules |
| 26 | Assembling machine 3 + 4x Prod 3 |
| 30 | Assembling machine 3 + no modules |

Final row set: 0, 10, 15, 19, 20, 21, 24, 25, 26, 30

## Intro Text

```
== Thresholds ==
The table below shows the total productivity bonus at key research levels
for [[Low density structure productivity (research)]]{{SA}}, for each machine and
module configuration. Applies to {{icon|low density structure|}} Low density structure
({{Icon|Assembling machine 3}}) and {{icon|Casting low density structure|}} Casting
low density structure ({{icon|Foundry|space-age=yes}} Foundry) recipes.
Productivity is capped at 300%; cells shown in '''bold''' indicate that the
configuration has reached the cap at that level and will not improve further
with additional research.
```

## Code Changes

### 1. Update Foundry icon in `_MACHINE_ICONS`

```python
'Foundry': '{{Icon|Foundry|space-age=yes}}',
```

### 2. Add `low_density_structure` to RESEARCHES

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
}
```

## Output Files

```bash
python3 factorio_productivity.py low_density_structure --wiki > WikiArticles/LowDensityStructureProductivityResearch.txt
python3 factorio_productivity.py steel_plate --wiki > WikiArticles/SteelPlateProductivityResearch.txt
```

## Verification

```bash
python3 factorio_productivity.py low_density_structure
# Breakpoints: [0, 10, 15, 19, 20, 21, 24, 25, 26, 30]
# Level 10 / AM3+none: 100%
# Level 15 / Foundry+LP3: 300% (first cap)
# Level 30 / AM3+none: 300% (last cap)

python3 factorio_productivity.py steel_plate
# Output unchanged except Foundry icon now includes space-age=yes in wiki output
```
