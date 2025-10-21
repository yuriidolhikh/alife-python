This is a hypothetical implementation of STALKER 2 offline A-Life in Python 3.

<img width="1440" height="819" alt="Screenshot 2025-09-24 at 14 22 31" src="https://github.com/user-attachments/assets/09001260-bbfd-49e4-9e6e-8d04277e3c76" />

Squads on the grid can
- be tasked to wait at current location or move to a new one
- navigate a map with obstacles with optimal (not 100% perfect though) pathfinding
- fight other squads and loot bodies
- gain experience and ranks when they complete certain tasks (i.e.: idling on location does not award exp, but traveling across the area does)
- have higher chances of surviving combat as they gain more experience

# HOWTO
    cd alife-python/
    pip3 install -r requirements.txt
    python3 main.py

# PATHFINDERS
- `simple`: direct shortest path to destination. Ignores obstacles
- `astar`: 4-way A*. Works well for medium-sized grids (less than 150x150)
- `diagonal-astar`: A*, but with 8-way movement, same as regular A* otherwise
- `hpa`: Hierarchical A*. Requires warm-up and extra memory, but works well with larger grids

# TODO
- ~~Support for obstacles and faction no-go zones on the map~~
- ~~Update of pathing algorithm for optimal pathfinding with obstacles~~
- ~~Trade and HuntSquad tasks~~
- ~~Firepower-based combat resolution~~
