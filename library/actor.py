from dataclasses import dataclass

from .types import Location

# Experience required to attain a given rank
RANKS = [
    (0, "Rookie"), (2000, "Novice"), (4000, "Experienced"),
    (6000, "Veteran"), (8000, "Master"), (10000, "Legend")
]


@dataclass
class Actor:
    """Individual actor on the grid"""
    faction: str
    location: Location  # TODO: consider removing and using squad location instead
    rank: str = "Rookie"
    experience: int = 0
    looted: bool = False

    def __str__(self):
        return f"{self.faction.capitalize()} actor ({self.rank}) at location {self.location}"

    def gain_exp(self, exp):
        """Simple method to track actor experience"""
        self.experience = min(10000, self.experience + exp)

        return True

    def rank_up(self):
        """Increase actor rank based on current experience"""
        max_rank = RANKS[-1]
        if self.experience == max_rank[0] and self.rank != max_rank[1]:
            self.rank = max_rank[1]

            return True

        for i, rank in enumerate(RANKS):
            if rank[0] > self.experience:
                current = RANKS[i - 1]
                self.rank = current[1]

                return True

        return False
