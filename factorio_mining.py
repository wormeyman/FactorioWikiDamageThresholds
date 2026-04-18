#!/usr/bin/env python3
"""
Factorio mining productivity threshold calculator.

Shows how many mining drills are needed to fully saturate each belt type
at each research level (0, 10, 20, ..., 110). Outputs plain text or MediaWiki markup.

Usage:
    python3 factorio_mining.py [--wiki]

    --wiki: MediaWiki markup  (default: text)
"""
import math
import sys

STACK_SIZE = 4  # Quad stacking from Gleba research

# (display_name, base_speed items/s, stacking)
MINERS = [
    ('Electric mining drill', 0.5, False),
    ('Big mining drill',      2.5, False),
    ('Big mining drill',      2.5, True),   # with quad stacking
]

# (display_name, lane_speed items/s per lane, space_age)
BELTS = [
    ('Transport belt',         7.5,  False),
    ('Fast transport belt',    15.0, False),
    ('Express transport belt', 22.5, False),
    ('Turbo transport belt',   30.0, True),
]

LEVELS = list(range(0, 111, 10))

TECH_NAME = 'Mining productivity (research)'


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


def cumulative_cost(level: int) -> str:
    """Cumulative Space Age research cost through a given level, as SI string.

    Level 1: 250 (Automation + Logistic)
    Level 2: 750 (+ 500 Chemical)
    Level N>=3: 750 + 500*(N-2)*(N-1)  [arithmetic: 1000*(N-2) per level]
    """
    if level == 0:
        return '-'
    if level == 1:
        return _si(250)
    cost = 750 + 500 * (level - 2) * (level - 1)
    return _si(cost)


def miners_needed(lane_speed: float, base_speed: float, level: int,
                  stacking: bool = False) -> int:
    """Total drills for both lanes of a belt at a given research level.

    Miners deposit on one side only, so both-lane total = ceil(lane * 2 / speed).
    With stacking, the belt lane capacity is multiplied by STACK_SIZE.
    """
    effective_lane = lane_speed * (STACK_SIZE if stacking else 1)
    effective_miner = base_speed * (1 + 0.1 * level)
    return math.ceil(effective_lane * 2 / effective_miner)


if __name__ == '__main__':
    pass
