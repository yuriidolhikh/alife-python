import random
import os
import string

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from colorama import Fore, Style, just_fix_windows_console

from config import LETTERS, MAX_NUM_MESSAGES


@dataclass
class Actor:
    """Individual actor on the grid"""
    faction: str
    location: tuple
    looted: bool = False

    def __str__(self):
        return f"{self.faction.capitalize()} ACTOR AT LOCATION {self.location}"


@dataclass
class Squad:
    """Squad on the grid, made up of multiple actors. Executes tasks"""
    faction: str
    location: tuple[str, int]
    actors: list = field(default_factory=list) # list of actors in the squad
    has_task: bool = False
    in_combat: bool = False
    is_looting: bool = False

    def __str__(self):
        return f"{self.faction.upper()} SQUAD ({len(self.actors)} ACTORS) AT LOCATION {self.location}"

    def isBusy(self):
        return self.in_combat or self.is_looting or self.has_task

    def addActor(self, actor: Actor):
        self.actors.append(actor)

    def removeActor(self, actor: Actor):
        try:
            index = self.actors.index(actor)
        except ValueError:
            return False

        del self.actors[index]

        return True


class MapGrid:
    """Defines the map and contains all map-related function"""

    def __init__(self):
        self._grid = {(l, d): ([], []) for l in LETTERS for d in range(len(LETTERS) + 1)}
        self._msg_log = deque([], maxlen=MAX_NUM_MESSAGES)

        # Fix colored display on Windows
        just_fix_windows_console()

    def getGrid(self):
        return self._grid

    def draw(self):
        """Draw current grid state in console"""

        # Extract row/column labels
        cols = sorted(set(k[0] for k in self._grid.keys()), key=lambda c: string.ascii_uppercase.index(c))
        rows = sorted(set(k[1] for k in self._grid.keys()))

        # Print column headers
        header = "     " + "  ".join(f"{col:^5}" for col in cols)
        print(header)
        print("   " + "-" * (len(cols) * 7))

        # Print rows
        for r in rows:
            row_str = f"{r:>2} |"
            for c in cols:
                cell = self._grid.get((c, r), ())
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
        os.system("cls" if os.name == "nt" else "printf '\33c\e[3J'")
        self.draw()

    def addLogMsg(self, msg_type: str, message: str, square: Optional[tuple[str, int]] = None):
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

        self._msg_log.append(logged_msg)

        return True

    def spawn(self, faction: str):
        """Spawn random faction squad on the map"""

        num_actors = random.randint(1, 5)
        location = (random.choice(LETTERS), random.randint(0, len(LETTERS)))

        # avoid spawning on top of existing squads
        while self._grid[location][0]:
            location = (random.choice(LETTERS), random.randint(0, len(LETTERS)))

        squad = Squad(faction, location)
        # Generate actors
        for _ in range(num_actors):
            squad.addActor(Actor(faction, location))

        self.place(squad, location)
        self.addLogMsg("INFO", f"Spawned a new {num_actors}-actor {faction.upper()} squad", location)

        return True

    def createPath(self, start: tuple[str, int], dest: tuple[str, int]):
        """
        Create a path from start to dest moving 1 step at a time.
        Each step can be diagonal, vertical, or horizontal.
        Grid rows start at 0, so top-left is ('A', 0).
        """
        # Map letters <-> numbers
        col_to_idx = {c: i for i, c in enumerate(LETTERS)}
        idx_to_col = {i: c for c, i in col_to_idx.items()}

        col_s, row_s = start
        col_d, row_d = dest

        x, y = col_to_idx[col_s], row_s
        x_end, y_end = col_to_idx[col_d], row_d

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

            path.append((idx_to_col[x], y))

        return path

    def remove(self, entity: type[Actor | Squad], square: Optional[tuple[str, int]] = None):
        """Remove actor or squad from the grid. If grid square is not provided - attempt to get location from the entity"""
        index = 0 if isinstance(entity, Squad) else 1
        try:
            location = square if square is not None else entity.location
            del self._grid[location][index][self._grid[location][index].index(entity)]
        except ValueError:
            return False

        return True

    def place(self, entity: type[Actor | Squad], square: tuple[str, int]):
        """Place actor or squad on the grid square"""
        index = 0 if isinstance(entity, Squad) else 1
        self._grid[square][index].append(entity)

        return True
