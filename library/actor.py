from dataclasses import dataclass


@dataclass
class Actor:
    """Individual actor on the grid"""
    faction: str
    location: tuple
    looted: bool = False

    def __str__(self):
        return f"{self.faction.capitalize()} actor at location {self.location}"
