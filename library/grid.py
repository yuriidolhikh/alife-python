import os
import random

from collections import deque
from colorama import Fore, Style, just_fix_windows_console
from typing import Optional

from .actor import Actor
from .squad import Squad
from .pathfinder import Pathfinder

from config import MAX_NUM_MESSAGES, SHOW_GRID, GRID_X_SIZE, GRID_Y_SIZE, OBSTACLES


class MapGrid:
    """Defines the map and contains all map-related function"""

    def __init__(self):
        self._grid = {}
        self._msg_log = deque([], maxlen=MAX_NUM_MESSAGES)
        self._squares_to_delete = set()
        self.pathfinder = Pathfinder()

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
                if ((c, r)) in OBSTACLES:
                    content = "#"
                else:
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
