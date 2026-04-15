# Artillery Shell Damage Thresholds - Design Spec

**Date:** 2026-04-15
**Status:** Approved

## Overview

Add a `== Thresholds ==` section to the Artillery Shell Damage (research) wiki page showing how many artillery shells are required to destroy enemies at each research level. This mirrors the thresholds sections on the Physical Projectile Damage and Laser Weapons Damage research pages.

## Weapon Data

Artillery shell deals two independent damage components per shot, both scaled by the research multiplier:

- 1000 physical damage
- 1000 explosion damage

Research multiplier: `mult(n) = 1.0 + 0.10 * n` (simple linear, 10% per level, no lookup table).

No overkill factor (1.0) - this applies to rocket turrets only, not artillery.

## Targets

Only the three targets with meaningful breakpoints are included. All other enemies (small worm, medium worm, big worm, small egg raft) are always destroyed in one hit at any research level and are noted in the intro text instead.

### Included targets

| Target | HP (max-evolution) | Physical resist | Explosion resist |
|---|---|---|---|
| Behemoth worm | 3000 | (10 flat, 0%) | (10 flat, 30%) |
| Biter spawner / Spitter spawner | 3500 | (2 flat, 15%) | (5 flat, 0%) |
| Egg raft | 5000 | (2 flat, 15%) | (5 flat, 15%) |

Spawner HP is max-evolution (base is 350). Egg raft HP is max-evolution (base is 500). Worm HP is fixed.

Biter spawner and spitter spawner share identical stats and are merged into a single column with both icons in the header.

### Excluded targets (always 1-shot)

| Target | HP |
|---|---|
| Small worm | 200 |
| Medium worm | 500 |
| Big worm | 1500 |
| Small egg raft | 1000 (max-evo) |

## Damage Formula

```
dmg_physical  = max(1000 * mult - flat_p, 1) * (1 - pct_p)
dmg_explosion = max(1000 * mult - flat_e, 1) * (1 - pct_e)
total_damage  = dmg_physical + dmg_explosion
shells        = ceil(hp / total_damage)
```

## Research Costs

7 science pack types per level (Automation, Logistic, Military, Chemical, Utility, Space, Metallurgic), each requiring `2^(L-1) * 1000` units.

Cumulative cost formula: `7000 * (2^n - 1)` total packs to reach level n.

## Table Structure

Styled like the Physical Projectile Damage thresholds table:
- `{{Icontech|Artillery shell damage (research)|N}}` level cells
- `{{Icon|Artillery shell|N}}` data cells
- Cumulative research cost column (second column)
- Caption: "Shells required to destroy enemy"

### Column header icons

| Column | Wiki markup |
|---|---|
| Behemoth worm | `{{Icon|Behemoth_worm}}` |
| Spawner (biter + spitter) | `{{Icon|Biter_nest}}` |
| Egg raft | `{{Icon|Egg_raft}}` |

### Rows

Levels 0-9 shown individually. Levels 10-19 combined (shell counts unchanged throughout). Level 20 shown individually (egg raft becomes 1-shot).

| Level | Cost | Behemoth worm | Spawner | Egg raft |
|---|---|---|---|---|
| 0 | - | 2 | 2 | 3 |
| 1 | 7k | 2 | 2 | 3 |
| 2 | 21k | 2 | 2 | 3 |
| 3 | 49k | 2 | 2 | 3 |
| 4 | 105k | 2 | 2 | 3 |
| 5 | 217k | 2 | 2 | 2 |
| 6 | 441k | 2 | 2 | 2 |
| 7 | 889k | 2 | 2 | 2 |
| 8 | 1.79M | 1 | 2 | 2 |
| 9 | 3.58M | 1 | 1 | 2 |
| 10-19 | 7.16M - 3.67G | 1 | 1 | 2 |
| 20 | 7.34G | 1 | 1 | 1 |

Per-column rowspan merging applies within this fixed row structure (not automatic breakpoint-based).

## Code Changes to `factorio_thresholds.py`

### 1. New multiplier function

```python
def asd_mult(level: int) -> float:
    return 1.0 + 0.10 * level
```

### 2. New cumulative cost function

```python
def _asd_cumulative_costs(max_lvl: int = 30) -> dict:
    total = 0
    result = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += 7 * (2 ** (lvl - 1)) * 1000
        result[lvl] = _si(total)
    return result
```

### 3. Dual-damage support

Artillery shells deal two independent damage types per shot. The existing `shots_needed` function handles a single damage type. A new helper is needed:

```python
def dual_shots_needed(hp, base1, mult, resist1, base2, resist2):
    dmg1 = max(base1 * mult - resist1[0], 1) * (1 - resist1[1])
    dmg2 = max(base2 * mult - resist2[0], 1) * (1 - resist2[1])
    return math.ceil(hp / (dmg1 + dmg2) - 1e-9)
```

### 4. Target data

Add worm, spawner (max-evo), and egg raft (max-evo) entries to a new `ARTILLERY_TARGETS` dict (or inline in the tree definition).

### 5. New tree entry

Add `artillery_shell_damage` to the `TREES` dict with:
- `tech_name = 'Artillery shell damage (research)'`
- `cumulative_costs = _asd_cumulative_costs()`
- `caption = 'Shells required to destroy enemy'`
- `max_level = 20`
- `force_rows = list(range(10)) + [('10-19', 10, 19), 20]` (custom row structure overriding automatic breakpoints)
- Three target columns: behemoth worm, spawner (merged biter+spitter), egg raft

### 6. Custom row output

The `print_wiki_table` function needs to support `force_rows` - a list of either integers (individual levels) or `(label, lo, hi)` tuples (combined ranges with cost shown as "cost(lo) - cost(hi)").

## Output

The script generates MediaWiki markup that is placed in a new `ArtilleryShellDamageResearch.txt` file and inserted into the Artillery Shell Damage research wiki page as a `== Thresholds ==` section after the existing tech cost table.

## Intro Text

```
The table below shows for each level of the artillery shell damage research how many (normal quality)
[[artillery shell]]s a [[artillery turret]] or [[artillery wagon]] requires to destroy a
[[Behemoth worm]], a [[Biter spawner]] or [[Spitter spawner]], or an [[egg raft]]{{SA}}.
HP values for spawners and egg rafts are at maximum evolution.
Small, medium, and big worms and small egg rafts are always destroyed in one hit regardless of
research level and are not shown.
```
