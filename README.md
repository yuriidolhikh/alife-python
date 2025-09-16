# alife-python
This is a hypothetical implementation of STALKER 2 offline A-Life in Python 3.

![demo](https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExOThnZzhzbno1NmU1YXJ3eTE0ZzV0cHRoZjY0OHpjYjdwam5tenByZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/VVh03jGxzHFca1aLjQ/giphy.gif)

# HOWTO
    cd alife-python/
    pip3 install -r requirements.txt
    python3 main.py

# PATHFINDERS
- `simple`: direct shortest path to destination. Ignores obstacles
- `astar`: 4-way A*. Works well for medium-sized grids (less then 150x150)
- `diagonal-astar`: A*, but with 8-way movement, same as regular A* otherwise
- `hpa`: Requires warm-up and extra memory, but works well with larger grids

# TODO
- Support for obstacles and faction no-go zones on the map
- ~~Update of pathing algorithm for optimal pathfinding with obstacles~~
- Trade and HuntSquad tasks
- Firepower-based combat resolution
