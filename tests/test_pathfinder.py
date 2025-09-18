import pytest

from library import Pathfinder


@pytest.fixture
def pathfinder(monkeypatch):
    monkeypatch.setattr('library.pathfinder.GRID_X_SIZE', 10)
    monkeypatch.setattr('library.pathfinder.GRID_Y_SIZE', 10)
    monkeypatch.setattr('library.pathfinder.CLUSTER_SIZE', 2)
    monkeypatch.setattr('library.pathfinder.PATHFINDING_MODE', 'hpa')

    return Pathfinder()


def test_create_simple_path(pathfinder):
    path = pathfinder.create_simple_path((0, 0), (9, 9))
    assert path == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9)], "Simple path should be correct"

    path = pathfinder.create_simple_path((2, 1), (5, 7))
    assert path == [(3, 2), (4, 3), (5, 4), (5, 5), (5, 6), (5, 7)], "Simple path with non-diagonal moves should be correct"


def test_create_astar_path(pathfinder):
    path = pathfinder.create_astar_path((0, 0), (9, 9), {(0, 5), (5, 10), (9, 10)})
    assert path == [(0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (1, 5), (1, 6), (1, 7),
                    (1, 8), (1, 9), (2, 9), (3, 9), (4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (9, 9)], "A* path should be correct"

    path = pathfinder.create_astar_path((0, 0), (10, 10), {(i, 5) for i in range(10)})
    assert path is None, "A* result should be empty if there's no path"


def test_create_8way_astar_path(pathfinder):
    path = pathfinder.create_8way_astar_path((0, 0), (9, 9), {(5, 5), (6, 6), (8, 8)})
    assert path == [(1, 1), (2, 2), (3, 3), (4, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 9)], "8-way A* path should be correct"

    path = pathfinder.create_astar_path((0, 0), (10, 10), {(i, 5) for i in range(10)})
    assert path is None, "8-way A* result should be empty if there's no path"


def test_create_hpa_path(pathfinder):
    path = pathfinder.create_hpa_path((0, 0), (9, 9), {(5, 5), (6, 6), (8, 8)})
    assert path == [(1, 1), (2, 2), (3, 3), (4, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 9)], "HPA path should be correct"

    path = pathfinder.create_hpa_path((0, 0), (10, 10), {(i, 5) for i in range(10)})
    assert path is None, "HPA result should be empty if there's no path"
