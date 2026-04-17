# Processing Unit Productivity - Design Spec

**Date:** 2026-04-17
**Branch:** ProcessingUnitProductivity

## Summary

Add Processing unit productivity research to `factorio_productivity.py` and generate a new wiki article `WikiArticles/ProcessingUnitProductivityResearch.txt`. Refactor the cost function to be shared across all productivity researches (in preparation for 5+ more to follow).

## Research Parameters

| Parameter | Value |
|-----------|-------|
| Tech name | Processing unit productivity (research) |
| Bonus per level | +10% |
| Max level | 30 |
| Productivity cap | 300% |
| Cost per level N | `round(1000 × 1.5^N)` packs |
| Science packs | Automation, Logistic, Chemical, Production, Electromagnetic |

## Machines

| Machine | Base productivity | Module slots |
|---------|-------------------|--------------|
| Assembling machine 3 | 0% | 4 |
| Electromagnetic plant | 50% | 5 |

## Module Configurations

- No modules
- Prod module 3 (10% per slot)
- Legendary Prod module 2 (15% per slot)
- Legendary Prod module 3 (25% per slot)

## Notable / Pinned Levels

- Level 10 - Assembling machine 3 + no modules hits 100%
- Level 20 - Assembling machine 3 + no modules hits 200%
- Level 30 - max level (always included as last row regardless)

## Auto-detected Breakpoints

Levels where at least one configuration first reaches 300%:

| Level | Configuration that first caps |
|-------|-------------------------------|
| 13 | Electromagnetic plant + 5x Legendary Prod 3 |
| 18 | Electromagnetic plant + 5x Legendary Prod 2 |
| 20 | Assembling machine 3 + 4x Legendary Prod 3; Electromagnetic plant + 5x Prod 3 |
| 24 | Assembling machine 3 + 4x Legendary Prod 2 |
| 25 | Electromagnetic plant + no modules |
| 26 | Assembling machine 3 + 4x Prod 3 |
| 30 | Assembling machine 3 + no modules |

Final row set (sorted, deduplicated): 0, 10, 13, 18, 20, 24, 25, 26, 30

## Code Changes

### 1. Shared cost function (replaces `_sp_cumulative_costs`)

```python
def _cumulative_costs(cost_base: int, max_lvl: int, multiplier: float = 1.5) -> dict:
    total = 0
    result = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += round(cost_base * multiplier ** lvl)
        result[lvl] = _si(total)
    return result
```

`steel_plate` updates its `cumulative_costs` field to call `_cumulative_costs(1000, 30)` - identical output.

### 2. MACHINES addition

```python
'Assembling machine 3': {'base_prod': 0.00, 'module_slots': 4},
```

### 3. _MACHINE_ICONS addition

```python
'Assembling machine 3': '{{Icon|Assembling machine 3}}',
```

### 4. RESEARCHES addition

```python
'processing_unit': {
    'name': 'Processing Unit Productivity',
    'tech_name': 'Processing unit productivity (research)',
    'bonus_per_level': 0.10,
    'cumulative_costs': _cumulative_costs(1000, 30),
    'max_level': 30,
    'cap': 3.00,
    'notable_levels': [10, 20],
    'machines': ['Assembling machine 3', 'Electromagnetic plant'],
    'module_configs': [
        'No modules',
        'Prod module 3',
        'Legendary Prod module 2',
        'Legendary Prod module 3',
    ],
    'intro': (
        "== Thresholds ==\n"
        "The table below shows the total productivity bonus at key research levels"
        " for [[Processing unit productivity (research)]]{{SA}}, for each machine and"
        " module configuration. Productivity is capped at 300%; cells shown in"
        " '''bold''' indicate that the configuration has reached the cap at that"
        " level and will not improve further with additional research.\n"
    ),
}
```

## Output

```bash
python3 factorio_productivity.py processing_unit --wiki > WikiArticles/ProcessingUnitProductivityResearch.txt
```

## Verification

```bash
python3 factorio_productivity.py processing_unit
# Level 10: AM3+none = 100%, EM plant+none = 150%
# Level 13: EM plant+LP3 = 300% (first cap)
# Level 20: AM3+LP3 = 300%, EM plant+PM3 = 300%
# Level 30: AM3+none = 300% (last cap)

python3 factorio_productivity.py steel_plate
# Output unchanged after _cumulative_costs refactor
```
