"""Spawn parameters"""
SPAWN_FREQUENCY = 15 # frequency of new squad spawns (seconds)
MIN_FACTION_SQUADS = 20 # min number of faction squads to spawn on startup
MAX_FACTION_SQUADS = 30 # max number of faction squads to spawn on startup

"""Task parameters"""
MIN_IDLE_DURATION = 10 # min duration of "wait at current location" task
MAX_IDLE_DURATION = 30 # max duration of wait at current location" task
COMBAT_DURATION = 10 # duration of combat task
TRAVEL_DURATION = 10 # duration of travel to the adjacent square
LOOT_DURATION = 5 # duration of looting task

"""Pathfinding parameters"""
PATHFINDING_MODE = "astar" # simple, astar, diagonal-astar or hpa
CLUSTER_SIZE = 80 # hpa only

"""Other parameters"""
MAX_NUM_MESSAGES = 20 # max number of latest messages to display under the map grid
SHOW_GRID = True
GRID_X_SIZE = 50
GRID_Y_SIZE = 50

# faction -> factions hostile to it
RELATIONS = {
    "stalker": {"mercenary", "military", "monolith", "mutant"},
    "ward": {"spark", "mercenary", "monolith", "mutant"},
    "spark": {"ward", "monolith", "mutant"},
    "mercenary": {"stalker", "ward", "military", "monolith", "mutant"},
    "military": {"stalker", "mercenary", "monolith", "mutant"},
    "monolith": {"stalker", "ward", "spark", "mercenary", "military", "mutant"},
    "mutant": {"stalker", "ward", "spark", "mercenary", "military", "monolith"}
}

FACTIONS = ("stalker", "ward", "spark", "mercenary", "military", "monolith", "mutant")

OBSTACLES = set()
