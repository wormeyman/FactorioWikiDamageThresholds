# Artillery Shell Damage Thresholds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Thresholds section to the Artillery Shell Damage research wiki page showing shells required to destroy a Behemoth worm, max-evolution spawner, and max-evolution egg raft at each research level.

**Architecture:** All code changes are in `factorio_thresholds.py`. Three additions: (1) `asd_mult` and `_asd_cumulative_costs` for the research formula and costs, (2) `extra_resists` on column dicts so a single shell can sum physical + explosion damage, (3) a `force_rows` mechanism in `print_wiki_table` to emit exact rows (levels 0-9 individually, 10-19 merged with cost range, level 20) instead of auto-detected breakpoints. Generated wiki markup is saved to `ArtilleryShellDamageResearch.txt`.

**Tech Stack:** Python 3, `factorio_thresholds.py` framework, MediaWiki template syntax.

---

## File Structure

- Modify: `factorio_thresholds.py` - all new functions, target data, tree definition
- Create: `ArtilleryShellDamageResearch.txt` - generated wiki markup (paste into wiki page)

---

### Task 1: Add `asd_mult` and `_asd_cumulative_costs`

**Files:**
- Modify: `factorio_thresholds.py` - insert after `_pp_cumulative_costs` (around line 224)

- [ ] **Step 1: Add the two functions after `_pp_cumulative_costs`**

```python
def asd_mult(level: int) -> float:
    """Artillery Shell Damage cumulative multiplier.

    Simple linear 10% per level — no lookup table.
    Level 0: 1.0. Level n: 1.0 + 0.10 * n.
    """
    return 1.0 + 0.10 * level


def _asd_cumulative_costs(max_lvl: int = 30) -> dict:
    """Cumulative total science pack cost to REACH each artillery shell damage level.

    7 pack types (Auto/Log/Mil/Chem/Util/Space/Metallurgic), each requiring
    2^(L-1)*1000 units per level. Total per level = 7 * 2^(L-1) * 1000.
    """
    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += 7 * (2 ** (lvl - 1)) * 1000
        result[lvl] = _si(total)
    return result
```

- [ ] **Step 2: Verify**

```bash
python3 -c "
from factorio_thresholds import asd_mult, _asd_cumulative_costs
assert asd_mult(0) == 1.0,  f'got {asd_mult(0)}'
assert asd_mult(9) == 1.9,  f'got {asd_mult(9)}'
assert asd_mult(20) == 3.0, f'got {asd_mult(20)}'
c = _asd_cumulative_costs()
assert c[0]  == '-',      f'got {c[0]}'
assert c[1]  == '7k',     f'got {c[1]}'
assert c[8]  == '1.785M', f'got {c[8]}'
assert c[9]  == '3.577M', f'got {c[9]}'
assert c[10] == '7.161M', f'got {c[10]}'
assert c[19] == '3.67G',  f'got {c[19]}'
assert c[20] == '7.34G',  f'got {c[20]}'
print('PASS')
"
```

Expected: `PASS`

- [ ] **Step 3: Commit**

```bash
git add factorio_thresholds.py
git commit -m "feat: add asd_mult and _asd_cumulative_costs for artillery shell damage research"
```

---

### Task 2: Add dual-damage support to `build_columns` and `_col_shots`

Artillery shells deal 1000 physical + 1000 explosion per shot. Both are scaled by the research multiplier and both components are summed before computing shot count. The weapon tuple gains an optional 7th element — a list of `(base_dmg, dmg_type)` extra components.

**Files:**
- Modify: `factorio_thresholds.py` - `build_columns` (around line 296) and `_col_shots` (around line 326)

- [ ] **Step 1: Extend `build_columns` to populate `extra_resists` on each column dict**

In `build_columns`, after the line extracting `magazine_size`:

```python
magazine_size  = weapon[5] if len(weapon) > 5 else 1
```

Add:

```python
extra_dmg      = weapon[6] if len(weapon) > 6 else []
extra_resists  = [
    (base, target['resist'].get(dt, (0, 0.0)))
    for base, dt in extra_dmg
]
```

Then add `'extra_resists': extra_resists` to the `cols.append({...})` dict. The full updated append:

```python
cols.append({
    'group':          group_name,
    'target':         target_name,
    'weapon':         weapon_name,
    'label':          f'{target_name} / {weapon_name}',
    'hp':             target['hp'],
    'overkill':       overkill,
    'base_dmg':       base_dmg,
    'resist':         resist,
    'header_icon':    header_icon,
    'data_icon_name': data_icon_name,
    'magazine_size':  magazine_size,
    'round_per_hit':  tree.get('round_per_hit', False),
    'extra_resists':  extra_resists,
})
```

- [ ] **Step 2: Update `_col_shots` to sum extra damage components when present**

Replace the existing `_col_shots` function:

```python
def _col_shots(col: dict, mult: float) -> int:
    """Raw shots needed to kill the target.

    If col['extra_resists'] is non-empty, sums all damage components per shot
    (e.g. artillery shell: 1000 physical + 1000 explosion). Otherwise falls
    through to shots_needed, preserving round_per_hit behaviour for gun turrets.
    """
    if col['extra_resists']:
        flat, pct = col['resist']
        total_dmg = max(col['base_dmg'] * mult - flat, 1.0) * (1.0 - pct)
        for base2, (flat2, pct2) in col['extra_resists']:
            total_dmg += max(base2 * mult - flat2, 1.0) * (1.0 - pct2)
        return math.ceil(col['hp'] * col['overkill'] / total_dmg - 1e-9)
    return shots_needed(col['hp'], col['overkill'], col['base_dmg'], mult,
                        col['resist'], col.get('round_per_hit', False))
```

- [ ] **Step 3: Verify existing trees are unaffected**

```bash
python3 factorio_thresholds.py stronger_explosives 2>&1 | head -5
python3 factorio_thresholds.py physical_projectile 2>&1 | head -5
python3 factorio_thresholds.py laser_weapons 2>&1 | head -5
```

Expected: all three print a `===` header line followed by column headers with no errors.

- [ ] **Step 4: Verify dual-damage math directly**

```bash
python3 -c "
import math, factorio_thresholds as ft

# Behemoth worm: HP 3000, physical (10,0%), explosion (10,30%)
# At level 0 (mult=1.0): dmg_p=990, dmg_e=693, total=1683 -> 2 shells
# At level 8 (mult=1.8): dmg_p=1790, dmg_e=1253, total=3043 -> 1 shell
col = {
    'hp': 3000, 'overkill': 1.0, 'base_dmg': 1000,
    'resist': (10, 0.0),
    'extra_resists': [(1000, (10, 0.30))],
    'round_per_hit': False,
}
assert ft._col_shots(col, 1.0) == 2, f'level 0: {ft._col_shots(col, 1.0)}'
assert ft._col_shots(col, 1.8) == 1, f'level 8: {ft._col_shots(col, 1.8)}'

# Max-evo spawner: HP 3500, physical (2,15%), explosion (5,0%)
# At level 0: dmg_p=848.3, dmg_e=995, total=1843.3 -> 2 shells
# At level 9 (mult=1.9): dmg_p=1683.3+...; computed below
col2 = {
    'hp': 3500, 'overkill': 1.0, 'base_dmg': 1000,
    'resist': (2, 0.15),
    'extra_resists': [(1000, (5, 0.0))],
    'round_per_hit': False,
}
assert ft._col_shots(col2, 1.0) == 2, f'spawner level 0: {ft._col_shots(col2, 1.0)}'
assert ft._col_shots(col2, 1.8) == 2, f'spawner level 8: {ft._col_shots(col2, 1.8)}'
assert ft._col_shots(col2, 1.9) == 1, f'spawner level 9: {ft._col_shots(col2, 1.9)}'
print('PASS')
"
```

Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add factorio_thresholds.py
git commit -m "feat: add extra_resists dual-damage support to build_columns and _col_shots"
```

---

### Task 3: Add `force_rows` support to `print_wiki_table`

When a tree sets `force_rows`, the table emits exactly those rows instead of auto-detected breakpoints. Each element is either an `int` (individual level) or a `(lo, hi)` tuple (merged range; cost cell shows "cost(lo) - cost(hi)").

**Files:**
- Modify: `factorio_thresholds.py` - add `_emit_force_rows` before `print_wiki_table` (around line 404), and call it from within `print_wiki_table`

- [ ] **Step 1: Add `_emit_force_rows` before `print_wiki_table`**

```python
def _emit_force_rows(cols: list, force_rows: list, mult_fn,
                     cumulative_costs: dict, tech_name: str) -> None:
    """Emit data rows for a table whose row structure is explicitly specified.

    force_rows elements:
      int n       — one row for level n; last element gets a '+' suffix on the level cell
      (lo, hi)    — one merged row for levels lo-hi; values computed at lo;
                    cost cell shows 'cost(lo) - cost(hi)'
    """
    n_cols  = len(cols)
    n_rows  = len(force_rows)

    # Resolve each spec to (compute_level, level_cell_str, cost_str)
    resolved = []
    for i, spec in enumerate(force_rows):
        is_last = (i == n_rows - 1)
        if isinstance(spec, int):
            lvl     = spec
            lvl_str = (f'{{{{Icontech|{tech_name}|{lvl}}}}}+'
                       if is_last else
                       f'{{{{Icontech|{tech_name}|{lvl}}}}}')
            cost_str = cumulative_costs.get(lvl, '?')
        else:
            lo, hi   = spec
            lvl      = lo
            lvl_str  = (f'{{{{Icontech|{tech_name}|{lo}}}}} to'
                        f' {{{{Icontech|{tech_name}|{hi}}}}}')
            cost_str = (f'{cumulative_costs.get(lo, "?")} -'
                        f' {cumulative_costs.get(hi, "?")}')
        resolved.append((lvl, lvl_str, cost_str))

    # Pre-compute display values (magazines/shots) for every (column, row)
    display = [
        [_col_display(cols[ci], mult_fn(lvl)) for lvl, _, _ in resolved]
        for ci in range(n_cols)
    ]

    # Forward-scan to compute per-column rowspans
    # rowspans[ci][ri] = span count if this cell is the start of a new value,
    # or 0 if it is covered by a rowspan from above.
    rowspans = [[0] * n_rows for _ in range(n_cols)]
    for ci in range(n_cols):
        ri = 0
        while ri < n_rows:
            span = 1
            while ri + span < n_rows and display[ci][ri + span] == display[ci][ri]:
                span += 1
            rowspans[ci][ri] = span
            for s in range(1, span):
                rowspans[ci][ri + s] = 0
            ri += span

    # Emit rows
    for ri, (_, lvl_str, cost_str) in enumerate(resolved):
        print('|- style="vertical-align:top;"')
        print(f'! style="vertical-align:middle;" | {lvl_str}')
        print(f'| {cost_str}')
        for ci in range(n_cols):
            rs = rowspans[ci][ri]
            if rs == 0:
                continue
            val = display[ci][ri]
            col = cols[ci]
            cell_content = (f'{{{{Icon|{col["data_icon_name"]}|{val}}}}}'
                            if col['data_icon_name'] else str(val))
            print(f'| rowspan="{rs}" | {cell_content}' if rs > 1
                  else f'| {cell_content}')
```

- [ ] **Step 2: Call `_emit_force_rows` from `print_wiki_table`**

In `print_wiki_table`, find the comment `# Data rows` that begins the data-row section (around line 509). Insert this block immediately before it:

```python
if tree.get('force_rows'):
    _emit_force_rows(cols, tree['force_rows'], mult_fn,
                     cumulative_costs, tech_name)
    print('|}')
    return
```

The existing `# Data rows` block and everything after it within `print_wiki_table` is unchanged and handles all trees that do not set `force_rows`.

- [ ] **Step 3: Smoke-test `force_rows` with a minimal inline tree**

```bash
python3 -c "
import factorio_thresholds as ft

mini = {
    'name': 'Force-rows smoke test',
    'mult_fn': ft.asd_mult,
    'tech_name': 'Artillery shell damage (research)',
    'cumulative_costs': ft._asd_cumulative_costs(),
    'caption': 'Test',
    'max_level': 4,
    'force_rows': [0, 1, (2, 3), 4],
    'weapons': [
        ('Shell', 1000, 'explosion', '{{Icon|Artillery shell}}', 'Artillery shell', 1),
    ],
    'target_groups': [
        ('T', {'Worm': {'hp': 3000, 'resist': {'explosion': (10, 0.30)}}}, 1.0),
    ],
    'target_wiki_labels': {'Worm': '{{Icon|Behemoth_worm}}'},
}
ft.print_wiki_table(mini)
" 2>&1
```

Expected: a valid wikitable that begins with `<!-- Force-rows smoke test`, has a caption row, two header rows (Level+Cost, then target icon), and 4 data rows for levels 0, 1, 2-3, and 4+. No Python errors.

- [ ] **Step 4: Verify existing trees still produce identical output to before**

```bash
python3 factorio_thresholds.py physical_projectile --wiki 2>&1 | md5sum
```

Save the hash. Then re-run after any further edits to confirm no regression.

- [ ] **Step 5: Commit**

```bash
git add factorio_thresholds.py
git commit -m "feat: add force_rows support to print_wiki_table for fixed table row structures"
```

---

### Task 4: Define artillery targets, add tree to TREES, generate output

**Files:**
- Modify: `factorio_thresholds.py` - target dicts (after `SPAWNERS`, line ~44) and `TREES` dict
- Create: `ArtilleryShellDamageResearch.txt`

- [ ] **Step 1: Add target dicts after `SPAWNERS`**

```python
# Worms — HP is fixed (not evolution-dependent).
# Small/medium/big worms are always one-shot by artillery at any research level
# and are included here for reference only; only Behemoth worm is in the tree.
WORMS = {
    'Small worm':    {'hp': 200,  'resist': {}},
    'Medium worm':   {'hp': 500,  'resist': {'explosion': (5, 0.15), 'physical': (5, 0.0)}},
    'Big worm':      {'hp': 1500, 'resist': {'explosion': (10, 0.30), 'physical': (10, 0.0)}},
    'Behemoth worm': {'hp': 3000, 'resist': {'explosion': (10, 0.30), 'physical': (10, 0.0)}},
}

# Max-evolution HP: spawners scale up to 10x base (350 -> 3500).
# Biter and spitter spawners share identical stats; merged as one column.
SPAWNERS_MAX_EVO = {
    'Spawner': {'hp': 3500, 'resist': {'explosion': (5, 0.0), 'physical': (2, 0.15)}},
}

# Max-evolution HP: egg raft scales up to 10x base (500 -> 5000).
EGG_RAFTS_MAX_EVO = {
    'Egg raft': {'hp': 5000, 'resist': {'explosion': (5, 0.15), 'physical': (2, 0.15)}},
}
```

- [ ] **Step 2: Add `artillery_shell_damage` to the `TREES` dict**

```python
'artillery_shell_damage': {
    'name': 'Artillery Shell Damage (enemies)',
    'mult_fn': asd_mult,
    'tech_name': 'Artillery shell damage (research)',
    'cumulative_costs': _asd_cumulative_costs(),
    'caption': 'Shells required to destroy enemy',
    'max_level': 20,
    # Levels 0-9 shown individually; 10-19 merged (no shell-count changes);
    # level 20 shown individually (egg raft becomes 1-shot).
    'force_rows': list(range(10)) + [(10, 19), 20],
    'weapons': [
        # Artillery shell deals 1000 physical + 1000 explosion per shot.
        # The 7th element lists extra (base, dmg_type) components summed per shot.
        ('Artillery shell', 1000, 'physical',
         '{{Icon|Artillery shell}}', 'Artillery shell', 1,
         [(1000, 'explosion')]),
    ],
    'target_groups': [
        ('Enemies', {
            'Behemoth worm': WORMS['Behemoth worm'],
            'Spawner':       SPAWNERS_MAX_EVO['Spawner'],
            'Egg raft':      EGG_RAFTS_MAX_EVO['Egg raft'],
        }, 1.0),
    ],
    'target_wiki_labels': {
        'Behemoth worm': '{{Icon|Behemoth_worm}}',
        'Spawner':       '{{Icon|Biter_nest}}',
        'Egg raft':      '{{Icon|Egg_raft}}',
    },
},
```

- [ ] **Step 3: Verify text output (uses breakpoints, not force_rows)**

```bash
python3 factorio_thresholds.py artillery_shell_damage
```

Expected:
```
=== Artillery Shell Damage (enemies) (max level 20) ===
       Level  Behem  Spawn  Egg r
...
         0-4      2      2      3
         5-7      2      2      2
           8      1      2      2
        9-19      1      1      2
          20      1      1      1
```

(Exact column-width formatting may vary; the level ranges and shell counts must match.)

- [ ] **Step 4: Generate wiki markup and inspect**

```bash
python3 factorio_thresholds.py artillery_shell_damage --wiki
```

Verify by eye:
- First data row (level 0): `rowspan="8"` on behemoth cell (covers rows 0-7), `rowspan="9"` on spawner cell (rows 0-8), `rowspan="5"` on egg raft value-3 cell (rows 0-4)
- Level 8 row: `{{Icon|Artillery shell|1}}` for behemoth (new cell), no new spawner cell (still covered), no new egg raft cell
- Level 9 row: `{{Icon|Artillery shell|1}}` for spawner (new cell)
- Level 10-19 row: level cell shows `{{Icontech|...|10}} to {{Icontech|...|19}}`; cost cell shows `7.161M - 3.67G`
- Level 20 row: level cell shows `{{Icontech|...|20}}+`; `{{Icon|Artillery shell|1}}` for egg raft

- [ ] **Step 5: Save full output to `ArtilleryShellDamageResearch.txt`**

```bash
python3 factorio_thresholds.py artillery_shell_damage --wiki > ArtilleryShellDamageResearch.txt
```

- [ ] **Step 6: Prepend the thresholds section header and intro paragraph**

Edit `ArtilleryShellDamageResearch.txt` to prepend:

```
== Thresholds ==
The table below shows for each level of the artillery shell damage research how many (normal [[quality]]{{SA}}) [[artillery shell]]s are required to destroy a [[Behemoth worm]], a [[Biter spawner]] or [[Spitter spawner]], or an [[Egg raft]]{{SA}}. HP values for spawners and egg rafts are at maximum evolution. Small, medium, and big worms and small egg rafts are always destroyed in one hit regardless of research level and are not shown.

```

The file should now start with `== Thresholds ==` and end with `|}`.

- [ ] **Step 7: Commit**

```bash
git add factorio_thresholds.py ArtilleryShellDamageResearch.txt
git commit -m "feat: add artillery_shell_damage tree and generate thresholds wiki table"
```

---

## Self-Review

**Spec coverage:**
- `asd_mult(n) = 1.0 + 0.10*n` - Task 1
- `_asd_cumulative_costs` with 7 pack types, formula `7000*(2^n-1)` - Task 1
- Dual-damage (1000 physical + 1000 explosion summed per shot) - Task 2
- `force_rows`: levels 0-9 individual, `(10,19)` merged with cost range, level 20 - Tasks 3 & 4
- Targets: Behemoth worm (3000 HP), Spawner max-evo (3500 HP), Egg raft max-evo (5000 HP) - Task 4
- No overkill factor (1.0 for all targets) - Task 4
- Column icons: `{{Icon|Behemoth_worm}}`, `{{Icon|Biter_nest}}`, `{{Icon|Egg_raft}}` - Task 4
- Data cell icons: `{{Icon|Artillery shell|N}}` - Task 4
- Intro text noting excluded targets - Task 4 Step 6
- Output in `ArtilleryShellDamageResearch.txt` - Task 4

**Placeholder scan:** No TBDs or vague steps. All code blocks are complete.

**Type consistency:**
- `extra_resists` key: set in `build_columns` Step 1, read in `_col_shots` Step 2 - consistent
- `force_rows` key: set in TREES Step 2, read via `tree.get('force_rows')` in `print_wiki_table` Step 2 - consistent
- `_emit_force_rows` defined before `print_wiki_table`, called from within it - consistent
- `asd_mult` and `_asd_cumulative_costs` defined before TREES, referenced in tree dict - consistent
- Weapon tuple 7th element is `[(1000, 'explosion')]` in TREES; `build_columns` reads `weapon[6]` and calls it `extra_dmg` - consistent
