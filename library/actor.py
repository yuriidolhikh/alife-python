from dataclasses import dataclass
from typing import Optional

from .types import Location

from config import RANKS, EXP_PER_RANK


@dataclass
class Actor:
    """Individual actor on the grid"""
    faction: str
    location: Location  # TODO: consider removing and using squad location instead
    rank: str = RANKS[0]
    experience: int = 0
    looted: bool = False

    def __str__(self):
        return f"{self.faction.capitalize()} actor ({self.rank}) at location {self.location}"

    def gain_exp(self, exp):
        """Simple method to track actor experience"""
        self.experience = min((len(RANKS) - 1) * EXP_PER_RANK, self.experience + exp)

        return True

    def rank_up(self):
        """Increase actor rank based on current experience"""
        self.rank = RANKS[self.experience // EXP_PER_RANK]

        return True
