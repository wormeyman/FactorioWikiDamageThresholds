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


def min_level_for_target(lane_speed: float, base_speed: float, target: int,
                         stacking: bool = False) -> int | None:
    """Minimum research level where miners_needed <= target, or None if > 1000."""
    for lvl in range(0, 1001):
        if miners_needed(lane_speed, base_speed, lvl, stacking) <= target:
            return lvl
    return None


def print_text() -> None:
    """Print plain-text tables for all belt types."""
    for belt_name, lane_speed, sa in BELTS:
        sa_tag = ' [SA]' if sa else ''
        total = lane_speed * 2
        stacked_total = total * STACK_SIZE
        print(f'\n=== {belt_name}{sa_tag} ({total:.0f}/s, stacked {stacked_total:.0f}/s) ===')
        for miner_name, base_speed, stacking in MINERS:
            t = min_level_for_target(lane_speed, base_speed, 2, stacking)
            stack_tag = ' + stacking' if stacking else ''
            label = f'{miner_name}{stack_tag}'
            if t is not None:
                print(f'  → 2 {label} first at level {t} (cost: {cumulative_cost(t)})')
        headers = [
            'EMD / No modules',
            'BMD / No modules',
            'BMD / No modules + stack',
        ]
        w = 26
        hdr = f"{'Level':>6}  {'Cost':>8}  " + '  '.join(f'{h[:w]:>{w}}' for h in headers)
        print(hdr)
        print('-' * len(hdr))
        for lvl in LEVELS:
            vals = [miners_needed(lane_speed, m[1], lvl, m[2]) for m in MINERS]
            cost = cumulative_cost(lvl)
            row = f'{lvl:>6}  {cost:>8}  ' + '  '.join(f'{v:>{w}}' for v in vals)
            print(row)


_MINER_ICONS = {
    'Electric mining drill': '{{Icon|Electric mining drill}}',
    'Big mining drill':      '{{Icon|Big mining drill|space-age=yes}}',
}


def _miner_cell(mi: int, val: int) -> str:
    name = MINERS[mi][0]
    if name == 'Electric mining drill':
        return f'{{{{Icon|Electric mining drill|{val}}}}}'
    return f'{{{{Icon|Big mining drill|{val}|space-age=yes}}}}'

_BELT_ICONS = {
    'Transport belt':         '{{Icon|Transport belt}}',
    'Fast transport belt':    '{{Icon|Fast transport belt}}',
    'Express transport belt': '{{Icon|Express transport belt}}',
    'Turbo transport belt':   '{{Icon|Turbo transport belt|space-age=yes}}',
}


def print_wiki_table(belt_name: str, lane_speed: float, sa: bool) -> None:
    """Emit a single MediaWiki wikitable for one belt type."""
    sa_tag = '{{SA}}' if sa else ''
    belt_icon = _BELT_ICONS[belt_name]
    emd_icon = _MINER_ICONS['Electric mining drill']
    bmd_icon = _MINER_ICONS['Big mining drill']

    max_threshold = max(
        (min_level_for_target(lane_speed, base_speed, 2, stacking) or 0)
        for _, base_speed, stacking in MINERS
    )
    max_level = max(LEVELS[-1], max_threshold)
    table_levels = list(range(0, max_level + 1, 10))
    n_miners = len(MINERS)
    n_levels = len(table_levels)

    print(f'=== {belt_icon} {belt_name}{sa_tag} ===')
    print(f'<!-- Mining productivity thresholds: {belt_name} -->')
    print('{| class="wikitable" style="text-align:center;"')

    # 2-row header: EMD gets rowspan=2 (single config), BMD gets colspan=2
    print(
        f'! rowspan="2" | Level'
        f' !! rowspan="2" | Cumulative<br>research cost'
        f' !! rowspan="2" | {emd_icon} Electric mining drill<br>No modules'
        f' !! colspan="2" | {bmd_icon} Big mining drill'
    )
    print('|-')
    print('! No modules !! No modules +<br>quad stacking')
    print('|-')

    # Precompute all values
    col_values = [
        [miners_needed(lane_speed, base_speed, lvl, stacking) for lvl in table_levels]
        for _, base_speed, stacking in MINERS
    ]

    # Floor = value at last level; rowspan starts at first row reaching it
    floor_row = []
    for col in col_values:
        floor_val = col[-1]
        floor_row.append(next(ri for ri, v in enumerate(col) if v == floor_val))

    floored = [False] * n_miners

    for ri, lvl in enumerate(table_levels):
        is_last = (ri == n_levels - 1)
        lvl_cell = f'{{{{Icontech|{TECH_NAME}|{lvl}}}}}' + ('+' if is_last else '')
        cost_cell = cumulative_cost(lvl)

        print('|- style="vertical-align:top;"')
        print(f'! style="vertical-align:middle;" | {lvl_cell}')
        print(f'| {cost_cell}')

        for mi in range(n_miners):
            if floored[mi]:
                continue  # covered by rowspan from first floor row

            val = col_values[mi][ri]
            icon = _miner_cell(mi, val)
            if ri == floor_row[mi]:
                floored[mi] = True
                rows_remaining = n_levels - ri
                cell = f"'''{icon}'''"
                if rows_remaining > 1:
                    print(f'| rowspan="{rows_remaining}" | {cell}')
                else:
                    print(f'| {cell}')
            else:
                print(f'| {icon}')

    print('|}')
    print()


def print_wiki() -> None:
    """Emit the full MediaWiki article section for all belt types."""
    print('== Thresholds ==')
    print(
        'The table below shows the number of mining drills needed to fully saturate'
        ' both lanes of each belt type at key [[Mining productivity (research)]]{{SA}} levels.'
        ' Miners deposit ore on one side of the belt only; values shown are total drills'
        ' for both sides. The quad stacking column requires the belt stacking research'
        ' from [[Gleba]] and shows drills needed to fill a belt whose lane capacity'
        ' is 4\u00d7 higher; the miner\'s output speed is unchanged.'
    )
    print()
    for belt_name, lane_speed, sa in BELTS:
        print_wiki_table(belt_name, lane_speed, sa)


if __name__ == '__main__':
    args = sys.argv[1:]
    wiki = '--wiki' in args
    if wiki:
        print_wiki()
    else:
        print_text()
