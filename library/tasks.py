import asyncio
import random

from typing import Awaitable, Optional

from .actor import Actor
from .grid import MapGrid
from .squad import Squad
from .types import Location

from config import GRID_X_SIZE, GRID_Y_SIZE
from config import (COMBAT_DURATION, MIN_IDLE_DURATION, MAX_IDLE_DURATION, TRADE_DURATION,
                    TRAVEL_DURATION, LOOT_DURATION, ARTIFACT_HUNT_DURATION, FACTIONS)


class Task:
    """Base class for all tasks"""

    _steps: list[Awaitable]  # can chain multiple steps to create more complex tasks

    async def execute(self):
        res = []
        while self._steps:
            res.append(await self._steps.pop(0))

        return res

    def get_steps(self):
        return self._steps

    def award_exp(self, squad: Squad):
        """Award exp for task completion"""
        if FACTIONS[squad.faction]["can_gain_exp"]:
            for actor in squad.actors:
                actor.gain_exp(random.randint(100, 300))
                actor.rank_up()

        return True


class CombatTask(Task):
    """Handles combat between two hostile squads"""

    def __init__(self, grid: MapGrid, left: Squad, right: Squad):
        self._steps = [self._run(grid, left, right)]

    async def _run(self, grid: MapGrid, left: Squad, right: Squad):

        left_firepower = sum([a.experience for a in left.actors]) * FACTIONS[left.faction]["relative_firepower"]
        right_firepower = sum([a.experience for a in right.actors]) * FACTIONS[right.faction]["relative_firepower"]

        # determine "winning" squad, weighted by firepower.
        # More squad members with more experience + higher relative firepower = higher overall power
        winner = random.choices([left, right], weights=[left_firepower, right_firepower])[0]

        def biased_outcome(low, high, inverted=False):
            """Generate a random number of losses, with bias towards a specific end of the range"""
            bias = inverted and 1 - (random.random() ** 3.0) or random.random() ** 3.0
            return round(low + (high - low) * bias)

        await asyncio.sleep(COMBAT_DURATION)

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

        self.award_exp(winner)

        return True


class MoveTask(Task):
    """Handles movement, duh"""

    def __init__(self, grid: MapGrid, squad: Squad, dest: Optional[Location] = None):
        # generate random destination if it was not specified
        if dest is None:
            while (dest := (random.randint(0, GRID_X_SIZE - 1), random.randint(0, GRID_Y_SIZE - 1))) in grid.get_obstacles(): pass

        self._steps = [self._run(grid, squad, dest)]

    async def _run(self, grid: MapGrid, squad: Squad, dest: Location):

        if squad.location == dest:  # already there
            return True

        path = grid.pathfinder.create_path(squad.location, dest)
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
        self.award_exp(squad)

        return True


class HuntArtifactsTask(Task):
    """Handles artifact hunts"""

    def __init__(self, grid: MapGrid, squad: Squad):
        closest_field = grid.get_closest_of_type("fields", squad.location)
        if closest_field:
            steps = MoveTask(grid, squad, closest_field).get_steps()
            steps.append(self._run(grid, squad))
            self._steps = steps
        else:
            self._steps = []  # map does not support artifact fields

    async def _run(self, grid: MapGrid, squad: Squad):
        grid.add_log_msg("HUNT", f"{squad.faction} squad is hunting for artifacts", squad.location)

        squad.has_task = True
        await asyncio.sleep(ARTIFACT_HUNT_DURATION)

        losses = random.randint(0, len(squad.actors) // 2)
        if losses:
            grid.add_log_msg("HUNT",
             f"{squad.faction} squad({len(squad.actors)}) has lost {losses} {losses > 1 and "men" or "man"} while hunting for artifacts",
             squad.location)

            for actor in squad.actors[:losses]:
                grid.place(actor, squad.location)
                squad.remove_actor(actor)

        squad.loot_value += random.randint(100, 500)

        self.award_exp(squad)
        squad.has_task = False

        return True


class TradeTask(Task):
    """Handles loot selling"""

    def __init__(self, grid: MapGrid, squad: Squad):
        closest_trader = grid.get_closest_of_type("traders", squad.location)
        if closest_trader:
            steps = MoveTask(grid, squad, closest_trader).get_steps()
            steps.append(self._run(grid, squad))
            self._steps = steps
        else:
            self._steps = []  # map does not support traders

    async def _run(self, grid: MapGrid, squad: Squad):

        squad.has_task = True
        while squad.loot_value:
            grid.add_log_msg("TRADE", f"{squad.faction} squad is selling habar", squad.location)
            squad.loot_value -= min(500, squad.loot_value)
            await asyncio.sleep(TRADE_DURATION)

        squad.has_task = False

        return True


class IdleTask(Task):
    """Handles waiting at the current location"""

    def __init__(self, grid: MapGrid, squad: Squad, duration: Optional[int] = None):
        if duration is None:
            duration = random.randint(MIN_IDLE_DURATION, MAX_IDLE_DURATION)

        self._steps = [self._run(grid, squad, duration)]

    async def _run(self, grid: MapGrid, squad: Squad, duration: int):
        grid.add_log_msg("IDLE", f"{squad.faction} squad({len(squad.actors)}) is waiting for {duration} seconds", squad.location)
        squad.has_task = True
        await asyncio.sleep(duration)
        squad.has_task = False

        return True


class LootTask(Task):
    """Handles looting of bodies"""

    def __init__(self, grid: MapGrid, squad: Squad, actor: Actor):
        self._steps = [self._run(grid, squad, actor)]

    async def _run(self, grid: MapGrid, squad: Squad, actor: Actor):
        # offset looted value by actor experience, so higher exp = more valuable loot

        msg = f"{squad.faction.upper()} squad({len(squad.actors)}) is looting a {actor.faction}"
        if actor.faction != "mutant":
            msg += f" actor ({actor.rank})"
        msg += " body..."

        grid.add_log_msg("LOOT", msg, actor.location)

        squad.is_looting = True
        actor.looted = True
        await asyncio.sleep(LOOT_DURATION)
        grid.remove(actor)

        squad.loot_value += round(random.randint(10, 50) * (actor.experience / 1000))
        squad.is_looting = False

        return True
