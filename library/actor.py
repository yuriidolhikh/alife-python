from dataclasses import dataclass

from .types import Location


@dataclass
class Actor:
    """Individual actor on the grid"""
    faction: str
    location: Location
    looted: bool = False

    def __str__(self):
        return f"{self.faction.capitalize()} actor at location {self.location}"
