#!/usr/bin/env python3
"""
Factorio damage threshold calculator.

For each research level, computes how many shots are needed to kill each
target. Outputs either a plain text summary or a MediaWiki table with
per-column rowspan merging (same style as the Thresholds table in
StrongerExplosivesResearch.txt).

Usage:
    python3 factorio_thresholds.py [tree] [--wiki]

    tree: stronger_explosives | physical_projectile  (default: all trees)
    --wiki: MediaWiki markup  (default: text)
"""
import math
import sys

# ---------------------------------------------------------------------------
# Target data: hp, resist = {damage_type: (flat, pct)}
# ---------------------------------------------------------------------------

ASTEROIDS = {
    'Small':       {'hp': 100,  'resist': {'explosion': (0, 0.50), 'physical': (0,    0.00), 'laser': (0, 0.20)}},
    'Medium':      {'hp': 400,  'resist': {'explosion': (0, 0.30), 'physical': (0,    0.10), 'laser': (0, 0.90)}},
    'Big':         {'hp': 2000, 'resist': {'explosion': (0, 0.10), 'physical': (2000, 0.10), 'laser': (0, 0.95)}},
    'Huge':        {'hp': 5000, 'resist': {'explosion': (0, 0.99), 'physical': (3000, 0.10), 'laser': (0, 0.99)}},
    'Small Prom':  {'hp': 200,  'resist': {'explosion': (0, 0.50), 'physical': (0,    0.00), 'laser': (0, 0.20)}},
    'Medium Prom': {'hp': 800,  'resist': {'explosion': (0, 0.30), 'physical': (0,    0.10), 'laser': (0, 0.90)}},
    'Big Prom':    {'hp': 4000, 'resist': {'explosion': (0, 0.10), 'physical': (2000, 0.10), 'laser': (0, 0.95)}},
    'Huge Prom':   {'hp': 10000,'resist': {'explosion': (0, 0.99), 'physical': (3000, 0.10), 'laser': (0, 0.99)}},
}

BITERS = {
    'Small Biter':    {'hp': 15,   'resist': {}},
    'Medium Biter':   {'hp': 75,   'resist': {'explosion': (0, 0.10), 'physical': (4, 0.10)}},
    'Big Biter':      {'hp': 375,  'resist': {'explosion': (0, 0.10), 'physical': (8, 0.10)}},
    'Behemoth Biter': {'hp': 3000, 'resist': {'explosion': (12, 0.10), 'physical': (12, 0.10)}},
}

SPAWNERS = {
    'Biter Spawner':   {'hp': 350, 'resist': {'explosion': (5, 0.0), 'physical': (2, 0.15)}},
    'Spitter Spawner': {'hp': 350, 'resist': {'explosion': (5, 0.0), 'physical': (2, 0.15)}},
}

# Worms — HP is fixed (not evolution-dependent).
# Small/medium/big worms are always one-shot by artillery at any research level
# and are included here for reference only; only Behemoth worm is in the tree.
WORMS = {
    'Small Worm':    {'hp': 200,  'resist': {}},
    'Medium Worm':   {'hp': 500,  'resist': {'explosion': (5, 0.15), 'physical': (5, 0.0)}},
    'Big Worm':      {'hp': 1500, 'resist': {'explosion': (10, 0.30), 'physical': (10, 0.0)}},
    'Behemoth Worm': {'hp': 3000, 'resist': {'explosion': (10, 0.30), 'physical': (10, 0.0)}},
}

# Max-evolution HP: spawners scale up to 10x base (350 -> 3500).
# Biter and spitter spawners share identical stats; merged as one column.
SPAWNERS_MAX_EVO = {
    'Spawner': {'hp': 3500, 'resist': {'explosion': (5, 0.0), 'physical': (2, 0.15)}},
}

# Max-evolution HP: egg raft scales up to 10x base (500 -> 5000).
EGG_RAFTS_MAX_EVO = {
    'Egg Raft': {'hp': 5000, 'resist': {'explosion': (5, 0.15), 'physical': (2, 0.15)}},
}

SPITTER_ENEMIES = {
    'Behemoth Spitter': {'hp': 1500, 'resist': {'explosion': (0, 0.30)}},
}

GLEBA_ENEMIES = {
    # hits_per_activation: Tesla bolt bounces between segments sharing one HP pool.
    # Strafer: 3 reliable hits (5 legs but attacks from range ~31 tiles; only 3 in bounce range).
    # Stomper: 5 reliable hits (5 legs, closes to melee so all legs within 12-tile bounce range).
    # Confirmed by in-game testing at levels 6 and 10.
    'Big Strafer': {'hp': 2400,  'resist': {'laser': (0, 0.50), 'physical': (2, 0.10)}, 'hits_per_activation': 3},
    'Big Stomper': {'hp': 15000, 'resist': {'impact': (0, 0.80), 'laser': (0, 0.80), 'physical': (2, 0.50)}, 'hits_per_activation': 4},
}

# ---------------------------------------------------------------------------
# Research multipliers
# ---------------------------------------------------------------------------

_SE = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.3, 4: 1.7, 5: 2.2, 6: 2.8}


def se_mult(level: int) -> float:
    """Stronger Explosives cumulative damage multiplier at the given level.

    Levels 0-2 grant no bonus to rockets (those levels only buff grenades
    and landmines). Level 3+ follows a lookup table up to 6, then grows
    linearly at +0.5 per level.
    Ref: https://forums.factorio.com/viewtopic.php?p=631428#p631428
    """
    return _SE[level] if level <= 6 else 2.8 + 0.5 * (level - 6)


_LW = {0: 1.0, 1: 1.20, 2: 1.40, 3: 1.70, 4: 2.10, 5: 2.60, 6: 3.30}


def lw_mult(level: int) -> float:
    """Laser Weapons Damage cumulative damage multiplier at the given level.

    Levels 0-6 follow a lookup table. Level 7+ grows linearly at +70% per
    level: cumulative = 230% + 70%*(level-6), so mult = 3.30 + 0.70*(level-6).
    """
    return _LW[level] if level <= 6 else 3.30 + 0.70 * (level - 6)


_PP = {0: 1.0, 1: 1.10}


def pp_mult(level: int) -> float:
    """Physical Projectile Damage cumulative multiplier per component (ammo OR turret).

    Both the ammo and the gun turret each receive this multiplier independently
    (confirmed from the wiki's Space Age table and in-game tooltips).

    Level 0: 1.0. Level 1: 1.10. Level 2+: 0.80 + 0.20*level.
    In Space Age, level 6 is halved vs vanilla: cumulative = 100% (not 120%),
    so pp_mult(6) = 2.0 and pp_mult(n>=6) = 2.0 + 0.20*(n-6).

    Levels 0-5 are the same as vanilla; level 6+ differ.
    """
    if level in _PP:
        return _PP[level]
    return 0.8 + 0.2 * level


def pp_total_mult(level: int) -> float:
    """Total damage multiplier for a gun turret firing PP-research ammo in Space Age.

    Both the ammo and the turret each receive pp_mult independently.
    Total damage = base_ammo * pp_mult * pp_mult = base_ammo * pp_mult^2.
    Verified by in-game tooltips (game shows 'turret: 5 + bonus', ammo: '5 + bonus'):
      Level 3: turret=9.8 (5*1.4^2), ammo=7 (5*1.4)
      Level 4: turret=12.8, ammo=8     Level 5: turret=16.2, ammo=9
      Level 6: turret=20.0, ammo=10    Level 7: turret=24.2, ammo=11
      Level 8: turret=28.8, ammo=12    Level 9: turret=33.8, ammo=13
      Level 10: turret=39.2, ammo=14   Level 11: turret=45.0, ammo=15
    """
    m = pp_mult(level)
    return m * m


# ---------------------------------------------------------------------------
# Core damage formula
# ---------------------------------------------------------------------------

def shots_needed(hp: float, overkill: float, base_dmg: float, mult: float,
                 resist: tuple, round_per_hit: bool = False) -> int:
    """Shots required to kill a target.

    Effective damage per shot: max(base_dmg * mult - flat, 1) * (1 - pct)
    Asteroids use overkill=1.01 (rocket turret behaviour); all other
    targets use overkill=1.0.

    round_per_hit: if True, apply round-half-up to dmg_eff before computing
    shot count. Used for gun turret vs asteroids (PP tree): the game appears
    to round per-hit effective damage, explaining the level-0 observation
    that ceil(5*0.9) = 4.5 should give 89 bullets but the game gives 80
    (round_half_up(4.5) = 5, ceil(400/5) = 80).
    """
    flat, pct = resist
    dmg_eff = max(base_dmg * mult - flat, 1.0) * (1.0 - pct)
    if round_per_hit:
        dmg_eff = max(math.floor(dmg_eff + 0.5), 1)
    # Subtract a small epsilon before ceiling to avoid floating-point
    # boundary errors (e.g. 1.0 - 0.9 = 0.0999...998 in binary, which
    # makes ceil(400/2.0) = 201 instead of 200). True non-integer ratios
    # are always at least ~2e-4 away from an integer boundary (hp ≤ 10000),
    # so 1e-9 is safe.
    return math.ceil(hp * overkill / dmg_eff - 1e-9)


# ---------------------------------------------------------------------------
# Research tree definitions
# ---------------------------------------------------------------------------

# Asteroids targeted by rocket/explosive weapons (Huge excluded — 99%
# explosion resistance makes rockets impractical against them).
ASTEROIDS_SE = {k: v for k, v in ASTEROIDS.items()
                if k not in ('Huge', 'Huge Prom')}

# Asteroids targeted by gun turrets — Big/Huge excluded (flat physical
# resistance makes bullets impractical); Medium Prom excluded (2× HP makes
# rocket turrets more practical for that tier).
ASTEROIDS_PP = {k: v for k, v in ASTEROIDS.items()
                if k in ('Small', 'Medium', 'Small Prom')}

# Asteroids targeted by laser turrets. Medium is included despite its 90%
# resistance (never one-shots) because the community targets it in practice.
# Big/Huge excluded (95%/99% resistance — impractical even at high levels).
ASTEROIDS_LW = {k: v for k, v in ASTEROIDS.items()
                if k in ('Small', 'Medium')}

_ASTEROID_ICONS = {
    'Small':       '{{Icon|Metallic asteroid chunk|S|space-age=yes}}{{Icon|Carbonic asteroid chunk|S|space-age=yes}}{{Icon|Oxide asteroid chunk|S|space-age=yes}}',
    'Medium':      '{{Icon|Metallic asteroid chunk|M|space-age=yes}}{{Icon|Carbonic asteroid chunk|M|space-age=yes}}{{Icon|Oxide asteroid chunk|M|space-age=yes}}',
    'Big':         '{{Icon|Metallic asteroid chunk|B|space-age=yes}}{{Icon|Carbonic asteroid chunk|B|space-age=yes}}{{Icon|Oxide asteroid chunk|B|space-age=yes}}',
    'Small Prom':  '{{Icon|Promethium asteroid chunk|SP|space-age=yes}}',
    'Medium Prom': '{{Icon|Promethium asteroid chunk|M|space-age=yes}}',
    'Big Prom':    '{{Icon|Promethium asteroid chunk|B|space-age=yes}}',
    # Huge asteroid chunk icon name not yet confirmed for the wiki.
}

def _si(n: int) -> str:
    """Format an integer with SI suffix (k, M, G, T), dropping trailing zeros."""
    if n < 1_000:
        return str(n)
    if n < 1_000_000:
        return f'{n / 1_000:.2f}'.rstrip('0').rstrip('.') + 'k'
    if n < 1_000_000_000:
        return f'{n / 1_000_000:.3f}'.rstrip('0').rstrip('.') + 'M'
    if n < 1_000_000_000_000:
        return f'{n / 1_000_000_000:.3f}'.rstrip('0').rstrip('.') + 'G'
    return f'{n / 1_000_000_000_000:.3f}'.rstrip('0').rstrip('.') + 'T'


def _lw_cumulative_costs(max_lvl: int = 50) -> dict:
    """Cumulative total science pack cost to REACH each laser weapons level.

    Pack counts per level: 1-4 use 4 types (Auto/Log/Mil/Chem),
    5-6 use 5 types (+Util), 7+ use 6 types (+Space).
    """
    n_packs = [4, 4, 4, 4, 5, 5]  # number of pack types per level 1-6

    def per_level_total(n: int) -> int:
        if n <= 6:
            return n_packs[n - 1] * (n * 100)
        return 6 * (2 ** (n - 7) * 1000)

    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += per_level_total(lvl)
        result[lvl] = _si(total)
    return result


def _pp_cumulative_costs(max_lvl: int = 50) -> dict:
    """Cumulative total science pack cost (all types summed) to REACH each level.

    Returns a dict: level -> SI-formatted string ('-' for level 0).
    """
    n_packs = [1, 2, 3, 3, 4, 5, 6]  # number of pack types per level 1-6

    def per_level_total(n: int) -> int:
        if n <= 6:
            return n_packs[n - 1] * (n * 100)
        return 6 * (2 ** (n - 7) * 1000)

    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += per_level_total(lvl)
        result[lvl] = _si(total)
    return result


def asd_mult(level: int) -> float:
    """Artillery Shell Damage cumulative multiplier.

    Simple linear 10% per level — no lookup table.
    Level 0: 1.0. Level n: 1.0 + 0.10 * n.
    """
    return 1.0 + 0.10 * level


def _asd_cumulative_costs(max_lvl: int = 50) -> dict:
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


def ewd_mult(level: int) -> float:
    """Electric Weapons Damage cumulative multiplier for Tesla turret.

    Levels 0-2 grant no Tesla bonus (those levels only buff Destroyers).
    Level 3: +70% cumulative. Level 4+: +70% per level.
    mult = 1 + 0.70*(level - 2) for level >= 3.
    """
    if level < 3:
        return 1.0
    return 1.0 + 0.70 * (level - 2)


def _ewd_cumulative_costs(max_lvl: int = 20) -> dict:
    """Cumulative total science pack cost to REACH each electric weapons damage level.

    Level 1: Auto+Log+Mil+Chem+Util × 250 (5 types).
    Level 2: +Space × 500 (6 types).
    Level 3+: +EM × 1000 × 2^(level-3) (7 types).
    """
    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        if lvl == 1:
            per_level = 5 * 250
        elif lvl == 2:
            per_level = 6 * 500
        else:
            per_level = 7 * 1000 * (2 ** (lvl - 3))
        total += per_level
        result[lvl] = _si(total)
    return result


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


TREES = {
    'stronger_explosives': {
        'name': 'Stronger Explosives',
        'mult_fn': se_mult,
        'weapons': [
            # (label, base_dmg, dmg_type, header_icon, data_icon_name, magazine_size)
            ('Rocket',     200, 'explosion', '{{Icon|Rocket}}',               'Rocket',           1),
            ('Exp Direct', 150, 'explosion', '{{Icon|Explosive rocket|hit}}', 'Explosive rocket', 1),
            ('Exp AoE',    100, 'explosion', '{{Icon|Explosive rocket|AoE}}', 'Explosive rocket', 1),
        ],
        'target_groups': [
            # (group_name, targets_dict, overkill)
            ('Asteroids', ASTEROIDS_SE, 1.01),
            ('Biters',    BITERS,       1.0),
            ('Spawners',  SPAWNERS,     1.0),
        ],
        'target_wiki_labels': _ASTEROID_ICONS,
    },
    'laser_weapons': {
        'name': 'Laser Weapons (laser turret vs asteroids)',
        'mult_fn': lw_mult,
        'tech_name': 'Laser weapons damage (research)',
        'cumulative_costs': _lw_cumulative_costs(),
        'caption': 'Activations required to destroy asteroid',
        # Medium never reaches 1 activation (90% resistance); cap the table
        # at level 20 where Small is long-since settled at 1 activation.
        'max_level': 20,
        'weapons': [
            ('Laser turret', 20, 'laser', '{{Icon|Laser turret}}', None, 1),
        ],
        'target_groups': [
            # Laser turrets do not apply the 1% overkill (rocket turret only).
            ('Asteroids', ASTEROIDS_LW, 1.0),
        ],
        'target_wiki_labels': _ASTEROID_ICONS,
    },
    'physical_projectile': {
        'name': 'Physical Projectile (gun turret vs asteroids)',
        # Both ammo and turret each receive pp_mult independently, so total
        # damage = base * pp_mult^2. Use pp_total_mult to encode this.
        'mult_fn': pp_total_mult,
        # Setting tech_name enables Icontech level cells, the cost column,
        # and {{Icon|...|N}} formatting for data cells in wiki output.
        'tech_name': 'Physical projectile damage (research)',
        'cumulative_costs': _pp_cumulative_costs(),
        'caption': 'Magazines required to destroy asteroid',
        'weapons': [
            ('Firearm',  5,  'physical', '{{Icon|Firearm magazine}}',         'Firearm magazine',         10),
            ('Piercing', 8,  'physical', '{{Icon|Piercing rounds magazine}}', 'Piercing rounds magazine', 10),
            ('Uranium',  14, 'physical', '{{Icon|Uranium rounds magazine}}',  'Uranium rounds magazine',  10),
        ],
        'target_groups': [
            # Gun turrets do NOT apply the 1% overkill (rocket turret only).
            # No per-hit rounding: confirmed at level 3 Small/Firearm = 11 bullets
            # (ceil(100/9.8)=11, not round(9.8)=10). Level 0 Medium/Firearm =
            # 89 bullets = 9 magazines (ceil(400/4.5)=89); initial "8 magazines"
            # count was off-by-one because the 9th partially-used magazine was
            # still loaded in the turret.
            ('Asteroids', ASTEROIDS_PP, 1.0),
        ],
        'target_wiki_labels': _ASTEROID_ICONS,
    },
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
                'Behemoth Worm': WORMS['Behemoth Worm'],
                'Spawner':       SPAWNERS_MAX_EVO['Spawner'],
                'Egg Raft':      EGG_RAFTS_MAX_EVO['Egg Raft'],
            }, 1.0),
        ],
        'target_wiki_labels': {
            'Behemoth Worm': '{{Icon|Behemoth_worm}}',
            'Spawner':       '{{Icon|Biter_nest}}',
            'Egg Raft':      '{{Icon|Egg_raft}}',
        },
    },
    'electric_weapons_damage': {
        'name': 'Electric Weapons Damage (Tesla turret vs enemies)',
        'intro': (
            "== Thresholds ==\n"
            "''Note: The values in this table are approximate. The Tesla turret's chain lightning"
            " bounces between nearby targets, so the number of hits per activation varies with"
            " enemy positioning and movement.''\n"
            "The table below shows the number of [[Tesla turret]]{{SA}} activations required"
            " to destroy each enemy at each level of [[Electric weapons damage (research)]]{{SA}}."
            " The Tesla turret fires a chain lightning bolt that bounces between nearby targets;"
            " against multi-segment enemies (Big Strafer, Big Stomper) each activation can hit"
            " multiple legs sharing one HP pool.\n"
        ),
        'mult_fn': ewd_mult,
        'tech_name': 'Electric weapons damage (research)',
        'cumulative_costs': _ewd_cumulative_costs(),
        'caption': 'Activations required to destroy enemy',
        # Big Stomper never reaches 1-shot within level 20 (~level 37 needed with 5 hits/activation).
        # Cap at 20 to match the laser_weapons tree style.
        'max_level': 20,
        'weapons': [
            ('Tesla turret', 120, 'electric', '{{Icon|Tesla turret}}', 'Tesla turret', 1),
        ],
        'target_groups': [
            ('Enemies', {
                'Behemoth Biter':  BITERS['Behemoth Biter'],
                'Behemoth Spitter': SPITTER_ENEMIES['Behemoth Spitter'],
                'Big Strafer': GLEBA_ENEMIES['Big Strafer'],
                'Big Stomper': GLEBA_ENEMIES['Big Stomper'],
            }, 1.0),
        ],
        'target_wiki_labels': {
            'Behemoth Biter':  '{{Icon|Behemoth_biter}}',
            'Behemoth Spitter': '{{Icon|Behemoth_spitter}}',
            'Big Strafer': '{{Icon|Strafer_big}}',
            'Big Stomper': '{{Icon|Stomper_big}}',
        },
        'note': "''Note: Big Stomper values are approximate. The Tesla bolt hits 3-5 of its 5 legs per activation depending on positioning; the table uses a 4-hit average. Actual activations may vary by ±2.''",
    },
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
}


# ---------------------------------------------------------------------------
# Table computation
# ---------------------------------------------------------------------------

def build_columns(tree: dict) -> list:
    """Return a flat list of column dicts for the given tree."""
    cols = []
    for (group_name, targets, overkill) in tree['target_groups']:
        for (target_name, target) in targets.items():
            for weapon in tree['weapons']:
                weapon_name    = weapon[0]
                base_dmg       = weapon[1]
                dmg_type       = weapon[2]
                header_icon    = weapon[3] if len(weapon) > 3 else weapon[0]
                data_icon_name = weapon[4] if len(weapon) > 4 else None
                magazine_size  = weapon[5] if len(weapon) > 5 else 1
                extra_dmg      = weapon[6] if len(weapon) > 6 else []
                extra_resists  = [
                    (base, target['resist'].get(dt, (0, 0.0)))
                    for base, dt in extra_dmg
                ]
                resist = target['resist'].get(dmg_type, (0, 0.0))
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
    return cols


def _col_shots(col: dict, mult: float) -> int:
    """Raw shots needed to kill the target.

    If col['extra_resists'] is non-empty, sums all damage components per shot
    (e.g. artillery shell: 1000 physical + 1000 explosion). Otherwise falls
    through to shots_needed, preserving round_per_hit behaviour for gun turrets.

    hits_per_activation > 1 scales effective damage per activation (e.g. Tesla
    turret bouncing between segments of a segmented enemy).
    """
    hits = col.get('hits_per_activation', 1)
    if col['extra_resists']:
        flat, pct = col['resist']
        total_dmg = max(col['base_dmg'] * mult - flat, 1.0) * (1.0 - pct)
        for base2, (flat2, pct2) in col['extra_resists']:
            total_dmg += max(base2 * mult - flat2, 1.0) * (1.0 - pct2)
        total_dmg *= hits
        return math.ceil(col['hp'] * col['overkill'] / total_dmg - 1e-9)
    flat, pct = col['resist']
    dmg_eff = max(col['base_dmg'] * mult - flat, 1.0) * (1.0 - pct) * hits
    if col.get('round_per_hit', False):
        dmg_eff = max(math.floor(dmg_eff + 0.5), 1)
    return math.ceil(col['hp'] * col['overkill'] / dmg_eff - 1e-9)


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


def find_max_level(tree: dict, cap: int = 500) -> int:
    """Smallest level at which every column displays 1 unit (shot or magazine)."""
    cols = build_columns(tree)
    mult_fn = tree['mult_fn']
    for lvl in range(cap + 1):
        mult = mult_fn(lvl)
        if all(_col_display(c, mult) == 1 for c in cols):
            return lvl
    return cap


def compute_table(tree: dict, max_level: int):
    """Return (cols, breakpoints, all_shots).

    all_shots[lvl] is a tuple of DISPLAY VALUES per column (magazines or
    single shots). Breakpoints fire only when a display value changes.
    """
    cols = build_columns(tree)
    mult_fn = tree['mult_fn']

    all_shots: dict[int, tuple] = {}
    for lvl in range(max_level + 1):
        mult = mult_fn(lvl)
        all_shots[lvl] = tuple(_col_display(c, mult) for c in cols)

    breakpoints = [0]
    for lvl in range(1, max_level + 1):
        if all_shots[lvl] != all_shots[lvl - 1]:
            breakpoints.append(lvl)

    return cols, breakpoints, all_shots


# ---------------------------------------------------------------------------
# Text output
# ---------------------------------------------------------------------------

def print_text(tree: dict) -> None:
    max_level = tree.get('max_level') or find_max_level(tree)
    cols, breakpoints, all_shots = compute_table(tree, max_level)
    n_bps = len(breakpoints)

    print(f'\n=== {tree["name"]} (max level {max_level}) ===')

    w = 4
    labels = [c['label'] for c in cols]
    hdr = f"{'Level':>12}  " + '  '.join(f'{lb[:w]:>{w}}' for lb in labels)
    print(hdr)
    print('-' * len(hdr))

    for i, lvl in enumerate(breakpoints):
        next_lvl = breakpoints[i + 1] if i + 1 < n_bps else max_level + 1
        end = next_lvl - 1
        lvl_str = str(lvl) if end == lvl else f'{lvl}-{end}'
        row = f'{lvl_str:>12}  ' + '  '.join(f'{v:>{w}}' for v in all_shots[lvl])
        print(row)


# ---------------------------------------------------------------------------
# Wiki output: per-column rowspan merging
# ---------------------------------------------------------------------------

def _emit_force_rows(cols: list, force_rows: list, mult_fn,
                     cumulative_costs: dict, tech_name: str) -> None:
    """Emit data rows for a table whose row structure is explicitly specified.

    force_rows elements:
      int n       - one row for level n; last element gets a '+' suffix on the level cell
      (lo, hi)    - one merged row for levels lo-hi; values computed at lo;
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


def print_wiki_table(tree: dict) -> None:
    """Emit a MediaWiki table with per-column rowspan merging.

    A new table row (|-) is emitted whenever ANY column's shot count
    changes. Columns that have not changed omit their cell (covered by
    the previous cell's rowspan). This mirrors the compact style of the
    Thresholds table in StrongerExplosivesResearch.txt.

    When tree has 'tech_name' set (e.g. Physical Projectile):
    - 2-row header: Level (rowspan=2), Cost (rowspan=2), then target cols
    - Level cells use {{Icontech|tech_name|N}} format
    - Data cells use {{Icon|data_icon_name|N}} format
    - A cumulative research cost cell follows each level cell

    Without 'tech_name' (e.g. Stronger Explosives):
    - 3-row header: groups, targets, weapons
    - Level cells are plain text ranges ("0-2", "3", etc.)
    - Data cells are plain integers
    """
    max_level = tree.get('max_level') or find_max_level(tree)
    cols, breakpoints, all_shots = compute_table(tree, max_level)
    n_cols = len(cols)
    n_bps = len(breakpoints)

    mult_fn = tree['mult_fn']
    tech_name = tree.get('tech_name')
    cumulative_costs = tree.get('cumulative_costs', {})

    # Per-column change levels (with sentinel at end so indexing is safe).
    col_change_at: list[list[int]] = []
    for ci in range(n_cols):
        bp = [0]
        for lvl in range(1, max_level + 1):
            if all_shots[lvl][ci] != all_shots[lvl - 1][ci]:
                bp.append(lvl)
        bp.append(max_level + 1)  # sentinel
        col_change_at.append(bp)

    def col_rowspan(ci: int, bi: int) -> int:
        """Number of global breakpoints covered by a new cell for column ci
        starting at global breakpoint index bi."""
        lvl = breakpoints[bi]
        my_bps = col_change_at[ci]
        pos = my_bps.index(lvl)      # lvl is always present when we emit
        next_change = my_bps[pos + 1]
        return sum(1 for b in breakpoints if lvl <= b < next_change)

    if tree.get('intro'):
        print(tree['intro'])
    print(f'<!-- {tree["name"]} damage thresholds -->')
    print('{| class="wikitable" style="text-align:center;"')
    n_weapons = len(tree['weapons'])
    target_wiki_labels = tree.get('target_wiki_labels', {})
    weapon_wiki_icons = [w[3] for w in tree['weapons']]
    n_targets_total = sum(len(targets) for _, targets, _ in tree['target_groups'])

    if tech_name:
        # --- caption row + 2-row header: Level (rs=2) | Cost (rs=2) | target cols ---
        if caption := tree.get('caption'):
            # +2 for the Level and Cost columns
            total_cols = 2 + n_targets_total * n_weapons
            print(f'! colspan="{total_cols}" | {caption}')
            print('|-')
        target_header_cells = []
        for (_, targets, _) in tree['target_groups']:
            for target_name in targets:
                wiki_label = target_wiki_labels.get(target_name, target_name)
                target_header_cells.append(f'colspan="{n_weapons}" | {wiki_label}')
        print(f'! rowspan="2" | Level'
              f' !! rowspan="2" | Cumulative<br>research cost'
              f' !! ' + ' !! '.join(target_header_cells))
        print('|-')
        weapon_cells = ' !! '.join(
            icon for _ in range(n_targets_total) for icon in weapon_wiki_icons
        )
        print(f'! {weapon_cells}')
        print('|-')
    else:
        # --- 3-row header: groups | targets | weapons ---
        groups: list[tuple[str, int]] = []
        for col in cols:
            if groups and groups[-1][0] == col['group']:
                groups[-1] = (groups[-1][0], groups[-1][1] + 1)
            else:
                groups.append((col['group'], 1))
        group_cells = ' !! '.join(
            f'colspan="{span}" | {name}' for name, span in groups
        )
        print(f'! rowspan="3" | Level !! {group_cells}')
        print('|-')

        target_header_cells = []
        for (_, targets, _) in tree['target_groups']:
            for target_name in targets:
                wiki_label = target_wiki_labels.get(target_name, target_name)
                target_header_cells.append(f'colspan="{n_weapons}" | {wiki_label}')
        print('! ' + ' !! '.join(target_header_cells))
        print('|-')

        weapon_cells = ' !! '.join(
            icon for _ in range(n_targets_total) for icon in weapon_wiki_icons
        )
        print(f'! {weapon_cells}')
        print('|-')

    if tree.get('force_rows'):
        _emit_force_rows(cols, tree['force_rows'], mult_fn,
                         cumulative_costs, tech_name)
        print('|}')
        if note := tree.get('note'):
            print(f'\n{note}')
        return

    # Data rows
    # remaining[ci]: how many more global breakpoints are still covered by
    # the current cell for column ci (decremented once per skipped row).
    remaining = [0] * n_cols

    for bi, lvl in enumerate(breakpoints):
        next_bp = breakpoints[bi + 1] if bi + 1 < n_bps else max_level + 1
        end = next_bp - 1
        is_last = next_bp > max_level

        if tech_name:
            tn = tech_name
            if is_last and lvl < max_level:
                lvl_str = (f'{{{{Icontech|{tn}|{lvl}}}}} to'
                           f' {{{{Icontech|{tn}|{max_level}}}}}+')
            elif end > lvl:
                lvl_str = (f'{{{{Icontech|{tn}|{lvl}}}}} to'
                           f' {{{{Icontech|{tn}|{end}}}}}')
            else:
                lvl_str = f'{{{{Icontech|{tn}|{lvl}}}}}'
            cost_val = cumulative_costs.get(lvl, '?')
        else:
            if is_last:
                lvl_str = f'{lvl}-\u221e' if lvl < max_level else str(lvl)
            elif end > lvl:
                lvl_str = f'{lvl}-{end}'
            else:
                lvl_str = str(lvl)

        print('|- style="vertical-align:top;"')
        print(f'! style="vertical-align:middle;" | {lvl_str}')

        if tech_name:
            print(f'| {cost_val}')

        for ci in range(n_cols):
            if remaining[ci] > 0:
                remaining[ci] -= 1
                continue
            rs = col_rowspan(ci, bi)
            remaining[ci] = rs - 1
            val = all_shots[lvl][ci]
            col = cols[ci]
            if tech_name and col['data_icon_name']:
                cell_content = f'{{{{Icon|{col["data_icon_name"]}|{val}}}}}'
            else:
                cell_content = str(val)
            if rs > 1:
                print(f'| rowspan="{rs}" | {cell_content}')
            else:
                print(f'| {cell_content}')

    print('|}')
    if note := tree.get('note'):
        print(f'\n{note}')


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    args = sys.argv[1:]
    wiki = '--wiki' in args
    tree_args = [a for a in args if not a.startswith('--')]

    if tree_args:
        unknown = [a for a in tree_args if a not in TREES]
        if unknown:
            print(f'Unknown tree(s): {unknown}', file=sys.stderr)
            print(f'Available: {list(TREES)}', file=sys.stderr)
            sys.exit(1)
        selected = [TREES[a] for a in tree_args]
    else:
        selected = list(TREES.values())

    for tree in selected:
        if wiki:
            print_wiki_table(tree)
        else:
            print_text(tree)
