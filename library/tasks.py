import asyncio
import random

from typing import Awaitable

from .actor import Actor
from .grid import MapGrid
from .squad import Squad
from .types import Location

from config import COMBAT_DURATION, TRAVEL_DURATION, LOOT_DURATION, FACTIONS


class Task:
    """Base class for all tasks"""

    # steps of task execution
    # can chain multiple coroutines to create more complex tasks
    _steps: list[Awaitable[bool]]

    async def execute(self):
        res = []
        while self._steps:
            res.append(await self._steps.pop(0))

        return res


class CombatTask(Task):
    """Handles combat between two hostile squads"""

    def __init__(self, grid: MapGrid, left: Squad, right: Squad):
        self._steps = [self._run(grid, left, right)]

    async def _run(self, grid: MapGrid, left: Squad, right: Squad):

        await asyncio.sleep(COMBAT_DURATION)

        left_firepower = sum([a.experience for a in left.actors]) * FACTIONS[left.faction]["relative_firepower"]
        right_firepower = sum([a.experience for a in right.actors]) * FACTIONS[right.faction]["relative_firepower"]

        # determine "winning" squad, weighted by firepower.
        # More squad members with more experience + higher relative firepower = higher overall power
        winner = random.choices([left, right], weights=[left_firepower, right_firepower])[0]
        def biased_outcome(low, high, inverted=False):
            """Generate a random number of losses, with bias towards a specific end of the range"""
            bias = inverted and 1 - (random.random() ** 3.0) or random.random() ** 3.0
            return round(low + (high - low) * bias)

        for squad in (left, right):
            losses = biased_outcome(0, len(squad.actors), squad is not winner)

            msg = f"{squad.faction} squad({len(squad.actors)}) {losses and f"lost {losses} {losses > 1 and "men" or "man"}" or "took no casualties"} in combat"
            if losses == len(squad.actors):
                msg += " and was wiped out"

            grid.add_log_msg("COMBAT", msg, squad.location)

            for actor in squad.actors[:losses]:
                grid.place(actor, squad.location)  # place actor "corpse" for future looting
                squad.remove_actor(actor)

            if not squad.actors:
                grid.remove(squad)

        left.in_combat = False
        right.in_combat = False

        return ["combat", winner, True]


class MoveTask(Task):
    """Handles movement, duh"""

    def __init__(self, grid: MapGrid, squad: Squad, dest: Location):
        self._steps = [self._run(grid, squad, dest)]

    async def _run(self, grid: MapGrid, squad: Squad, dest: Location):
        if squad.location == dest:  # already there
            return ["move", squad, False]

        path = grid.pathfinder.create_path(squad.location, dest)
        if path is None:
            return ["move", squad, False]

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

        return ["move", squad, True]


class IdleTask(Task):
    """Handles waiting at the current location"""

    def __init__(self, grid: MapGrid, squad: Squad, duration: int):
        self._steps = [self._run(grid, squad, duration)]

    async def _run(self, grid: MapGrid, squad: Squad, duration: int):
        grid.add_log_msg("IDLE", f"{squad.faction} squad({len(squad.actors)}) is waiting for {duration} seconds", squad.location)
        squad.has_task = True
        await asyncio.sleep(duration)
        squad.has_task = False

        return ["idle", squad, False]


class LootTask(Task):
    """Handles looting of bodies"""

    def __init__(self, grid: MapGrid, squad: Squad, actor: Actor):
        self._steps = [self._run(grid, squad, actor)]

    async def _run(self, grid: MapGrid, squad: Squad, actor: Actor):
        msg = f"{squad.faction.upper()} squad({len(squad.actors)}) is looting a {actor.faction}"
        if actor.faction != "mutant":
            msg += f" actor ({actor.rank})"
        msg += " body..."

        grid.add_log_msg("LOOT", msg, actor.location)

        squad.is_looting = True
        actor.looted = True
        await asyncio.sleep(LOOT_DURATION)
        grid.remove(actor)
        squad.is_looting = False

        return ["loot", squad, False]
