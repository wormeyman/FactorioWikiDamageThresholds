#!/usr/bin/env python3
"""
Factorio productivity threshold calculator.

For each research level at which a new configuration first reaches the
300% productivity cap, shows the current productivity bonus for every
machine x module configuration. Outputs plain text or MediaWiki markup.

Usage:
    python3 factorio_productivity.py [research] [--wiki]

    research: steel_plate  (default: all)
    --wiki: MediaWiki markup  (default: text)
"""
import math
import sys

# ---------------------------------------------------------------------------
# Machines: base productivity bonus and module slot count
# ---------------------------------------------------------------------------

MACHINES = {
    'Foundry':          {'base_prod': 0.50, 'module_slots': 4},
    'Electric furnace': {'base_prod': 0.00, 'module_slots': 2},
}

# ---------------------------------------------------------------------------
# Modules: productivity bonus per module slot.
# 'No modules' has 0.00 per-module bonus; 0.00 x any slot count = 0.
# ---------------------------------------------------------------------------

MODULES = {
    'No modules':              0.00,
    'Prod module 3':           0.10,
    'Legendary Prod module 2': 0.15,
    'Legendary Prod module 3': 0.25,
}

# ---------------------------------------------------------------------------
# SI suffix formatter (independent copy; files intentionally kept separate)
# ---------------------------------------------------------------------------

def _si(n: float) -> str:
    """Format a number with SI suffix (k, M, G, T), dropping trailing zeros."""
    n = int(round(n))
    if n < 1_000:
        return str(n)
    if n < 1_000_000:
        return f'{n / 1_000:.2f}'.rstrip('0').rstrip('.') + 'k'
    if n < 1_000_000_000:
        return f'{n / 1_000_000:.3f}'.rstrip('0').rstrip('.') + 'M'
    if n < 1_000_000_000_000:
        return f'{n / 1_000_000_000:.3f}'.rstrip('0').rstrip('.') + 'G'
    return f'{n / 1_000_000_000_000:.3f}'.rstrip('0').rstrip('.') + 'T'

# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def total_prod(base: float, slots: int, module_bonus: float,
               level: int, bonus_per_level: float) -> float:
    """Total productivity bonus at a given research level (fraction; 1.0 = 100%)."""
    return base + slots * module_bonus + level * bonus_per_level


def min_level_to_cap(base: float, slots: int, module_bonus: float,
                     bonus_per_level: float, cap: float) -> int:
    """Minimum research level to reach the productivity cap.

    Uses epsilon subtraction before ceil to avoid floating-point boundary
    errors (e.g. 2.1 / 0.1 = 20.999...998 in binary floating point).
    True non-integer ratios are always at least ~2e-4 away from an integer
    boundary for the values used here, so 1e-9 is safe.
    """
    needed = cap - base - slots * module_bonus
    if needed <= 0:
        return 0
    return math.ceil(needed / bonus_per_level - 1e-9)

# ---------------------------------------------------------------------------
# Cumulative research cost functions
# ---------------------------------------------------------------------------

def _sp_cumulative_costs(max_lvl: int = 30) -> dict:
    """Cumulative science pack cost to reach each Steel Plate Productivity level.

    Cost per level N: round(1000 x 1.5^N) packs
    (Automation + Logistic + Chemical + Production science packs).
    Returns: {level: SI-formatted string} with '-' for level 0.
    """
    total = 0
    result: dict = {0: '-'}
    for lvl in range(1, max_lvl + 1):
        total += round(1000 * 1.5 ** lvl)
        result[lvl] = _si(total)
    return result

# ---------------------------------------------------------------------------
# Research definitions
# ---------------------------------------------------------------------------

RESEARCHES = {
    'steel_plate': {
        'name': 'Steel Plate Productivity',
        'tech_name': 'Steel plate productivity (research)',
        'bonus_per_level': 0.10,
        'cumulative_costs': _sp_cumulative_costs(),
        'max_level': 30,
        'cap': 3.00,
        'machines': ['Foundry', 'Electric furnace'],
        'module_configs': [
            'No modules',
            'Prod module 3',
            'Legendary Prod module 2',
            'Legendary Prod module 3',
        ],
    },
}

# ---------------------------------------------------------------------------
# Column building and breakpoint detection
# ---------------------------------------------------------------------------

def build_columns(research: dict) -> list:
    """Return flat list of column dicts for the given research.

    One column per (machine x module_config) combination, ordered:
    Foundry configs first, then Electric furnace configs.
    Within each machine: in the order listed in research['module_configs'].
    """
    cols = []
    for machine_name in research['machines']:
        machine = MACHINES[machine_name]
        for config_name in research['module_configs']:
            cols.append({
                'machine':      machine_name,
                'config':       config_name,
                'label':        f'{machine_name} / {config_name}',
                'base_prod':    machine['base_prod'],
                'slots':        machine['module_slots'],
                'module_bonus': MODULES[config_name],
            })
    return cols


def find_breakpoints(research: dict) -> list:
    """Levels at which at least one column first reaches the productivity cap.

    Always includes level 0 as the baseline row.
    Capped at research['max_level'] so no row exceeds the table end.
    Returns a sorted list of unique levels.
    """
    cols = build_columns(research)
    cap = research['cap']
    bpl = research['bonus_per_level']
    max_level = research['max_level']
    cap_levels = set()
    for col in cols:
        lvl = min_level_to_cap(
            col['base_prod'], col['slots'], col['module_bonus'], bpl, cap)
        cap_levels.add(min(lvl, max_level))
    return sorted({0} | cap_levels)

# ---------------------------------------------------------------------------
# Text output
# ---------------------------------------------------------------------------

def print_text(research: dict) -> None:
    """Print a plain text summary of productivity % at each breakpoint level."""
    cols = build_columns(research)
    bpl = research['bonus_per_level']
    breakpoints = find_breakpoints(research)
    max_level = research['max_level']
    cap = research['cap']

    print(f'\n=== {research["name"]} (max level {max_level}) ===')

    w = 8
    labels = [c['label'] for c in cols]
    hdr = f"{'Level':>8}  " + '  '.join(f'{lb[:w]:>{w}}' for lb in labels)
    print(hdr)
    print('-' * len(hdr))

    n_bps = len(breakpoints)
    for i, lvl in enumerate(breakpoints):
        next_lvl = breakpoints[i + 1] if i + 1 < n_bps else max_level + 1
        end = next_lvl - 1
        lvl_str = str(lvl) if end == lvl else f'{lvl}-{end}'
        vals = []
        for c in cols:
            p = int(round(min(
                total_prod(c['base_prod'], c['slots'], c['module_bonus'], lvl, bpl),
                cap) * 100))
            vals.append(f'{p}%')
        row = f'{lvl_str:>8}  ' + '  '.join(f'{v:>{w}}' for v in vals)
        print(row)
