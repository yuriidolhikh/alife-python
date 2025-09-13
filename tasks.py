import asyncio
import random

from classes import MapGrid, Squad, Actor
from config import COMBAT_DURATION, TRAVEL_DURATION, LOOT_DURATION


class CombatTask:
    """Handles combat between two hostile squads"""
    @staticmethod
    async def execute(grid: MapGrid, left: Squad, right: Squad):

        await asyncio.sleep(COMBAT_DURATION)

        for squad in (left, right):
            losses = random.randint(0, len(squad.actors))

            msg = f"{squad.faction} squad({len(squad.actors)}) {losses and f'lost {losses} {losses > 1 and "men" or "man"}' or 'took no casualtieS'} in combat"
            if losses == len(squad.actors):
                msg += " and was wiped out"

            grid.addLogMsg("COMBAT", msg, squad.location)

            for actor in squad.actors[:losses]:
                grid.place(actor, squad.location) # place actor "corpse" for future looting
                squad.removeActor(actor)

            if not squad.actors:
                grid.remove(squad)

        left.in_combat = False
        right.in_combat = False

        return True


class MoveTask:
    """Handles movement, duh"""
    @staticmethod
    async def execute(grid: MapGrid, squad: Squad, dest: tuple[str, int]):
        grid.addLogMsg("MOVE", f"{squad.faction} squad({len(squad.actors)}) is moving to {dest}", squad.location)

        path = grid.createPath(squad.location, dest)
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


class IdleTask:
    """Handles waiting at the current location"""
    @staticmethod
    async def execute(grid: MapGrid, squad: Squad, duration: int):
        grid.addLogMsg("IDLE", f"{squad.faction} squad({len(squad.actors)}) is waiting for {duration} seconds", squad.location)
        squad.has_task = True
        await asyncio.sleep(duration)
        squad.has_task = False

        return True


class LootTask:
    """Handles looting of bodies"""
    @staticmethod
    async def execute(grid: MapGrid, squad: Squad, actor: Actor):
        grid.addLogMsg("LOOT",
            f"{squad.faction.upper()} squad({len(squad.actors)}) is looting a {actor.faction} actor body...", actor.location
        )

        squad.is_looting = True
        actor.looted = True
        await asyncio.sleep(LOOT_DURATION)
        grid.remove(actor)
        squad.is_looting = False

        return True
