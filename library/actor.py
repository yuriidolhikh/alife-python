import random

from dataclasses import dataclass

from library.types import Location
from config import RANKS, EXP_PER_RANK, FACTIONS


@dataclass
class Actor:
    """Individual actor on the grid"""
    faction: str
    location: Location  # TODO: consider removing and using squad location instead
    rank: str = RANKS[0]
    experience: int = 0
    loot_value: int | None = 0

    def __post_init__(self) -> None:
        """Set-up actor after creation"""
        if FACTIONS[self.faction]["can_gain_exp"]:
            if not self.experience: self.gain_exp(random.randint(1, (len(RANKS) - 1) * EXP_PER_RANK))
        else:
            # assume that actors that don't gain exp are "average" for combat purposes
            self.gain_exp(((len(RANKS) - 1) * EXP_PER_RANK) // 2)

        self.rank_up()

        self.loot_value = self.experience // random.randint(10, 30)  # assume actor's loot value is proportional to his experience

    def __str__(self) -> str:
        return f"{self.faction.capitalize()} actor ({self.rank}) at location {self.location}"

    def gain_exp(self, exp: int) -> None:
        """Simple method to track actor experience"""
        self.experience = min((len(RANKS) - 1) * EXP_PER_RANK, self.experience + exp)

    def rank_up(self) -> None:
        """Increase actor rank based on current experience"""
        self.rank = RANKS[self.experience // EXP_PER_RANK]
