"""Spawn parameters"""
SPAWN_FREQUENCY = 20  # frequency of new squad spawns (seconds)
MIN_FACTION_SQUADS = 5  # min number of faction squads to spawn on startup
MAX_FACTION_SQUADS = 7  # max number of faction squads to spawn on startup

"""Task parameters"""
MIN_IDLE_DURATION = 10  # min duration of "wait at current location" task
MAX_IDLE_DURATION = 30  # max duration of wait at current location" task
COMBAT_DURATION = 10  # duration of combat task
TRAVEL_DURATION = 10  # duration of travel to the adjacent square
LOOT_DURATION = 5  # duration of looting task

"""Pathfinding parameters"""
PATHFINDING_MODE = "hpa"  # simple, astar, diagonal-astar or hpa
CLUSTER_SIZE = 10  # hpa only

"""Other parameters"""
SHOW_GRID = True
MAX_NUM_MESSAGES = 40  # max number of latest messages to display under the map grid
MAP = "map_40x24"  # make sure map dimensions match grid dimensions
GRID_X_SIZE = 40
GRID_Y_SIZE = 24

FACTIONS = {
    "stalker": {
        "spawn_bias": (0.5, 0.8),  # spawn bias on the grid, (0.5, 0.8) here being lower-center
        "relative_firepower": 1.0,  # relative firepower of the faction squad, 1.0 being the baseline
        "hostile": ("mercenary", "bandit", "military", "monolith", "mutant")  # factions hostile to the current faction
        },
    "bandit": {
        "spawn_bias": (0.5, 0.5),
        "relative_firepower": 0.9,
        "hostile": ("stalker", "mercenary", "ward", "military", "monolith", "mutant")
        },
    "ward": {
        "spawn_bias": (0.3, 0.6),
        "relative_firepower": 1.4,
        "hostile": ("spark", "bandit", "mercenary", "monolith", "mutant")
    },
    "spark": {
        "spawn_bias": (0.0, 0.5),
        "relative_firepower": 1.4,
        "hostile": ("ward", "monolith", "mutant")
    },
    "mercenary": {
        "spawn_bias": (0.0, 0.8),
        "relative_firepower": 1.5,
        "hostile": ("stalker", "bandit", "ward", "military", "monolith", "mutant")
    },
    "military": {
        "spawn_bias": (0.5, 0.2),
        "relative_firepower": 1.2,
        "hostile": ("stalker", "bandit", "mercenary", "monolith", "mutant")
    },
    "monolith": {
        "spawn_bias": (0.1, 0.1),
        "relative_firepower": 1.8,
        "hostile": ("stalker", "bandit", "ward", "spark", "mercenary", "military", "mutant")
    },
    "mutant": {
        "spawn_bias": None,  # can spawn anywhere
        "relative_firepower": 1.6,
        "hostile": ("stalker", "bandit", "ward", "spark", "mercenary", "military", "monolith")
    }
}
