import itertools
import heapq
import random
import os
import string

from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Optional

from colorama import Fore, Style, just_fix_windows_console

from config import MAX_NUM_MESSAGES, GRID_X_SIZE, GRID_Y_SIZE, SHOW_GRID, PATHFINDING_MODE, CLUSTER_SIZE, OBSTACLES


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
        self._path_cache = {}

        # Fix colored display on Windows
        just_fix_windows_console()

        # Pre-compute HPA* clusters
        if PATHFINDING_MODE == "hpa":
            self.add_log_msg("INFO", "Pre-computing HPA* clusters. This may take a while...")
            self._precompute_hpa()

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

    def create_simple_path(self, start: tuple[int, int], dest: tuple[int, int]):
        """Simple direct path on a 2D grid with 8-direction movement"""

        x, y = start
        x_end, y_end = dest
        path = []

        while (x, y) != dest:
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

    def create_8way_astar_path(self, start: tuple[int, int], goal: tuple[int, int], obstacles: set[tuple[int, int]]):
        """A* pathfinding on a 2D grid with 8-direction movement"""
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
                # Diagonals are more expensive
                step_cost = 1.4142 if dx != 0 and dy != 0 else 1.0
                tentative_g = current_g + step_cost
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        return None

    def create_astar_path(self, start: tuple[int, int], goal: tuple[int, int], obstacles: set[tuple[int, int]]):
        """A* pathfinding on a 2D grid with 4-direction movement"""

        def heuristic(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])

        open_set = [(heuristic(start, goal), 0, start, [start])]
        visited = set()

        while open_set:
            _, g, current, path = heapq.heappop(open_set)
            if current == goal:
                if (start, goal) not in self._path_cache and heuristic(current, goal) > 2:
                    self._path_cache[(start, goal)] = path[1:]

                return path[1:]

            if current in visited:
                continue

            if self._path_cache.get((current, goal), None):
                return self._path_cache[(current, goal)]

            visited.add(current)
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if 0 <= nx < GRID_X_SIZE and 0 <= ny < GRID_Y_SIZE and (nx, ny) not in obstacles:
                    heapq.heappush(open_set, (g + 1 + heuristic((nx,ny), goal), g + 1, (nx,ny), path + [(nx,ny)]))

        return None

    def _precompute_hpa(self):
        """Pre-compute HPA clusters and cluster links"""

        # Build cluster adjacency graph
        clusters = {}
        for x in range(0, GRID_X_SIZE, CLUSTER_SIZE):
            for y in range(0, GRID_Y_SIZE, CLUSTER_SIZE):
                cid = (x//CLUSTER_SIZE, y//CLUSTER_SIZE)
                clusters[cid] = [(i, j) for i in range(x, min(x+CLUSTER_SIZE, GRID_X_SIZE))
                                          for j in range(y, min(y+CLUSTER_SIZE, GRID_Y_SIZE))]

        graph = defaultdict(list)

        for cid, cells in clusters.items():
            cx, cy = cid
            for dx, dy in [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
                nid = (cx+dx, cy+dy)
                if nid in clusters:
                    # Check if there's any walkable shared-border cell
                    border_ok = False
                    for (x,y) in cells:
                        nx, ny = x + dx*CLUSTER_SIZE//max(1, abs(dx)), y + dy*CLUSTER_SIZE//max(1, abs(dy))
                        if 0 <= nx < GRID_X_SIZE and 0 <= ny < GRID_Y_SIZE and (nx,ny) not in OBSTACLES:
                            border_ok = True
                            break
                    if border_ok:
                        graph[cid].append(nid)

        self._clusters = clusters
        self._hpa_graph = graph

    def create_hpa_path(self, start: tuple[int, int], goal: tuple[int, int], obstacles: set[tuple[int, int]]):

        start_c, goal_c = (start[0]//CLUSTER_SIZE, start[1]//CLUSTER_SIZE), (goal[0]//CLUSTER_SIZE, goal[1]//CLUSTER_SIZE)
        if start_c == goal_c:
            return self.create_astar_path(start, goal, obstacles)

        def h_abs(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
        def cluster_of(cell):
            return (cell[0] // CLUSTER_SIZE, cell[1] // CLUSTER_SIZE)

        open_set = [(h_abs(start_c, goal_c), 0, start_c, [start_c])]
        visited = set()
        cluster_path = None
        while open_set:
            f, g, cur, path = heapq.heappop(open_set)
            if cur == goal_c:
                cluster_path = path
                break
            if cur in visited: continue
            visited.add(cur)
            for nxt in self._hpa_graph[cur]:
                if nxt not in visited:
                    heapq.heappush(open_set, (g+1+h_abs(nxt, goal_c), g+1, nxt, path+[nxt]))

        if not cluster_path:
            # Fallback to plain A*
            return self.create_8way_astar_path(start, goal, obstacles)

        # Refine each cluster-to-cluster hop
        full_path = [start]
        current = start
        for i in range(len(cluster_path)-1):
            from_c, to_c = cluster_path[i], cluster_path[i+1]
            # Find a border cell between these two clusters
            border_cells = []
            for cell in self._clusters[from_c]:
                if any(cluster_of((cell[0]+dx, cell[1]+dy)) == to_c
                       for dx, dy in [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]):
                    if cell not in obstacles:
                        border_cells.append(cell)
            # Pick the closest border cell to our current position
            border_cells.sort(key=lambda p: abs(p[0]-current[0])+abs(p[1]-current[1]))
            if not border_cells:
                return None
            next_goal = border_cells[0]
            segment = self.create_8way_astar_path(current, next_goal, obstacles)
            if not segment:
                return None

            full_path.extend(segment)
            current = next_goal

        # Final segment inside last cluster
        segment = self.create_8way_astar_path(current, goal, obstacles)
        if segment:
            full_path.extend(segment[1:])

        return full_path

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
