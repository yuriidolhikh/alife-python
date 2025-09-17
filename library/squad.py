from dataclasses import dataclass, field

from .actor import Actor


@dataclass
class Squad:
    """Squad on the grid, made up of multiple actors. Executes tasks"""
    faction: str
    location: tuple[int, int]
    actors: list = field(default_factory=list) # list of actors in the squad
    has_task: bool = False
    in_combat: bool = False
    is_looting: bool = False

    def __str__(self):
        return f"{self.faction.upper()} squad ({len(self.actors)} actors) at location {self.location}"

    def is_busy(self):
        return self.in_combat or self.is_looting or self.has_task

    def add_actor(self, actor: Actor):
        self.actors.append(actor)

    def remove_actor(self, actor: Actor):
        try:
            index = self.actors.index(actor)
        except ValueError:
            return False

        del self.actors[index]

        return True
