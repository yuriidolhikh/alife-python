This is a hypothetical implementation of STALKER 2 offline A-Life in Python 3.

<img width="1053" height="868" alt="Screenshot 2025-10-22 at 19 38 55" src="https://github.com/user-attachments/assets/fcba280d-8147-4cd2-8284-864a089c28c0" />

Squads on the grid can
- be tasked to wait at current location or move to a new one
- navigate a map with obstacles with optimal pathfinding
- fight other squads and loot bodies
- hunt for artifacts and trade
- collect bounties on other squads
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

# Known Issues
- Some maps have disconnected passable squares where squads can spawn and get stuck
