from library import MapGrid, Squad


def test_grid_logger(monkeypatch):
    monkeypatch.setattr('library.grid.SHOW_GRID', True)

    grid = MapGrid()
    grid.add_log_msg("INFO", " test")

    assert len(grid._msg_log) == 1, "Message should be added to the message log"
    assert grid._msg_log.pop() == "[INFO] TEST", "Message in the log should be correctly formatted"


def test_grid_spawner():
    grid = MapGrid()
    grid.spawn("stalker", (5, 33))

    grid_dict = grid.get_grid()
    assert len(grid_dict.keys()) == 1, "Only one square should be populated"
    assert (5, 33) in grid_dict, "Entity should be spawned at the expected square"

    entities = grid_dict[(5, 33)]
    assert len(entities[0]) == 1, "Only one entity should spawn"

    squad = entities[0][0]
    assert isinstance(squad, Squad), "Should be correct entity object"
    assert squad.faction == "stalker", "Entity should have correct faction set"
    assert squad.location == (5, 33), "Entity should have correct location set"


def test_grid_remove():
    grid = MapGrid()
    grid.spawn("stalker", (4, 22))

    grid_dict = grid.get_grid()

    squad = grid_dict[(4, 22)][0][0]
    grid.remove(squad)
    grid.cleanup()

    assert (4, 22) not in grid_dict, "Square should be removed from the grid"


def test_grid_place():
    grid = MapGrid()
    squad = Squad(faction="stalker", location=(0, 0))
    grid.place(squad, (3, 26))
    grid_dict = grid.get_grid()

    assert (3, 26) in grid_dict, "Square should be added to the grid"
    assert grid_dict[(3, 26)][0][0] is squad, "Square should contain correct entity"
