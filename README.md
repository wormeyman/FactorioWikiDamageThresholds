# Factorio Wiki Damage Thresholds

Scripts and MediaWiki markup for Factorio Wiki contributions covering damage thresholds and productivity research.

## Scripts

### `factorio_thresholds.py` - Damage threshold tables

Calculates shots/activations required to destroy targets at each research level.

```bash
# Text output (all trees)
python3 factorio_thresholds.py

# Text output (single tree)
python3 factorio_thresholds.py stronger_explosives
python3 factorio_thresholds.py laser_weapons
python3 factorio_thresholds.py physical_projectile
python3 factorio_thresholds.py artillery_shell_damage

# Regenerate wiki articles
python3 factorio_thresholds.py stronger_explosives --wiki > WikiArticles/StrongerExplosivesResearch.txt
python3 factorio_thresholds.py artillery_shell_damage --wiki > WikiArticles/ArtilleryShellDamageResearch.txt
```

### `factorio_productivity.py` - Productivity threshold tables

Shows total productivity bonus at key research levels for each machine and module configuration.

```bash
# Text output (all researches)
python3 factorio_productivity.py

# Text output (single research)
python3 factorio_productivity.py steel_plate
python3 factorio_productivity.py processing_unit
python3 factorio_productivity.py low_density_structure
python3 factorio_productivity.py plastic_bar

# Regenerate wiki articles
python3 factorio_productivity.py steel_plate --wiki > WikiArticles/SteelPlateProductivityResearch.txt
python3 factorio_productivity.py processing_unit --wiki > WikiArticles/ProcessingUnitProductivityResearch.txt
python3 factorio_productivity.py low_density_structure --wiki > WikiArticles/LowDensityStructureProductivityResearch.txt
python3 factorio_productivity.py plastic_bar --wiki > WikiArticles/PlasticBarProductivityResearch.txt
```

## Wiki Articles

| File | Wiki page |
|------|-----------|
| `WikiArticles/StrongerExplosivesResearch.txt` | Stronger explosives (research) |
| `WikiArticles/ArtilleryShellDamageResearch.txt` | Artillery shell damage (research) |
| `WikiArticles/SteelPlateProductivityResearch.txt` | Steel plate productivity (research) - Thresholds section |
| `WikiArticles/ProcessingUnitProductivityResearch.txt` | Processing unit productivity (research) - Thresholds section |
| `WikiArticles/LowDensityStructureProductivityResearch.txt` | Low density structure productivity (research) - Thresholds section |
| `WikiArticles/PlasticBarProductivityResearch.txt` | Plastic bar productivity (research) - Thresholds section |

## Reference Data

| File | Contents |
|------|----------|
| `WikiArticles/Technologies.json` | Factorio wiki API - infinite research data, cost formulas, breakpoints |
| `WikiArticles/enemies_wiki.json` | Factorio wiki API - HP and resistance data for biters, spawners, worms |
| `FactorioAsteroidDamageCalculator.xlsx` | Excel export of Google Sheet (sheet is source of truth) |
