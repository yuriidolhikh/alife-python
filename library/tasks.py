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


async def move_to(grid: MapGrid, squad: Squad, dest: Location):
    """Helper method to handle square-by-square movement"""

    if not squad.actors:
        grid.remove(squad)
        return False

    await asyncio.sleep(TRAVEL_DURATION)
    # interrupt movement for more important tasks
    if squad.in_combat or squad.is_looting:
        return False

    grid.remove(squad)
    squad.location = dest
    grid.place(squad, dest)

    for actor in squad.actors:
        actor.location = dest

    return True


class Task:
    """Base class for all tasks"""

    _steps: list[Awaitable]  # can chain multiple steps to create more complex tasks

    async def execute(self):
        """Execute steps in order and aggregate results"""
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
            losses = biased_outcome(0, squad.num_actors(), squad is not winner)

            msg = f"{squad} {losses and f"lost {losses} {losses > 1 and "men" or "man"}" or "took no casualties"} in combat"
            if losses == squad.num_actors():
                msg += " and was wiped out"

            grid.add_log_msg("CMBT", msg, squad.location)

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

        grid.add_log_msg("MOVE", f"{squad} is moving to {dest}", squad.location)
        squad.has_task = True

        while path:
            next_square = path.pop(0)
            res = await move_to(grid, squad, next_square)

            if not res:
                break

        squad.has_task = False
        self.award_exp(squad)

        return True


class HuntArtifactsTask(Task):
    """Handles artifact hunts"""

    def __init__(self, grid: MapGrid, squad: Squad):
        closest_field = grid.get_closest_of_type("fields", squad.location)
        if closest_field:
            grid.add_log_msg("ARTI", f"{squad} is moving to artifact field at {closest_field}", squad.location)
            steps = MoveTask(grid, squad, closest_field).get_steps()
            steps.append(self._run(grid, squad))
            self._steps = steps
        else:
            self._steps = []  # map does not support artifact fields

    async def _run(self, grid: MapGrid, squad: Squad):
        grid.add_log_msg("ARTI", f"{squad} is hunting for artifacts", squad.location)

        squad.has_task = True
        await asyncio.sleep(ARTIFACT_HUNT_DURATION)

        if squad.in_combat:
            return False

        losses = random.randint(0, squad.num_actors() // 2)
        if losses:
            grid.add_log_msg("ARTI",
             f"{squad} has lost {losses} {losses > 1 and "men" or "man"} while hunting for artifacts",
             squad.location)

            for actor in squad.actors[:losses]:
                grid.place(actor, squad.location)
                squad.remove_actor(actor)

        random.choice(squad.actors).loot_value += random.randint(100, 500)

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
        grid.add_log_msg("TRDE", f"{squad} is selling habar", squad.location)

        for actor in squad.actors:
            actor.loot_value //= 2  # "sell" half of loot

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
        grid.add_log_msg("IDLE", f"{squad} is waiting for {duration} seconds", squad.location)
        squad.has_task = True
        await asyncio.sleep(duration)
        squad.has_task = False

        return True


class LootTask(Task):
    """Handles looting of bodies"""

    def __init__(self, grid: MapGrid, squad: Squad, actor: Actor):
        self._steps = [self._run(grid, squad, actor)]

    async def _run(self, grid: MapGrid, squad: Squad, actor: Actor):
        if actor.loot_value is None:
            return False  # already looted

        msg = f"{squad} is looting a {actor.faction}"
        if actor.faction != "mutant":
            msg += f" actor (rank={actor.rank}; loot_value={actor.loot_value})"
        msg += " body..."

        grid.add_log_msg("LOOT", msg, actor.location)

        squad.is_looting = True

        actor_loot_value = actor.loot_value
        actor.loot_value = None

        await asyncio.sleep(LOOT_DURATION)
        grid.remove(actor)

        random.choice(squad.actors).loot_value += actor_loot_value  # award loot to a random actor in a squad

        squad.is_looting = False

        return True


class HuntSquadTask(Task):
    """Hunt another squad for bounty"""

    def __init__(self, grid: MapGrid, squad: Squad):
        target = grid.get_squad_in_vicinity(squad.location, FACTIONS[squad.faction]["hostile"], max_actors=squad.num_actors())

        if target:
            grid.add_log_msg("HUNT", f"{squad} is hunting {target} at {target.location}", squad.location)
            self._steps = [self._run(grid, squad, target)]
        else:
            self._steps = []

    async def _run(self, grid: MapGrid, squad: Squad, target: Squad):
        path = grid.pathfinder.create_path(squad.location, target.location)

        squad.has_task = True
        old_location = target.location

        while squad.location != target.location and path:
            next_square = path.pop(0)
            await move_to(grid, squad, next_square)

            # target has moved
            if target.location != old_location:
                old_location = target.location
                path = grid.pathfinder.create_path(squad.location, target.location)

        grid.add_log_msg("HUNT", f"{squad} has found it's target", squad.location)

        self.award_exp(squad)
        squad.has_task = False

        return True

