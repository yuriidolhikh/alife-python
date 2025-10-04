import asyncio
import os
import random

from library import MapGrid, CombatTask, IdleTask, MoveTask, LootTask, HuntArtifactsTask
from config import FACTIONS, SPAWN_FREQUENCY, MIN_FACTION_SQUADS, MAX_FACTION_SQUADS


async def main(loop, grid: MapGrid):
    tasks = []

    while True:
        grid.refresh()

        for square, entities in grid.get_grid().items():
            squadlist = entities[0]
            actorlist = entities[1]

            for index, squad in enumerate(squadlist):
                # Do some ghost-busting. Squads with no actors are considered dead and shouldn't be on the grid
                if not squad.actors:
                    grid.remove(squad, square)
                    continue

                # Seek nearby hostile squads
                j = index + 1
                while j < len(squadlist):
                    nxt = squadlist[j]
                    # not hostile to each other OR squad already dead OR is fighting someone else
                    if nxt.faction not in FACTIONS[squad.faction]["hostile"]\
                    or not nxt.actors\
                    or (squad.in_combat or nxt.in_combat):
                        j += 1
                        continue

                    # Set flags to prevent double-tasking
                    squad.in_combat = True
                    nxt.in_combat = True

                    tasks.append(loop.create_task(CombatTask(grid, squad, nxt).execute()))
                    break

                # Prevent looting mid-combat
                if squad.in_combat:
                    continue

                # Loot if there are bodies in the same square. Prevents movement
                if actorlist and FACTIONS[squad.faction]["can_loot"]:
                    max_lootable_corpses = min(len(actorlist), len(squad.actors))  # 1 guy loots 1 corpse at a time
                    for actor in filter(lambda x: not x.looted, actorlist[:max_lootable_corpses]):
                        tasks.append(loop.create_task(LootTask(grid, squad, actor).execute()))
                else:
                    # Can't task a squad already doing something else
                    if squad.is_busy():
                        continue

                    # These tasks are the same priority and can be randomly selected
                    # New task types can go here as well
                    new_task = random.choice([IdleTask, MoveTask, HuntArtifactsTask])
                    if new_task is HuntArtifactsTask and not FACTIONS[squad.faction]["can_hunt_artifacts"]:
                        continue

                    if new_task is HuntArtifactsTask:
                        print(f"{squad} assigned Hunt")

                    tasks.append(loop.create_task(new_task(grid, squad).execute()))

        _, running = await asyncio.wait(tasks, timeout=1)
        tasks = list(running)

        grid.cleanup()

if __name__ == "__main__":

    map_grid = MapGrid()
    map_grid.add_log_msg("INFO", " Starting simulation...")

    # Generate squads
    for f in FACTIONS:
        num_squads = random.randint(MIN_FACTION_SQUADS, MAX_FACTION_SQUADS)
        for _ in range(num_squads):
            map_grid.spawn(f)

    async def scheduled_spawner(grid: MapGrid):
        # Spawn a new random squad every X seconds
        while True:
            await asyncio.sleep(SPAWN_FREQUENCY)
            grid.spawn(random.choice(list(FACTIONS.keys())))

    if os.name == "nt":
        main_loop = asyncio.new_event_loop()
    else:
        import uvloop
        main_loop = uvloop.new_event_loop()

    main_loop.create_task(main(main_loop, map_grid))
    main_loop.create_task(scheduled_spawner(map_grid))
    main_loop.run_forever()
