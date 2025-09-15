import asyncio
import random

from typing import Awaitable

from classes import MapGrid, Squad, Actor
from config import COMBAT_DURATION, TRAVEL_DURATION, LOOT_DURATION

class Task:
    """Base class for all tasks"""

    # steps of task execution
    # can chain multiple coroutines to create more complex tasks
    _steps: list[Awaitable[bool]]

    async def execute(self):
        while task := self._steps.pop(0):
            await task


class CombatTask(Task):
    """Handles combat between two hostile squads"""

    def __init__(self, grid, left, right):
        self._steps = [self._run(grid, left, right)]

    async def _run(self, grid: MapGrid, left: Squad, right: Squad):

        await asyncio.sleep(COMBAT_DURATION)

        for squad in (left, right):
            losses = random.randint(0, len(squad.actors))

            msg = f"{squad.faction} squad({len(squad.actors)}) {losses and f'lost {losses} {losses > 1 and "men" or "man"}' or 'took no casualtieS'} in combat"
            if losses == len(squad.actors):
                msg += " and was wiped out"

            grid.add_log_msg("COMBAT", msg, squad.location)

            for actor in squad.actors[:losses]:
                grid.place(actor, squad.location) # place actor "corpse" for future looting
                squad.remove_actor(actor)

            if not squad.actors:
                grid.remove(squad)

        left.in_combat = False
        right.in_combat = False

        return True


class MoveTask(Task):
    """Handles movement, duh"""

    def __init__(self, grid, squad, dest):
        self._steps = [self._run(grid, squad, dest)]

    async def _run(self, grid: MapGrid, squad: Squad, dest: tuple[int, int]):
        path = grid.create_astar_path(squad.location, dest, [])
        if path is None:
            return False

        grid.add_log_msg("MOVE", f"{squad.faction} squad({len(squad.actors)}) is moving to {dest}", squad.location)
        squad.has_task = True

        while path:
            next_square = path.pop(0)

            if not squad.actors:
                grid.remove(squad)
                break

            await asyncio.sleep(TRAVEL_DURATION)
            # interrupt movement for more important tasks
            if squad.in_combat or squad.is_looting:
                break

            grid.remove(squad)
            squad.location = next_square
            grid.place(squad, next_square)

            for actor in squad.actors:
                actor.location = next_square

        squad.has_task = False

        return True


class IdleTask(Task):
    """Handles waiting at the current location"""

    def __init__(self, grid, squad, duration):
        self._steps = [self._run(grid, squad, duration)]

    async def _run(self, grid: MapGrid, squad: Squad, duration: int):
        grid.add_log_msg("IDLE", f"{squad.faction} squad({len(squad.actors)}) is waiting for {duration} seconds", squad.location)
        squad.has_task = True
        await asyncio.sleep(duration)
        squad.has_task = False

        return True


class LootTask(Task):
    """Handles looting of bodies"""

    def __init__(self, grid, squad, actor):
        self._steps = [self._run(grid, squad, actor)]

    async def _run(self, grid: MapGrid, squad: Squad, actor: Actor):
        grid.add_log_msg("LOOT",
            f"{squad.faction.upper()} squad({len(squad.actors)}) is looting a {actor.faction} actor body...", actor.location
        )

        squad.is_looting = True
        actor.looted = True
        await asyncio.sleep(LOOT_DURATION)
        grid.remove(actor)
        squad.is_looting = False

        return True
