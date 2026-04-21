# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Maintenance Rules

- When a PR is merged that adds a new research to `factorio_productivity.py` or a new tree to `factorio_thresholds.py`, update `README.md` to include the new text and `--wiki` commands.

## Preferred Workflow

When completing a development branch, always push and create a Pull Request (do not merge locally).

## Repository Overview

This is a content repository for contributions to the [Factorio Wiki](https://wiki.factorio.com/). It contains:

- **`WikiArticles/StrongerExplosivesResearch.txt`** - MediaWiki markup source for the "Stronger explosives (research)" wiki page
- **`WikiArticles/ArtilleryShellDamageResearch.txt`** - MediaWiki markup source for the "Artillery shell damage (research)" wiki page
- **`FactorioAsteroidDamageCalculator.xlsx`** - Excel export of a Google Sheet used to calculate asteroid damage thresholds. The Google Sheet is the source of truth; the .xlsx export is unreliable. The `Calculator` tab has a `Research Level Required` summary table (columns G-O, rows 15-38).
- **`factorio_thresholds.py`** - Source of truth for damage threshold calculations. Covers Stronger Explosives (asteroids, biters, spawners), Physical Projectile (gun turret vs Small/Medium asteroids), Laser Weapons (laser turret vs Small/Medium asteroids), Artillery Shell Damage (enemies), and Electric Weapons Damage (Tesla turret vs enemies). Run with `python3 factorio_thresholds.py [tree] [--wiki]`.
- **`factorio_productivity.py`** - Source of truth for productivity threshold calculations. Covers Steel Plate Productivity (foundry and electric furnace), Processing Unit Productivity (assembling machine 3 and electromagnetic plant), Low Density Structure Productivity (assembling machine 3 and foundry), and Plastic Bar Productivity (chemical plant, biochamber, and cryogenic plant), various module configs. Run with `python3 factorio_productivity.py [research] [--wiki]`.
- **`factorio_mining.py`** - Source of truth for mining productivity threshold calculations. Shows how many mining drills are needed to fully saturate each belt type (Transport, Fast transport, Express transport, Turbo transport) at each research level. Supports Electric mining drill and Big mining drill, with and without quad belt stacking (Gleba research). Run with `python3 factorio_mining.py [--wiki]`.
- **`factorio_wiki_fetch.py`** - Downloads a Factorio Wiki page via the MediaWiki API and saves the JSON response to `WikiArticles/` for offline use. Accepts a full wiki URL or bare page name. Run with `python3 factorio_wiki_fetch.py <url-or-page-name> [--output FILENAME]`.
- **`WikiArticles/MiningProductivityResearch.txt`** - MediaWiki markup source for the "Mining productivity (research)" wiki page thresholds section.
- **`WikiArticles/SteelPlateProductivityResearch.txt`** - MediaWiki markup source for the "Steel plate productivity (research)" wiki page thresholds section.
- **`WikiArticles/ProcessingUnitProductivityResearch.txt`** - MediaWiki markup source for the "Processing unit productivity (research)" wiki page thresholds section.
- **`WikiArticles/LowDensityStructureProductivityResearch.txt`** - MediaWiki markup source for the "Low density structure productivity (research)" wiki page thresholds section.
- **`WikiArticles/PlasticBarProductivityResearch.txt`** - MediaWiki markup source for the "Plastic bar productivity (research)" wiki page thresholds section.
- **`WikiArticles/ElectricWeaponsDamageResearch.txt`** - MediaWiki markup source for the "Electric weapons damage (research)" wiki page thresholds section.
- **`WikiArticles/RefinedFlammablesResearch.txt`** - MediaWiki markup source for the "Refined flammables (research)" wiki page thresholds section.
- **`WikiArticles/enemies_wiki.json`** - Factorio wiki API response for the Enemies page. Extract wikitext via `data['parse']['wikitext']['*']`. Contains HP and resistance data for biters, spawners, and worms.
- **`WikiArticles/Technologies.json`** - Factorio wiki API response for the Technologies page. Contains infinite research data, pricing formulas, and interesting breakpoints.

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

## Electric Weapons Damage Tree

Tesla turret base damage: 120 electric per bolt. Damage type: electric. No overkill factor.

Source: `data/factorioraw.json` → `beam["chain-tesla-turret-beam-bounce"].action.action_delivery.target_effects[1].damage.amount = 120`. Both the start beam and bounce beam deal 120 each.

Chain mechanics (from `chain-active-trigger["chain-tesla-turret-chain"]`):
- `max_jumps = 10`, `max_range_per_jump = 12` tiles, `jump_delay_ticks = 6`
- `fork_chance = 0.05` (5% per jump at regular quality), `fork_chance_increase_per_quality_level = 0.05`

Cumulative damage multiplier (`ewd_mult`):
- Levels 0-2: 1.0 (those levels only buff Destroyers, not Tesla)
- Level 3+: 1.0 + 0.70 × (level - 2)

Research cost per level:
- Level 1: Auto+Log+Mil+Chem+Util × 250 (5 types)
- Level 2: +Space × 500 (6 types)
- Level 3+: +EM × 1000 × 2^(level-3) (7 types)

Segmented enemy mechanics - Tesla bolt bounces between segments sharing a single HP pool. Both Big Strafer and Big Stomper are `spider-unit` type (NOT `segmented_unit` - that is only for demolishers). Both have 5 legs each (`big-stomper-pentapod-leg` / `big-strafer-pentapod-leg`). Number of reliable hits per activation depends on how many legs are within 12-tile bounce range:

| Enemy | HP | `hits_per_activation` | Wiki icon | Reason | Confirmed |
|---|---|---|---|---|---|
| Big Strafer | 2400 | 3 | `{{Icon|Strafer_big}}` | Attacks from range ~31 tiles; only 3 of 5 legs in bounce range | Level 10: always 2 shots, sometimes 1 |
| Big Stomper | 15000 | 4 | `{{Icon|Stomper_big}}` | Closes to melee; all 5 legs in range but hit count varies 3-5; 4 is the conservative average | Level 6: 7 shots (4/4 tests, matches 5 hits); Lua counter shows 50% = 5 hits, 37% = 3 hits, 13% = 4 hits |

Big Stomper has `healing_per_tick = 0.5` (30 HP/s). This introduces ~1 shot of variability at higher research levels. Table uses 4 hits/activation as a conservative average; wiki note warns of ±2 variability.

Big Demolisher excluded: 300,000 HP, 24,000 HP/s regen, Electric 20/20% resistance, complex head/body segmentation. Table capped at level 20 (Big Stomper reaches 1-shot around level 37).

Tree definition supports two optional output fields:
- `intro`: heading + disclaimer/paragraph emitted before the wiki table (same pattern as `factorio_productivity.py`). Avoid `{{Icon|...}}` in prose - use plain wikilinks instead (renders as block-level div, breaks paragraph).
- `note`: italic footnote emitted after the closing `|}`.

In-game testing techniques:

Make a selected entity indestructible before testing (prevents turret from being destroyed mid-test):
```lua
/c game.player.selected.destructible = false
```

Count hits per Tesla activation (groups events within 70 ticks as one activation; chain takes max 60 ticks, cooldown is 120 ticks):
```lua
/c local state = {}
script.on_event(defines.events.on_entity_damaged, function(e)
  local name = e.entity.name
  -- add target entity names to check here
  if name ~= "big-stomper-pentapod" and name ~= "big-strafer-pentapod" then return end
  local t = game.tick
  local s = state[name]
  if not s then s = {hits=0, dmg=0, last_tick=-999, n=0}; state[name] = s end
  if t - s.last_tick > 70 then
    if s.hits > 0 then
      s.n = s.n + 1
      game.print(name.." shot "..s.n..": "..s.hits.." hits, total dmg="..s.dmg)
    end
    s.hits = 0; s.dmg = 0
  end
  s.hits = s.hits + 1
  s.dmg = s.dmg + e.final_damage_amount
  s.last_tick = t
end)
```

Clear the event handler when done: `/c script.on_event(defines.events.on_entity_damaged, nil)`

Choose a diagnostic research level where predicted shot counts differ clearly between hypotheses (level 6 worked well for Big Stomper: 7/9/11 shots for 5/4/3 hits/activation).

## General Damage Formula (biters, spawners)

Rocket turrets apply a 1% overkill factor against asteroids (overkill = 1.01). Gun turrets do not (overkill = 1.0) - confirmed by in-game testing. Biters and spawners use overkill = 1.0.

For targets with flat+percentage resistances:

```
dmg_eff = max(dmg_raw - flat, 1) * (1 - pct)
shots   = ceil(hp / dmg_eff)
```

Resistances are (flat, pct) tuples in `factorio_thresholds.py`. Behemoth Biter: hp 3000, explosion (12, 0.10), physical (12, 0.10). Spawners: hp 350, explosion (5, 0.0), physical (2, 0.15).

## Productivity Formula

Total productivity bonus at a given research level:

```
total_prod = base_prod + slots * module_bonus + level * bonus_per_level
```

Capped at 300% (3.00). Minimum level to reach cap:

```
min_level = ceil( (cap - base_prod - slots * module_bonus) / bonus_per_level )
```

Cumulative research costs use the shared `_cumulative_costs(cost_base, max_lvl, multiplier=1.5)` helper. Cost per level N: `round(cost_base × multiplier^N)` packs.

Steel Plate Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(1000, 30)` - packs: Automation + Logistic + Chemical + Production

Processing Unit Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(1000, 30)` - packs: Automation + Logistic + Chemical + Production + Electromagnetic

Low Density Structure Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(1000, 30)` - packs: Automation + Logistic + Chemical + Production + Metallurgic

Plastic Bar Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(1000, 30)` - packs: Automation + Logistic + Chemical + Production + Agricultural
- Machines: Chemical plant, Biochamber, Cryogenic plant (column order)
- Applies to [[Plastic bar]] recipe (all 3 machines) and [[Plastic bar#Alternative recipes|Bioplastic]] recipe (Biochamber only)

Rocket Fuel Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(1000, 30)` - packs: Automation + Logistic + Chemical + Production + Agricultural
- Machines: Assembling machine 3, Biochamber, Cryogenic plant (column order)
- Applies to [[Rocket fuel]] recipe (AM3), [[Rocket fuel#Alternative recipes|Rocket fuel from jelly]] recipe (Biochamber only), and [[Rocket fuel#Alternative recipes|Ammonia rocket fuel]] recipe (Cryogenic plant only)

Rocket Part Productivity parameters:
- `bonus_per_level`: 10% per level, max level 30
- `cap`: 300%
- Cost: `_cumulative_costs(2000, 30)` - packs: Automation + Logistic + Chemical + Production + Cryogenic
- Machines: Rocket silo (column order)
- Applies to [[Rocket part]] recipe (Rocket silo)

Machines and base productivity:
- Foundry: 50% base, 4 module slots
- Electric furnace: 0% base, 2 module slots
- Assembling machine 3: 0% base, 4 module slots
- Electromagnetic plant: 50% base, 5 module slots
- Chemical plant: 0% base, 3 module slots
- Biochamber: 50% base, 4 module slots
- Cryogenic plant: 0% base, 8 module slots
- Rocket silo: 0% base, 4 module slots

Module bonuses per slot:
- No modules: 0%
- Productivity module 3: 10%
- Legendary Productivity module 2: 15%
- Legendary Productivity module 3: 25%

Known breakpoints (verified against wiki):
- Level 10: Electric furnace + no modules reaches 100% productivity (notable level, manually added)
- Level 15: Foundry + 4x Legendary Prod 3 reaches 300% cap
- Level 20: Notable milestone (manually added)
- Level 25: Foundry + no modules reaches 300% cap; Electric furnace + 2x Legendary Prod 3 reaches 300% cap

Research dict supports two optional fields:
- `notable_levels`: list of manually pinned row levels beyond the auto-detected cap breakpoints
- `intro`: section header + paragraph emitted before the wiki table (so regenerating the file is fully automated)

Wiki icon format for legendary modules: `{{Icon|productivity_module_3|[[File:quality_legendary.png|Legendary|16px]]}}`. Sub-header cells include slot count prefix (e.g. `4× {{Icon|...}}`) generated dynamically from `MACHINES[name]['module_slots']`.

**Intro text rule:** Never use `{{icon|...}}` or `{{Icon|...}}` inline in prose sentences in the `intro` field. The Factorio Wiki renders these as block-level `<div>` elements, which breaks the paragraph into fragments. Use plain wikilinks (`[[Item name]]`) instead. Icons are fine in table headers and cells - only avoid them in the intro paragraph text.

## Verification

```bash
python3 factorio_thresholds.py stronger_explosives
# Small/Rocket: level 0-2 = 2, level 3+ = 1
# Big/Exp AoE: level 45 = 2, level 46 = 1
# Big Prom/Exp AoE: level 90 = 2, level 91 = 1

python3 factorio_productivity.py steel_plate
# Breakpoints: [0, 10, 15, 19, 20, 21, 25, 27, 28, 30]
# Level 10 / EFurn+none: 100%
# Level 15 / Foundry+LP3: 300% (first cap)
# Level 30 / EFurn+none: 300% (last cap)

python3 factorio_productivity.py steel_plate --wiki > WikiArticles/SteelPlateProductivityResearch.txt

python3 factorio_productivity.py processing_unit
# Breakpoints: [0, 10, 13, 18, 20, 24, 25, 26, 30]
# Level 10 / AM3+none: 100%
# Level 13 / EM plant+LP3: 300% (first cap)
# Level 30 / AM3+none: 300% (last cap)

python3 factorio_productivity.py processing_unit --wiki > WikiArticles/ProcessingUnitProductivityResearch.txt

python3 factorio_productivity.py low_density_structure
# Breakpoints: [0, 10, 15, 19, 20, 21, 24, 25, 26, 30]
# Level 10 / AM3+none: 100%
# Level 15 / Foundry+LP3: 300% (first cap)
# Level 30 / AM3+none: 300% (last cap)

python3 factorio_productivity.py low_density_structure --wiki > WikiArticles/LowDensityStructureProductivityResearch.txt

python3 factorio_productivity.py plastic_bar
# Breakpoints: [0, 10, 15, 18, 19, 20, 21, 22, 23, 25, 26, 27, 30]
# Level 10 / Cryogenic+LP3: 300% (first cap)
# Level 15 / Biochamber+LP3: 300%
# Level 30 / Chemical+none: 300% (last cap)

python3 factorio_productivity.py plastic_bar --wiki > WikiArticles/PlasticBarProductivityResearch.txt

python3 factorio_productivity.py rocket_fuel
# Breakpoints: [0, 10, 15, 18, 19, 20, 21, 22, 24, 25, 26, 30]
# Level 10 / Cryogenic+LP3: 300% (first cap)
# Level 20 / AM3+LP3: 300%
# Level 25 / Biochamber+none: 300%
# Level 30 / AM3+none: 300% (last cap)

python3 factorio_productivity.py rocket_fuel --wiki > WikiArticles/RocketFuelProductivityResearch.txt

python3 factorio_productivity.py rocket_part
# Breakpoints: [0, 10, 20, 24, 26, 30]
# Level 20 / Rocket silo+LP3: 300% (first cap)
# Level 30 / Rocket silo+none: 300% (last cap)

python3 factorio_productivity.py rocket_part --wiki > WikiArticles/RocketPartProductivityResearch.txt

python3 factorio_mining.py
# Level 0, Yellow belt, EMD: 30 drills
# Level 110, Turbo belt, BMD: 2 drills
# Level 110, Yellow belt, BMD+stacking: 2 drills

python3 factorio_mining.py --wiki > WikiArticles/MiningProductivityResearch.txt

python3 factorio_thresholds.py electric_weapons_damage
# Level 0-2: Behemoth Spitter = 13 shots (1500/120 = 12.5 → 13)
# Level 3: Behemoth Spitter = 8 shots (1500/204 = 7.35 → 8)
# Level 19: Behemoth Spitter = 1 shot
# Level 20: Big Stomper = 10 shots (15000/1632 = 9.19 → 10)

python3 factorio_thresholds.py electric_weapons_damage --wiki > WikiArticles/ElectricWeaponsDamageResearch.txt

python3 factorio_thresholds.py refined_flammables
# Level 0 / Crude oil / Behemoth Biter:   800
# Level 0 / Light oil / Behemoth Biter:   728
# Level 6 / Crude oil / Behemoth Biter:   119
# Level 20 / Crude oil / Behemoth Biter:  28

python3 factorio_thresholds.py refined_flammables --wiki > WikiArticles/RefinedFlammablesResearch.txt
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
