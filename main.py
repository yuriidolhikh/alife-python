import asyncio
import os
import random

from library import MapGrid, CombatTask, IdleTask, MoveTask, LootTask
from config import (FACTIONS, SPAWN_FREQUENCY, MIN_IDLE_DURATION,
                    MAX_IDLE_DURATION, MIN_FACTION_SQUADS, MAX_FACTION_SQUADS,
                    GRID_Y_SIZE, GRID_X_SIZE)


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
                    task = random.choice([IdleTask, MoveTask])
                    if task is IdleTask:
                        duration = random.randint(MIN_IDLE_DURATION, MAX_IDLE_DURATION)
                        tasks.append(loop.create_task(IdleTask(grid, squad, duration).execute()))
                    else:
                        while (dest := (random.randint(0, GRID_X_SIZE - 1), random.randint(0, GRID_Y_SIZE - 1))) in grid.get_obstacles(): pass
                        tasks.append(loop.create_task(MoveTask(grid, squad, dest).execute()))

        complete, running = await asyncio.wait(tasks, timeout=1)
        tasks = list(running)

        # Award task exp to eligible squads
        for task in complete:
            for item in task.result():
                _, squad, exp_eligible = item
                if FACTIONS[squad.faction]["can_gain_exp"] and exp_eligible:
                    for actor in squad.actors:
                        actor.gain_exp(random.randint(100, 300))
                        actor.rank_up()

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
