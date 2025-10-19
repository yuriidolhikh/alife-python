from library import Actor


def test_actor_init():
    actor = Actor(faction="stalker", location=(0, 99), experience=100)
    assert actor.faction == "stalker", "Actor faction should be set correctly"
    assert actor.location == (0, 99), "Actor location should be set correctly"
    assert actor.loot_value is not None, "Actor should not be marked as looted"
    assert str(actor) == "Stalker actor (Rookie) at location (0, 99)", "Actor string should be correct"


def test_actor_update():
    actor = Actor(faction="stalker", location=(0, 99), experience=100)
    actor.loot_value = None
    actor.location = (55, 14)
    assert actor.faction == "stalker", "Actor faction should be set correctly"
    assert actor.location == (55, 14), "Actor location should be updated correctly"
    assert actor.loot_value is None, "Actor should be marked as looted"
    assert str(actor) == "Stalker actor (Rookie) at location (55, 14)", "Actor string should be correct"


def test_actor_exp_and_rank():
    actor = Actor(faction="stalker", location=(0, 99), experience=100)
    actor.gain_exp(2000)
    actor.rank_up()

    assert actor.rank == "Novice", "Actor should rank up according to current exp"

    actor.gain_exp(3000)
    actor.rank_up()

    assert actor.rank == "Experienced", "Actor should rank up according to current exp"

    actor.gain_exp(9999)
    actor.rank_up()

    assert actor.rank == "Legend", "Actor should rank up to 'legend' correctly"
