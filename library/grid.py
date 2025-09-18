import os
import pickle
import random

from collections import deque, defaultdict
from colorama import Fore, Style, just_fix_windows_console
from typing import Optional

from .actor import Actor
from .squad import Squad
from .pathfinder import Pathfinder

from config import MAX_NUM_MESSAGES, SHOW_GRID, GRID_X_SIZE, GRID_Y_SIZE, MAP

type Location = tuple[int, int]


class MapGrid:
    """Defines the map and contains all map-related function"""

    def __init__(self):
        self._grid = defaultdict(lambda: ([], []))
        self._msg_log = deque([], maxlen=MAX_NUM_MESSAGES)
        self._squares_to_delete = set()

        dirname = os.path.dirname(__file__)
        mapfile = os.path.join(dirname, f'../maps/{MAP}')

        with open(mapfile, 'rb') as f:
            obstacles = pickle.load(f)
            self._obstacles = obstacles

        self.pathfinder = Pathfinder(obstacles)

        # Fix colored display on Windows
        just_fix_windows_console()

    def get_grid(self):
        return self._grid

    def draw(self):
        """Draw current grid state in console"""

        # Extract row/column labels
        cols = range(GRID_X_SIZE)
        rows = range(GRID_Y_SIZE)

        # Print column headers
        header = "     " + "  ".join(f"{col:^5}" for col in cols)
        print(header)
        print("   " + "-" * (GRID_X_SIZE * 7))

        # Print rows
        for r in rows:
            row_str = f"{r:>2} |"
            for c in cols:
                if ((c, r)) in self._obstacles:
                    content = "#"
                else:
                    cell = self._grid.get((c, r), ([], []))
                    if cell[0]:
                        if len(cell[0]) == 1:
                            content = ",".join(f"{x.faction[0:2].capitalize()}({len(x.actors)})" for x in cell[0])
                        else:
                            content = f"-{len(cell[0])} sq-"
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

    def add_log_msg(self, msg_type: str, message: str, square: Optional[Location] = None):
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

    def spawn(self, faction: str, location: Optional[Location] = None):
        """Spawn random faction squad on the map"""

        num_actors = random.randint(1, 5)

        if location is None:
            location = (random.randint(0, GRID_X_SIZE - 1), random.randint(0, GRID_Y_SIZE - 1))
            # avoid spawning on top of existing squads
            while location in self._grid and location not in self._obstacles:
                location = (random.randint(0, GRID_X_SIZE - 1), random.randint(0, GRID_Y_SIZE - 1))

        squad = Squad(faction, location)
        # Generate actors
        for _ in range(num_actors):
            squad.add_actor(Actor(faction, location))

        self.place(squad, location)
        self.add_log_msg("INFO", f"Spawned a new {num_actors}-actor {faction.upper()} squad", location)

        return True

    def remove(self, entity: type[Actor | Squad], square: Optional[Location] = None):
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

    def place(self, entity: type[Actor | Squad], square: Location):
        """Place actor or squad on the grid square"""
        index = 0 if isinstance(entity, Squad) else 1
        self._grid[square][index].append(entity)

        return True

    def cleanup(self):
        """Clean up empty squares. On larger grids they take up a lot of memory"""
        for square in self._squares_to_delete:
            del self._grid[square]

        self._squares_to_delete = set()

        return True
