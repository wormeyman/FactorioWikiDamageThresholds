# Design: Refined Flammables Research Tree

**Date:** 2026-04-21
**Topic:** New `refined_flammables` tree in `factorio_thresholds.py`

## Problem

The Refined flammables (research) wiki page needs a threshold table for the Flamethrower turret. Unlike all existing trees (rockets, lasers, bullets, Tesla), the flamethrower is a continuous stream weapon - there are no discrete "shots." The player-facing metric that makes practical sense is **fluid units consumed to destroy an enemy**, since that tells players how much oil to store in their tank.

## Scope

- Targets: Behemoth Biter (3000 HP) and Behemoth Spitter (1500 HP) on Nauvis
- Ammo columns: Crude oil (1.0x damage modifier) and Light oil (1.1x)
- Research levels: 0-20 (infinite research; capped at 20 to match laser/EWD trees)
- Output file: `WikiArticles/RefinedFlammablesResearch.txt`

## Data (verified from data/factorioraw.json)

### Flamethrower turret

- Stream entity: `flamethrower-fire-stream`
- Base fire damage: **3 per pulse**, area radius 2.5 tiles
- Attack cooldown: **4 ticks** (15 pulses/sec at 60 ticks/sec)
- Fluid consumption: **0.2 units/tick** = **0.8 units per pulse** (fluid type does not affect consumption rate)
- Fluid damage modifiers: crude oil 1.0x (no field = default), light oil 1.1x, heavy oil 1.05x

### Research effects per level (both apply independently)

| Levels | `ammo-damage` modifier | `turret-attack` modifier |
|--------|----------------------|------------------------|
| 1-3 | +0.2 | +0.2 |
| 4-5 | +0.3 | +0.3 |
| 6 | +0.4 | +0.4 |
| 7+ (infinite) | +0.2 | +0.2 |

Cumulative single-factor bonus: `{0:0.0, 1:0.2, 2:0.4, 3:0.6, 4:0.9, 5:1.2, 6:1.6}`, then 1.6 + 0.2*(level-6) for level 7+.

Both modifiers apply independently and multiply (same pattern as Physical Projectile research):
`rf_mult(level) = (1 + cumulative_bonus)²`

### Targets

Neither target has fire resistance:
- Behemoth Biter: 3000 HP, `{'explosion': (12, 0.10), 'physical': (12, 0.10)}`
- Behemoth Spitter: 1500 HP, `{'explosion': (0, 0.30)}`

### Research costs

| Level | Count | Pack types |
|-------|-------|-----------|
| 1 | 100 | Auto, Log, Mil |
| 2 | 200 | Auto, Log, Mil |
| 3 | 300 | Auto, Log, Mil, Chem |
| 4 | 400 | Auto, Log, Mil, Chem |
| 5 | 500 | Auto, Log, Mil, Chem, Util |
| 6 | 600 | Auto, Log, Mil, Chem, Util, Space |
| 7+ | 2^(L-7)×1000 | + Agri (7 types total) |

## Formula

```
pulses_to_kill = ceil( hp / (base_dmg_per_pulse × rf_mult(level)) )
fluid_to_kill  = ceil( pulses_to_kill × 0.8 )
```

- `base_dmg_per_pulse` = 3.0 (crude oil) or 3.3 (light oil)
- `overkill = 1.0` (no overkill factor - rocket turret only)
- Two-step ceiling is intentional: `ceil(ceil(hp/dmg) × 0.8) ≠ ceil(hp × 0.8 / dmg)` in edge cases (collapsing introduces off-by-one errors)

## Architecture

### New: `units_per_shot` field on tree dict

The existing `shots_needed()` function is reused unchanged. A new optional field `units_per_shot: 0.8` on the tree dict signals the renderer to apply `ceil(shots × units_per_shot)` instead of using the raw shot count. This is the only change to shared rendering logic.

### New functions

- `rf_single(level)` - single-factor cumulative multiplier (1 + bonus)
- `rf_mult(level)` - total multiplier = rf_single²
- `_rf_cumulative_costs(max_lvl=20)` - cumulative pack cost dict

### New tree entry

Key fields:
```python
'units_per_shot': 0.8,
'caption': 'Fluid units required to destroy enemy',
'max_level': 20,
'weapons': [
    ('Crude oil', 3.0, 'fire', '{{Icon|Crude oil}}', 'Crude oil', 1),
    ('Light oil', 3.3, 'fire', '{{Icon|Light oil}}', 'Light oil', 1),
],
```

## Sample values

| Level | Crude / Biter | Light / Biter | Crude / Spitter | Light / Spitter |
|-------|-------------|--------------|----------------|----------------|
| 0 | 800 | 728 | 400 | 364 |
| 3 | 313 | 285 | 157 | 143 |
| 6 | 119 | 109 | 60 | 55 |
| 10 | 70 | 64 | 35 | 32 |
| 20 | 28 | 26 | 14 | 13 |

## Verification

```bash
python3 factorio_thresholds.py refined_flammables
# Level 0 / Crude oil / Behemoth Biter:   800
# Level 0 / Light oil / Behemoth Biter:   728
# Level 0 / Crude oil / Behemoth Spitter: 400
# Level 6 / Crude oil / Behemoth Biter:   119
# Level 6 / Light oil / Behemoth Biter:   109
# Level 20 / Crude oil / Behemoth Biter:  28

python3 factorio_thresholds.py refined_flammables --wiki > WikiArticles/RefinedFlammablesResearch.txt
```
