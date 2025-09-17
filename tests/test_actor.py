from library import Actor


def test_actor_init():
    actor = Actor(faction="test_faction", location=(0, 99))
    assert actor.faction == "test_faction"
    assert actor.location == (0, 99)
    assert not actor.looted
    assert str(actor) == "Test_faction actor at location (0, 99)"


def test_actor_update():
    actor = Actor(faction="test_faction", location=(0, 99))
    actor.looted = True
    actor.location = (55, 14)
    assert actor.faction == "test_faction"
    assert actor.location == (55, 14)
    assert actor.looted
    assert str(actor) == "Test_faction actor at location (55, 14)"
