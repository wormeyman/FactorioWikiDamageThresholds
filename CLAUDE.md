# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a content repository for contributions to the [Factorio Wiki](https://wiki.factorio.com/). It contains:

- **`StrongerExplosivesResearch.txt`** - MediaWiki markup source for the "Stronger explosives (research)" wiki page
- **`FactorioAsteroidDamageCalculator.xlsx`** - Excel export of a Google Sheet used to calculate asteroid damage thresholds. The Google Sheet is the source of truth; the .xlsx export is unreliable. The `Calculator` tab has a `Research Level Required` summary table (columns G-O, rows 15-38).
- **`factorio_thresholds.py`** - Source of truth for damage threshold calculations. Covers Stronger Explosives (asteroids, biters, spawners), Physical Projectile (gun turret vs Small/Medium asteroids), and Laser Weapons (laser turret vs Small/Medium asteroids). Run with `python3 factorio_thresholds.py [tree] [--wiki]`.
- **`enemies_wiki.json`** - Factorio wiki API response for the Enemies page. Extract wikitext via `data['parse']['wikitext']['*']`. Contains HP and resistance data for biters, spawners, and worms.

## MediaWiki Markup Conventions

The `.txt` file uses MediaWiki template syntax specific to the Factorio Wiki:

- `{{Icon|ItemName}}` - renders an in-game item icon
- `{{Icontech|TechName|level}}` - renders a technology icon at a specific level
- `{{Key|expression}}` - renders a keyboard-key styled formula
- `{| class="wikitable" ... |}` - standard MediaWiki table syntax
- `{{#expr: ceil(...)}}` - MediaWiki parser function for inline math (calculates values at render time)
- `rowspan="N"` / `colspan="N"` - used extensively in the damage threshold tables to merge cells across multiple research levels
- `{{SA}}` - marks Space Age DLC-specific content
- `{{Languages}}` and `{{TechNav}}` - wiki-wide navigation templates

## Damage Threshold Formula

The rockets-required calculation in the Thresholds table follows:

```
rockets_required = ceil( overkill_health / (damage * (1 + bonus)) / resistance_factor )
overkill_health  = asteroid_health * 1.01   (1% overkill from rocket turret behavior)
resistance_factor = 1 - asteroid_resistance
```

Asteroid parameters used in the table:
- Small (S): health 100/202, resistance 0.5
- Medium (M): health 400/808, resistance 0.7
- Big (B): health 2000/4040, resistance 0.9
- Promethium values are 2x the standard asteroid health values

Rocket base damage: 200 (rocket), 150 (explosive rocket direct hit), 100 (explosive rocket AoE)

## Laser Weapons Damage Tree

Laser turret base damage: 20. Damage type: laser. No overkill factor (rocket turrets only).

Cumulative damage multiplier (`lw_mult`):
- Levels 1-6: 1.20, 1.40, 1.70, 2.10, 2.60, 3.30
- Level 7+: 3.30 + 0.70 × (level - 6)

Asteroid laser resistances (from Asteroids.json):
- Small: 20% (practical target)
- Medium: 90% (never one-shot at any level; requires many activations)
- Big: 95%, Huge: 99% (not practical targets - excluded from table)

Community rule: research level 12 with 20+ laser turrets is viable for routes with small and medium asteroids at normal platform travel speeds. Level 11 is the minimum to one-shot small asteroids. The table is capped at level 20; medium asteroids continue to decrease beyond that but never reach 1 activation.

## General Damage Formula (biters, spawners)

Rocket turrets apply a 1% overkill factor against asteroids (overkill = 1.01). Gun turrets do not (overkill = 1.0) - confirmed by in-game testing. Biters and spawners use overkill = 1.0.

For targets with flat+percentage resistances:

```
dmg_eff = max(dmg_raw - flat, 1) * (1 - pct)
shots   = ceil(hp / dmg_eff)
```

Resistances are (flat, pct) tuples in `factorio_thresholds.py`. Behemoth Biter: hp 3000, explosion (12, 0.10), physical (12, 0.10). Spawners: hp 350, explosion (5, 0.0), physical (2, 0.15).

## Verification

```bash
python3 factorio_thresholds.py stronger_explosives
# Small/Rocket: level 0-2 = 2, level 3+ = 1
# Big/Exp AoE: level 45 = 2, level 46 = 1
# Big Prom/Exp AoE: level 90 = 2, level 91 = 1
```

## Known Sheet vs Wiki Discrepancies

The `Research Level Required` table in the Google Sheet was computed using `effective_damage >= HP` (no overkill). The wiki applies a 1% rocket turret overkill factor (`effective_damage >= HP * 1.01`). This causes mismatches at exact-boundary levels. The following 8 cells need to be corrected in the Google Sheet:

| Cell | Description | Sheet | Wiki |
|------|-------------|-------|------|
| L17 | Small / One-Shot / Rocket | 0 | 3 |
| N16 | Small / Two-Shot / Explosive AoE | 0 | 3 |
| L28 | Small Promethium / Two-Shot / Rocket | 0 | 3 |
| N23 | Big / One-Shot / Explosive AoE | 45 | 46 |
| N34 | Big Promethium / Two-Shot / Explosive AoE | 45 | 46 |
| L35 | Big Promethium / One-Shot / Rocket | 45 | 46 |
| M35 | Big Promethium / One-Shot / Explosive Impact | 60 | 61 |
| N35 | Big Promethium / One-Shot / Explosive AoE | 90 | 91 |
