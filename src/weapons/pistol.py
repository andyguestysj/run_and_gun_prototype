# pistol.py
# A simple semi-auto pistol.

from __future__ import annotations
from .weapon import Weapon


class Pistol(Weapon):
    """Basic semi-auto pistol (default player weapon).

    * Fires 1 bullet (no spread)
    * Short cooldown
    """

    def __init__(self):
        super().__init__(burst_bullets=1, spread_deg=0.0, cooldown=0.15)
