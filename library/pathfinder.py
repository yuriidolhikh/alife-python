import heapq

from collections import defaultdict

from config import GRID_X_SIZE, GRID_Y_SIZE, PATHFINDING_MODE, CLUSTER_SIZE

from library.types import Location


class Pathfinder:
    """Everything related to finding a path on the grid"""

    def __init__(self, obstacles: set[Location]) -> None:

        # Cache computed path chunks for faster pathfinding
        self._path_cache = {}
        self._neighbors_including_diagonals = [
            (0, 1), (1, 1), (1, 0), (1, -1),
            (0, -1), (-1, -1), (-1, 0), (-1, 1)
        ]
        self._obstacles = obstacles

        if PATHFINDING_MODE == "hpa":
            """
                For performance reasons it's optimal to pre-compute HPA* cluster links if obstacles are static
                If obstacle set changes between pathfinding calls the new set can be passed
                directly into create_path method
            """
            print("[INFO] PRE-COMPUTING HPA* CLUSTERS. THIS MAY TAKE A WHILE...")
            self._clusters = self._precompute_clusters()
            self._hpa_graph = self._compute_cluster_links(obstacles)

    def _precompute_clusters(self) -> dict[Location, list[Location]]:
        """Pre-compute HPA clusters and cluster links"""

        # Build cluster adjacency graph
        clusters = {}
        for x in range(0, GRID_X_SIZE, CLUSTER_SIZE):
            for y in range(0, GRID_Y_SIZE, CLUSTER_SIZE):
                cid = (x // CLUSTER_SIZE, y // CLUSTER_SIZE)
                clusters[cid] = [(i, j) for i in range(x, min(x + CLUSTER_SIZE, GRID_X_SIZE))
                                          for j in range(y, min(y + CLUSTER_SIZE, GRID_Y_SIZE))]

        return clusters

    def _compute_cluster_links(self, obstacles: set[Location]) -> defaultdict[Location, list[Location]]:
        graph = defaultdict(list)
        for cid, cells in self._clusters.items():
            cx, cy = cid
            for dx, dy in self._neighbors_including_diagonals:
                nid = (cx + dx, cy + dy)
                if nid in self._clusters:
                    # Check if there's any walkable shared-border cell
                    border_ok = False
                    for (x, y) in cells:
                        nx, ny = x + dx * CLUSTER_SIZE // max(1, abs(dx)), y + dy * CLUSTER_SIZE // max(1, abs(dy))
                        if 0 <= nx < GRID_X_SIZE and 0 <= ny < GRID_Y_SIZE and (nx, ny) not in obstacles:
                            border_ok = True
                            break

                    if border_ok:
                        graph[cid].append(nid)

        return graph

    def manhattan_distance(self, a: Location, b: Location) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def chebyshev_distance(self, a: Location, b: Location) -> int:
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def in_bounds(x: int, y: int) -> bool:
        return 0 <= x < GRID_X_SIZE and 0 <= y < GRID_Y_SIZE

    def create_path(self, start: Location, dest: Location, obstacles: set[Location] | None = None) -> list[Location] | None:
        """Create a path using a specified pathfinder algorithm"""

        final_obstacle_set = self._obstacles
        if obstacles:
            final_obstacle_set = self._obstacles.union(obstacles)

        if PATHFINDING_MODE == "hpa":
            path = self.create_hpa_path(start, dest, final_obstacle_set)
        elif PATHFINDING_MODE == "astar":
            path = self.create_astar_path(start, dest, final_obstacle_set)
        elif PATHFINDING_MODE == "diagonal-astar":
            path = self.create_8way_astar_path(start, dest, final_obstacle_set)
        else:
            path = self.create_simple_path(start, dest)

        return path

    def create_simple_path(self, start: Location, dest: Location) -> list[Location]:
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

    def create_8way_astar_path(self, start: Location, goal: Location, obstacles: set[Location]) -> list[Location] | None:
        """A* pathfinding on a 2D grid with 8-direction movement"""

        open_set = []
        heapq.heappush(open_set, (self.chebyshev_distance(start, goal), 0, start))
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

            for dx, dy in self._neighbors_including_diagonals:
                neighbor = (current[0] + dx, current[1] + dy)
                if not self.in_bounds(*neighbor) or neighbor in obstacles:
                    continue
                # Diagonals are more expensive
                step_cost = 1.4142 if dx != 0 and dy != 0 else 1.0
                tentative_g = current_g + step_cost
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.chebyshev_distance(neighbor, goal)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        return None

    def create_astar_path(self, start: Location, goal: Location, obstacles: set[Location]) -> list[Location] | None:
        """A* pathfinding on a 2D grid with 4-direction movement"""

        open_set = [(self.manhattan_distance(start, goal), 0, start, [start])]
        visited = set()

        while open_set:
            _, g, current, path = heapq.heappop(open_set)
            if current == goal:
                if (start, goal) not in self._path_cache and self.manhattan_distance(current, goal) > 2:
                    self._path_cache[(start, goal)] = path[1:]

                return path[1:]

            if current in visited:
                continue

            if self._path_cache.get((current, goal), None):
                return self._path_cache[(current, goal)]

            visited.add(current)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if self.in_bounds(nx, ny) and (nx, ny) not in obstacles:
                    heapq.heappush(open_set, (g + 1 + self.manhattan_distance((nx, ny), goal), g + 1, (nx, ny), path + [(nx, ny)]))

        return None

    def create_hpa_path(self, start: Location, goal: Location, obstacles: set[Location]) -> list[Location] | None:
        """HPA* pathfinding on a 2D grid with 8-directional movement"""

        def cluster_of(cell: Location) -> Location:
            return cell[0] // CLUSTER_SIZE, cell[1] // CLUSTER_SIZE

        start_c, goal_c = cluster_of(start), cluster_of(goal)
        # Both points inside the same cluster - fallback to plain A*
        if start_c == goal_c:
            return self.create_8way_astar_path(start, goal, obstacles)

        # Obstacle set changed, need to rebuild cluster links
        if obstacles != self._obstacles:
            graph = self._compute_cluster_links(obstacles)
        else:
            graph = self._hpa_graph

        open_set = [(self.manhattan_distance(start_c, goal_c), 0, start_c, [start_c])]
        visited = set()
        cluster_path = None

        while open_set:
            f, g, cur, path = heapq.heappop(open_set)
            if cur == goal_c:
                cluster_path = path
                break

            if cur in visited:
                continue

            visited.add(cur)
            for nxt in graph[cur]:
                if nxt not in visited:
                    heapq.heappush(open_set, (g + 1 + self.manhattan_distance(nxt, goal_c), g + 1, nxt, path + [nxt]))

        if not cluster_path:
            # Fallback to plain A*
            return self.create_8way_astar_path(start, goal, obstacles)

        # Refine each cluster-to-cluster hop
        full_path = [start]
        current = start
        for i in range(len(cluster_path) - 1):
            from_c, to_c = cluster_path[i], cluster_path[i + 1]
            # Find a border cell between these two clusters
            border_cells = []
            for cell in self._clusters[from_c]:
                if any(cluster_of((cell[0] + dx, cell[1] + dy)) == to_c for dx, dy in self._neighbors_including_diagonals):
                    if cell not in obstacles:
                        border_cells.append(cell)

            # Pick the closest border cell to our current position
            border_cells.sort(key=lambda p: self.manhattan_distance(p, current))
            if not border_cells:
                return self.create_8way_astar_path(start, goal, obstacles)

            next_goal = border_cells[0]
            if next_goal == current:
                continue

            # Try simple direct path first. If it has obstacles - fallback to A*
            tentative_path = self.create_simple_path(current, next_goal)
            if not set(tentative_path) & obstacles:
                segment = tentative_path
            else:
                segment = self.create_8way_astar_path(current, next_goal, obstacles)

            if not segment:
                return None

            full_path.extend(segment)
            current = next_goal

        # Final segment inside last cluster
        tentative_path = self.create_simple_path(current, goal)
        if not set(tentative_path) & obstacles:
            segment = tentative_path
        else:
            segment = self.create_8way_astar_path(current, goal, obstacles)

        if segment:
            full_path.extend(segment)

        return full_path[1:]
