import pytest

from library import CombatTask, IdleTask, MoveTask, LootTask, MapGrid, Actor, Squad


@pytest.mark.asyncio
async def test_combat_task(monkeypatch):
    grid = MapGrid()

    squad1 = Squad("stalker", (1, 1))
    squad1.add_actor(Actor("stalker", (1, 1)))
    squad1.add_actor(Actor("stalker", (1, 1)))
    grid.place(squad1, (1, 1))

    squad2 = Squad("monolith", (1, 1))
    squad2.add_actor(Actor("monolith", (1, 1)))
    squad2.add_actor(Actor("monolith", (1, 1)))
    grid.place(squad2, (1, 1))

    monkeypatch.setattr('library.tasks.COMBAT_DURATION', 0)
    monkeypatch.setattr('random.choices', lambda *args, **kwargs: [squad2])
    monkeypatch.setattr('random.random', lambda: 0.5)

    await CombatTask(grid, squad1, squad2).execute()
    assert not squad1.actors, "squad1 should not have alive actors"
    assert not squad1.in_combat, "squad1 should not be in combat"

    assert len(squad2.actors) == 2, "squad2 should not have alive actors"
    assert not squad2.in_combat, "squad2 should not be in combat"

    squads, actors = grid.get_grid()[(1, 1)]

    assert len(squads) == 1, "Actorless squads should not be on the map"
    assert len(actors) == 2, "CombatTask should produce exactly 2 lootable bodies"

    for actor in actors:
        assert not actor.looted, "Actor should not be looted"


@pytest.mark.asyncio
async def test_move_task(monkeypatch):
    grid = MapGrid()
    squad = Squad("stalker", (0, 0))
    squad.add_actor(Actor("stalker", (0, 0)))

    monkeypatch.setattr('library.tasks.TRAVEL_DURATION', 0)
    monkeypatch.setattr('library.pathfinder.PATHFINDING_MODE', 'simple')

    await MoveTask(grid, squad, (5, 5)).execute()

    assert not grid.get_grid()[(1, 1)][0], "Squad should be removed from the original square"
    assert squad.location == (5, 5), "Squad should move to expected location"
    assert squad.actors[0].location == (5, 5), "Squad actors should move to expected location"
    assert squad.has_task is False, "Squad should mark task as complete"

    assert grid.get_grid()[(5, 5)][0][0] is squad, "Squad should be placed on the destination square"


@pytest.mark.asyncio
async def test_idle_task():
    grid = MapGrid()
    squad = Squad("test_faction", (0, 0))

    await IdleTask(grid, squad, 0).execute()
    assert squad.has_task is False, "Squad should mark task as complete"


@pytest.mark.asyncio
async def test_loot_task(monkeypatch):
    grid = MapGrid()

    squad = Squad("stalker", (1, 1))
    squad.add_actor(Actor("stalker", (1, 1)))

    lootable = Actor("ward", (1, 1))
    grid.place(lootable, (1, 1))

    monkeypatch.setattr('library.tasks.LOOT_DURATION', 0)
    await LootTask(grid, squad, lootable).execute()

    assert squad.is_looting is False, "Squad should not be marked as looting"
    assert lootable.looted, "Actor should be marked as looted"

    assert len(grid.get_grid()[(1, 1)][1]) == 0, "Looted actor should be removed from the grid"
