"""Spawn parameters"""
SPAWN_FREQUENCY = 15 # frequency of new squad spawns (seconds)
MIN_FACTION_SQUADS = 15 # min number of faction squads to spawn on startup
MAX_FACTION_SQUADS = 17 # max number of faction squads to spawn on startup

"""Task parameters"""
MIN_IDLE_DURATION = 10 # min duration of "wait at current location" task
MAX_IDLE_DURATION = 30 # max duration of wait at current location" task
COMBAT_DURATION = 10 # duration of combat task
TRAVEL_DURATION = 10 # duration of travel to the adjacent square
LOOT_DURATION = 5 # duration of looting task

"""Pathfinding parameters"""
PATHFINDING_MODE = "hpa" # simple, astar, diagonal-astar or hpa
CLUSTER_SIZE = 10 # hpa only

"""Other parameters"""
SHOW_GRID = True
MAX_NUM_MESSAGES = 20 # max number of latest messages to display under the map grid
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
