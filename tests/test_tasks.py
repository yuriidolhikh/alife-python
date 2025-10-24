import pytest

from library import CombatTask, IdleTask, MoveTask, LootTask, HuntArtifactsTask, TradeTask, HuntSquadTask, MapGrid, Actor, Squad


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

    monkeypatch.setattr('config.COMBAT_DURATION', 0)
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
        assert actor.loot_value is not None, "Actor should not be looted"


@pytest.mark.asyncio
async def test_move_task(monkeypatch):
    grid = MapGrid()
    squad = Squad("stalker", (0, 0))
    squad.add_actor(Actor("stalker", (0, 0)))

    monkeypatch.setattr('config.TRAVEL_DURATION', 0)
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
async def test_hunt_artifacts_task(monkeypatch):
    grid = MapGrid()
    grid._area_map["fields"].extend([(1, 1), (4, 4)])

    monkeypatch.setattr('config.TRAVEL_DURATION', 0)
    monkeypatch.setattr('config.ARTIFACT_HUNT_DURATION', 0)
    monkeypatch.setattr('library.pathfinder.PATHFINDING_MODE', 'simple')

    squad = Squad("stalker", (0, 0))
    squad.add_actor(Actor("stalker", (0, 0)))

    actor_exp_before = squad.actors[0].experience

    await HuntArtifactsTask(grid, squad).execute()

    assert squad.location == (1, 1), "Squad should move to the nearest artifact field"
    assert squad.actors[0].location == (1, 1), "Squad actors should move to the nearest field"
    assert squad.actors[0].experience > actor_exp_before, "Task should award experience"
    assert squad.has_task is False, "Squad should mark task as complete"


@pytest.mark.asyncio
async def test_trade_task(monkeypatch):
    grid = MapGrid()
    grid._area_map["traders"].extend([(1, 1), (4, 4)])

    monkeypatch.setattr('config.TRAVEL_DURATION', 0)
    monkeypatch.setattr('config.TRADE_DURATION', 0)
    monkeypatch.setattr('library.pathfinder.PATHFINDING_MODE', 'simple')

    squad = Squad("stalker", (0, 0))
    squad.add_actor(Actor("stalker", (0, 0)))

    prev_total = sum(a.loot_value for a in squad.actors)

    await TradeTask(grid, squad).execute()

    assert squad.location == (1, 1), "Squad should move to the nearest trader"
    assert squad.actors[0].location == (1, 1), "Squad actors should move to the trader"
    assert sum(a.loot_value for a in squad.actors) < prev_total, "Loot should be sold"
    assert squad.has_task is False, "Squad should mark task as complete"


@pytest.mark.asyncio
async def test_loot_task(monkeypatch):
    grid = MapGrid()

    squad = Squad("stalker", (1, 1))
    squad.add_actor(Actor("stalker", (1, 1)))

    lootable = Actor("ward", (1, 1))
    lootable_value = lootable.loot_value
    prev_actor_value = squad.actors[0].loot_value

    grid.place(lootable, (1, 1))

    monkeypatch.setattr('config.LOOT_DURATION', 0)
    await LootTask(grid, squad, lootable).execute()

    assert squad.is_looting is False, "Squad should not be marked as looting"
    assert lootable.loot_value is None, "Actor should be marked as looted"
    assert squad.actors[0].loot_value == (prev_actor_value + lootable_value), "Actor's loot value should increase"

    assert len(grid.get_grid()[(1, 1)][1]) == 0, "Looted actor should be removed from the grid"


@pytest.mark.asyncio
async def test_hunt_squad_task(monkeypatch):
    grid = MapGrid()

    squad1 = Squad("stalker", (0, 0))
    squad1.add_actor(Actor("stalker", (0, 0)))
    grid.place(squad1, (0, 0))

    squad2 = Squad("monolith", (2, 2))
    squad2.add_actor(Actor("monolith", (2, 2)))
    grid.place(squad2, (2, 2))

    squad3 = Squad("monolith", (5, 8))
    squad3.add_actor(Actor("monolith", (5, 8)))
    grid.place(squad3, (5, 8))

    monkeypatch.setattr('config.TRAVEL_DURATION', 0)
    monkeypatch.setattr('library.pathfinder.PATHFINDING_MODE', 'simple')

    await HuntSquadTask(grid, squad1).execute()

    assert squad1.location == (2, 2), "Squad should move to correct target position"
    assert squad1.is_busy() is False, "Squad should unset 'busy' flag after finding the target"
