import heapq
import random
import os
import string

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from colorama import Fore, Style, just_fix_windows_console

from config import MAX_NUM_MESSAGES, GRID_X_SIZE, GRID_Y_SIZE, SHOW_GRID


@dataclass
class Actor:
    """Individual actor on the grid"""
    faction: str
    location: tuple
    looted: bool = False

    def __str__(self):
        return f"{self.faction.capitalize()} actor at location {self.location}"


@dataclass
class Squad:
    """Squad on the grid, made up of multiple actors. Executes tasks"""
    faction: str
    location: tuple[int, int]
    actors: list = field(default_factory=list) # list of actors in the squad
    has_task: bool = False
    in_combat: bool = False
    is_looting: bool = False

    def __str__(self):
        return f"{self.faction.upper()} squad ({len(self.actors)} actors) at location {self.location}"

    def is_busy(self):
        return self.in_combat or self.is_looting or self.has_task

    def add_actor(self, actor: Actor):
        self.actors.append(actor)

    def remove_actor(self, actor: Actor):
        try:
            index = self.actors.index(actor)
        except ValueError:
            return False

        del self.actors[index]

        return True


class MapGrid:
    """Defines the map and contains all map-related function"""

    def __init__(self):
        self._grid = {}
        self._msg_log = deque([], maxlen=MAX_NUM_MESSAGES)
        self._squares_to_delete = set()

        # Fix colored display on Windows
        just_fix_windows_console()

    def get_grid(self):
        return self._grid

    def draw(self):
        """Draw current grid state in console"""

        # Extract row/column labels
        cols = [i for i in range(GRID_X_SIZE)]
        rows = [i for i in range(GRID_Y_SIZE)]

        # Print column headers
        header = "     " + "  ".join(f"{col:^5}" for col in cols)
        print(header)
        print("   " + "-" * (len(cols) * 7))

        # Print rows
        for r in rows:
            row_str = f"{r:>2} |"
            for c in cols:
                cell = self._grid.get((c, r), ([], []))
                if cell[0]:
                    content = ",".join(f"{x.faction[0:2].capitalize()}({len(x.actors)})" for x in cell[0])
                elif cell[1]:
                    content = "x"
                else:
                    content = ""
                row_str += f"{content:^7}"

            print(row_str)

        # Draw log section
        print()
        for entry in self._msg_log:
            print(entry)

        return True

    def refresh(self):
        """Redraw the grid in the terminal"""
        if not SHOW_GRID:
            return False

        os.system("cls" if os.name == "nt" else "printf '\033c\033[3J'")
        self.draw()

    def add_log_msg(self, msg_type: str, message: str, square: Optional[tuple[int, int]] = None):
        """Logging helper"""

        if msg_type == "COMBAT":
            logged_msg = f"{Fore.RED}[COMBAT]{Style.RESET_ALL}"
        elif msg_type == "LOOT":
            logged_msg = f"{Fore.YELLOW}[LOOT]{Style.RESET_ALL}"
        elif msg_type == "MOVE":
            logged_msg = f"{Fore.GREEN}[MOVE]{Style.RESET_ALL}"
        elif msg_type == "IDLE":
            logged_msg = f"{Fore.CYAN}[IDLE]{Style.RESET_ALL}"
        else:
            logged_msg = "[INFO]"

        if square:
            logged_msg += f"[SQUARE={square}] "

        logged_msg += message.upper()

        if SHOW_GRID:
            self._msg_log.append(logged_msg)
        else:
            print(logged_msg)

        return True

    def spawn(self, faction: str):
        """Spawn random faction squad on the map"""

        num_actors = random.randint(1, 5)
        location = (random.randint(0, GRID_X_SIZE - 1), random.randint(0, GRID_Y_SIZE - 1))

        # avoid spawning on top of existing squads
        while location in self._grid:
            location = (random.randint(0, GRID_X_SIZE - 1), random.randint(0, GRID_Y_SIZE - 1))

        squad = Squad(faction, location)
        # Generate actors
        for _ in range(num_actors):
            squad.add_actor(Actor(faction, location))

        self.place(squad, location)
        self.add_log_msg("INFO", f"Spawned a new {num_actors}-actor {faction.upper()} squad", location)

        return True

    def create_simple_path(self, start: tuple[int, int], dest: tuple[int, int]):
        """
        Create a path from start to dest moving 1 step at a time.
        Each step can be diagonal, vertical, or horizontal.
        Grid rows start at 0, so top-left is ('A', 0).
        """
        col_s, row_s = start
        col_d, row_d = dest

        x, y = col_s, row_s
        x_end, y_end = col_d, row_d

        path = []

        while (x, y) != (x_end, y_end):
            if x < x_end:
                x += 1
            elif x > x_end:
                x -= 1

            if y < y_end:
                y += 1
            elif y > y_end:
                y -= 1

            path.append((x, y))

        return path

    def create_astar_path(self, start: tuple[int, int], goal: tuple[int, int], obstacles: list[tuple[int, int]]):
        """
        A* pathfinding on a 2D grid with 8-direction movement
        and uniform cost for all moves (diagonals cost the same as straight).

        :param start: (x, y) tuple for the starting point
        :param goal: (x, y) tuple for the goal point
        :param obstacles: list of (x, y) tuples representing blocked cells
        :return: list of (x, y) tuples representing the path, or None if no path
        """
        # 8 directions: N, NE, E, SE, S, SW, W, NW
        neighbors = [
            (0, 1), (1, 1), (1, 0), (1, -1),
            (0, -1), (-1, -1), (-1, 0), (-1, 1)
        ]
        obstacle_set = set(obstacles)

        def heuristic(a, b):
            # Chebyshev distance is ideal for 8-way movement with equal costs
            return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

        def in_bounds(p):
            return 0 <= p[0] < GRID_X_SIZE and 0 <= p[1] < GRID_Y_SIZE

        open_set = []
        heapq.heappush(open_set, (heuristic(start, goal), 0, start))
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current_g, current = heapq.heappop(open_set)

            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]

                return path[::-1]

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                if not in_bounds(neighbor) or neighbor in obstacle_set:
                    continue
                # All moves cost 1
                tentative_g = current_g + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        return None  # No path found

    def remove(self, entity: type[Actor | Squad], square: Optional[tuple[int, int]] = None):
        """Remove actor or squad from the grid. If grid square is not provided - attempt to get location from the entity"""
        index = 0 if isinstance(entity, Squad) else 1
        try:
            location = square if square is not None else entity.location
            del self._grid[location][index][self._grid[location][index].index(entity)]
        except (KeyError, ValueError):
            return False

        # Query empty square cleanup
        if not list(filter(bool, self._grid[location])):
            self._squares_to_delete.add(location)

        return True

    def place(self, entity: type[Actor | Squad], square: tuple[int, int]):
        """Place actor or squad on the grid square"""
        index = 0 if isinstance(entity, Squad) else 1
        if square not in self._grid:
            self._grid[square] = [[], []]

        self._grid[square][index].append(entity)

        return True

    def cleanup(self):
        """Clean up empty squares. On larger grids they take up a lot of memory"""
        for square in self._squares_to_delete:
            del self._grid[square]

        self._squares_to_delete = set()

        return True
