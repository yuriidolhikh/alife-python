from library import Squad, Actor


def test_squad_init():
    squad = Squad(faction="test_faction", location=(0, 55))

    assert squad.faction == "test_faction"
    assert squad.location == (0, 55)
    assert not squad.actors
    assert not squad.has_task
    assert not squad.in_combat
    assert not squad.is_looting
    assert not squad.is_busy()
    assert str(squad) == "Test_faction squad (0 actors) at location (0, 55)"


def test_squad_update():
    squad = Squad(faction="stalker", location=(2, 25))
    actor = Actor("stalker", (2, 25))

    squad.add_actor(actor)
    squad.has_task = True
    squad.location = (5, 56)

    assert squad.has_task
    assert squad.actors
    assert squad.actors == [actor]
    assert squad.location == (5, 56)

    squad.remove_actor(actor)
    assert not squad.actors
