from library import Actor


def test_actor_init():
    actor = Actor(faction="test_faction", location=(0, 99))
    assert actor.faction == "test_faction", "Actor faction should be set correctly"
    assert actor.location == (0, 99), "Actor location should be set correctly"
    assert not actor.looted, "Actor should not be marked as looted"
    assert str(actor) == "Test_faction actor at location (0, 99)", "Actor string should be correct"


def test_actor_update():
    actor = Actor(faction="test_faction", location=(0, 99))
    actor.looted = True
    actor.location = (55, 14)
    assert actor.faction == "test_faction", "Actor faction should be set correctly"
    assert actor.location == (55, 14), "Actor location should be updated correctly"
    assert actor.looted, "Actor should be marked as looted"
    assert str(actor) == "Test_faction actor at location (55, 14)", "Actor string should be correct"
