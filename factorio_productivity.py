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
