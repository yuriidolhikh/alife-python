import os
import pickle
import random

from collections import deque, defaultdict
from colorama import Fore, Style, just_fix_windows_console
from typing import Optional

from .actor import Actor
from .pathfinder import Pathfinder
from .squad import Squad
from .types import Location

from config import MAX_NUM_MESSAGES, SHOW_GRID, GRID_X_SIZE, GRID_Y_SIZE, MAP, FACTIONS


class MapGrid:
    """Defines the map and contains all map-related function"""

    def __init__(self):
        self._grid = defaultdict(lambda: ([], []))
        self._msg_log = deque([], maxlen=MAX_NUM_MESSAGES)
        self._squares_to_delete = set()

        dirname = os.path.dirname(__file__)
        mapfile = os.path.abspath(os.path.join(dirname, f'../maps/{MAP}'))
        area_map = {"pois": set(), "fields": set(), "traders": set(), "obstacles": set()}

        try:
            with open(mapfile, 'rb') as f:
                tentative_map = pickle.load(f)
                if isinstance(tentative_map, set):  # retain support for simple maps
                    area_map = {"pois": set(), "fields": set(), "traders": set(), "obstacles": tentative_map}
                else:
                    area_map = tentative_map

        except Exception as e:
            self.add_log_msg("INFO", f" Failed to load map data: {e}")
            area_map = {"pois": set(), "fields": set(), "traders": set(), "obstacles": set()}

        self._area_map = area_map
        self.pathfinder = Pathfinder(area_map["obstacles"])

        # Fix colored display on Windows
        just_fix_windows_console()

    def get_grid(self):
        return self._grid

    def get_obstacles(self):
        return self._area_map["obstacles"]

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
                if ((c, r)) in self._area_map["obstacles"]:
                    content = "#"
                elif ((c, r)) in self._area_map["traders"]:
                    content = "T"
                elif ((c, r)) in self._area_map["fields"]:
                    content = "F"
                elif ((c, r)) in self._area_map["pois"]:
                    content = "P"
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

        parts = []
        if msg_type == "COMBAT":
            parts.append(f"{Fore.RED}[COMBAT]{Style.RESET_ALL}")
        elif msg_type == "LOOT":
            parts.append(f"{Fore.YELLOW}[LOOT]{Style.RESET_ALL}")
        elif msg_type == "MOVE":
            parts.append(f"{Fore.GREEN}[MOVE]{Style.RESET_ALL}")
        elif msg_type == "IDLE":
            parts.append(f"{Fore.CYAN}[IDLE]{Style.RESET_ALL}")
        else:
            parts.append("[INFO]")

        if square:
            parts.append(f"[SQUARE={square}]")

        parts.append(message.upper())
        logged_msg = " ".join(parts)

        if SHOW_GRID:
            self._msg_log.append(logged_msg)
        else:
            print(logged_msg)

        return True

    def spawn(self, faction: str, location: Optional[Location] = None):
        """Spawn random faction squad on the map"""

        if location is None:
            bias = FACTIONS[faction]["spawn_bias"]
            lower_x, lower_y, upper_x, upper_y = (0, 0, GRID_X_SIZE, GRID_Y_SIZE)

            if bias is not None:
                lower_x, lower_y, upper_x, upper_y = self.get_spawn_area(FACTIONS[faction]["spawn_bias"])

            # avoid spawning on top of obstacles
            while (location := (random.randint(lower_x, upper_x), random.randint(lower_y, upper_y))) in self._area_map["obstacles"]: pass

        squad = Squad(faction, location)
        # Generate actors
        num_actors = random.randint(1, 5)
        for _ in range(num_actors):
            actor = Actor(faction, location)
            squad.add_actor(actor)

        self.place(squad, location)
        self.add_log_msg("INFO", f"Spawned a new {num_actors}-actor {faction.upper()} squad", location)

        return True

    def get_spawn_area(self, bias: tuple[float, float], fractions: Optional[tuple[float, float]] = None):
        """
            Create a spawning area given a bias ((0.0, 0.0) being an upper left corner, (1.0, 1.0) being the lower right)
            and a fraction parameter that determines the percentage of the grid in X and Y dimensions to include.
            This method is used to spawn faction squads in their designated areas.
        """
        x_bias, y_bias = bias
        # If no fractions are specified, default to a 20% of the grid
        if fractions is None:
            fractions = (0.2, 0.2)

        fx = max(0.0, min(1.0, fractions[0]))
        fy = max(0.0, min(1.0, fractions[1]))

        box_w = GRID_X_SIZE * fx
        box_h = GRID_Y_SIZE * fy

        # Center coordinates based on bias
        cx = x_bias * GRID_X_SIZE
        cy = y_bias * GRID_Y_SIZE

        # Compute boundaries
        x_min = int(round(cx - box_w / 2))
        x_max = int(round(cx + box_w / 2))
        y_min = int(round(cy - box_h / 2))
        y_max = int(round(cy + box_h / 2))

        # Clamp to grid
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(GRID_X_SIZE, x_max)
        y_max = min(GRID_Y_SIZE, y_max)

        return [x_min, y_min, x_max, y_max]

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
