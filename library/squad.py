import uuid

from dataclasses import dataclass, field

from library.actor import Actor
from library.types import Location


@dataclass
class Squad:
    """Squad on the grid, made up of multiple actors. Executes tasks"""
    faction: str
    location: Location

    sid: str = field(init=False)
    actors: list = field(default_factory=list)  # list of actors in the squad

    has_task: bool = False
    in_combat: bool = False
    is_looting: bool = False

    def __post_init__(self) -> None:
        self.sid = uuid.uuid4().hex[-12:]

    def __str__(self) -> str:
        return f"{self.faction} squad (SID={self.sid}) ({self.num_actors()} {self.num_actors() > 1 and "actors" or "actor"})"

    def num_actors(self) -> int:
        return len(self.actors)

    def is_busy(self) -> bool:
        return self.in_combat or self.is_looting or self.has_task

    def add_actor(self, actor: Actor) -> None:
        self.actors.append(actor)

    def remove_actor(self, actor: Actor) -> bool:
        try:
            index = self.actors.index(actor)
        except ValueError:
            return False

        del self.actors[index]

        return True
