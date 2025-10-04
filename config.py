"""Spawn parameters"""
SPAWN_FREQUENCY = 20  # frequency of new squad spawns (seconds)
MIN_FACTION_SQUADS = 15  # min number of faction squads to spawn on startup
MAX_FACTION_SQUADS = 17  # max number of faction squads to spawn on startup

"""Task parameters"""
MIN_IDLE_DURATION = 10  # min duration of "wait at current location" task
MAX_IDLE_DURATION = 30  # max duration of wait at current location" task
COMBAT_DURATION = 10  # duration of combat task
TRAVEL_DURATION = 10  # duration of travel to the adjacent square
LOOT_DURATION = 5  # duration of looting task
ARTIFACT_HUNT_DURATION = 10

"""Pathfinding parameters"""
PATHFINDING_MODE = "hpa"  # simple, astar, diagonal-astar or hpa
CLUSTER_SIZE = 10  # hpa only

"""Other parameters"""
SHOW_GRID = True  # enables the map grid display in terminal (larger grids may not fit)
MAX_NUM_MESSAGES = 40  # max number of latest messages to display under the map grid
MAP = "pois_obstacles_map_100x85"  # make sure map dimensions match grid dimensions
GRID_X_SIZE = 100
GRID_Y_SIZE = 85

RANKS = ("Rookie", "Novice", "Experienced", "Veteran", "Master", "Legend")  # rank progression of an actor
EXP_PER_RANK = 2000  # Amount of exp required to advance a rank

FACTIONS = {
    "stalker": {
        "spawn_bias": None,  # spawn bias on the grid, for example (0.5, 0.8) being lower-center
        "relative_firepower": 1.0,  # relative firepower of the faction squad, 1.0 being the baseline
        "hostile": ("mercenary", "bandit", "military", "monolith", "mutant"),  # factions hostile to the current faction
        "can_loot": True,  # determines if this faction can loot bodies
        "can_gain_exp": True,  # determines if actors of this faction can gain exp
        "can_trade": True,  # determines if actors of this faction will visit traders
        "can_hunt_artifacts": True  # determines if actors of this faction will hunt for artifacts
        },
    "bandit": {
        "spawn_bias": (0.5, 0.5),
        "relative_firepower": 0.9,
        "hostile": ("stalker", "mercenary", "ward", "military", "monolith", "mutant"),
        "can_loot": True,
        "can_gain_exp": True,
        "can_trade": True,
        "can_hunt_artifacts": False
        },
    "ward": {
        "spawn_bias": (0.3, 0.6),
        "relative_firepower": 1.4,
        "hostile": ("spark", "bandit", "mercenary", "monolith", "mutant"),
        "can_loot": True,
        "can_gain_exp": True,
        "can_trade": True,
        "can_hunt_artifacts": False
    },
    "spark": {
        "spawn_bias": (0.1, 0.5),
        "relative_firepower": 1.4,
        "hostile": ("ward", "monolith", "mutant"),
        "can_loot": True,
        "can_gain_exp": True,
        "can_trade": True,
        "can_hunt_artifacts": False
    },
    "mercenary": {
        "spawn_bias": (0.1, 0.8),
        "relative_firepower": 1.5,
        "hostile": ("stalker", "bandit", "ward", "military", "monolith", "mutant"),
        "can_loot": True,
        "can_gain_exp": True,
        "can_trade": False,
        "can_hunt_artifacts": False
    },
    "military": {
        "spawn_bias": (0.5, 0.3),
        "relative_firepower": 1.2,
        "hostile": ("stalker", "bandit", "mercenary", "monolith", "mutant"),
        "can_loot": True,
        "can_gain_exp": True,
        "can_trade": False,
        "can_hunt_artifacts": False
    },
    "monolith": {
        "spawn_bias": (0.2, 0.0),
        "relative_firepower": 1.8,
        "hostile": ("stalker", "bandit", "ward", "spark", "mercenary", "military", "mutant"),
        "can_loot": True,
        "can_gain_exp": True,
        "can_trade": False,
        "can_hunt_artifacts": False
    },
    "mutant": {
        "spawn_bias": None,  # can spawn anywhere
        "relative_firepower": 2.0,
        "hostile": ("stalker", "bandit", "ward", "spark", "mercenary", "military", "monolith"),
        "can_loot": False,
        "can_gain_exp": False,
        "can_trade": False,
        "can_hunt_artifacts": False
    }
}
