import uuid

from library import Squad, Actor


def test_squad_init(monkeypatch):
    monkeypatch.setattr('uuid.uuid4', lambda: uuid.UUID("6148b8ca-a130-11f0-b311-8c859097fb57"))
    squad = Squad(faction="test_faction", location=(0, 55))

    assert squad.faction == "test_faction", "Squad faction should be correct"
    assert squad.location == (0, 55), "Squad location should be correct"
    assert not squad.actors, "Squad should not have actors"
    assert not squad.has_task, "Squad should not have tasks"
    assert not squad.in_combat, "Squad should not be in combat"
    assert not squad.is_looting, "Squad should not be looting"
    assert not squad.is_busy(), "Squad should not be busy"
    assert str(squad) == "Test_faction squad(SID=8c859097fb57) (0 actors)", "Squad string should be correct"


def test_squad_update():
    squad = Squad(faction="stalker", location=(2, 25))
    actor = Actor("stalker", (2, 25))

    squad.add_actor(actor)
    squad.has_task = True
    squad.location = (5, 56)

    assert squad.has_task, "Squad should have task"
    assert squad.actors, "Squad should have actors"
    assert squad.actors == [actor], "Squad actors should contain correct objects"
    assert squad.location == (5, 56), "Squad location should be correct"

    squad.remove_actor(actor)
    assert not squad.actors, "Squad should not have actors after removal"
