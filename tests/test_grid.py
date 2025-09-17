from mock import patch

from library import MapGrid, Squad


@patch('library.grid.SHOW_GRID', True)
def test_grid_logger(monkeypatch):
    grid = MapGrid()
    grid.add_log_msg("INFO", " test")

    assert len(grid._msg_log) == 1
    assert grid._msg_log.pop() == "[INFO] TEST"


def test_grid_spawner():
    grid = MapGrid()
    grid.spawn("test_faction", (5, 33))

    grid_dict = grid.get_grid()
    assert len(grid_dict.keys()) == 1
    assert (5, 33) in grid_dict

    entities = grid_dict[(5, 33)]
    assert len(entities[0]) == 1

    squad = entities[0][0]
    assert isinstance(squad, Squad)
    assert squad.faction == "test_faction"
    assert squad.location == (5, 33)


def test_grid_remove():
    grid = MapGrid()
    grid.spawn("test_faction", (4, 22))

    grid_dict = grid.get_grid()

    squad = grid_dict[(4, 22)][0][0]
    grid.remove(squad)
    grid.cleanup()

    assert (4, 22) not in grid_dict


def test_grid_place():
    grid = MapGrid()
    squad = Squad(faction="stalker", location=(0, 0))
    grid.place(squad, (3, 26))
    grid_dict = grid.get_grid()

    assert (3, 26) in grid_dict
    assert grid_dict[(3, 26)][0][0] is squad
