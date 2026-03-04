# smg.py
# A light submachine gun: three-bullet spread burst with a longer cooldown.

from __future__ import annotations
from .weapon import Weapon


class SMG(Weapon):
    """Submachine gun.

    * Fires 3 bullets per shot (small spread)
    * Cooldown is 3x the pistol cooldown (0.15s -> 0.45s)
    """

    def __init__(self):
        super().__init__(burst_bullets=3, spread_deg=8.0, cooldown=0.45)
