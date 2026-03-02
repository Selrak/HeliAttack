# --- AUTO-GENERATED HA2 CONSTANTS ---

# --- ENVIRONMENT ---
TILE_SIZE = 50
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 320
GRAVITY = 1.0
MAX_FALL_SPEED = 50.0
TERMINAL_VELOCITY_X = 6.0

# --- PLAYER ---
PLAYER_START_HEALTH = 100
PLAYER_WIDTH = 10
PLAYER_HEIGHT = 42
PLAYER_DUCK_WIDTH = 6.66
PLAYER_DUCK_HEIGHT = 28
MOVE_ACCEL = 1.0
MAX_WALK_SPEED = 5.0
FRICTION = 1.0
JUMP_POWER = -8.0
JUMP_FRAMES = 6
HYPER_JUMP_POWER = -32.0
HYPER_JUMP_CHARGE_MAX = 150

# --- ENEMIES ---
HELI_START_HEALTH = 300
ENEMY_BULLET_SPEED = 7.0
ENEMY_BULLET_DAMAGE = 10

# --- WEAPONS ---
WEAPONS = {
    'MachineGun':      {'reload': 5,   'speed': 8,  'damage': 10},
    'AkimboMac10s':    {'reload': 4,   'speed': 8,  'damage': 9},
    'Shotgun':         {'reload': 25,  'speed': 8,  'damage': 15},
    'ShotgunRockets':  {'reload': 40,  'speed': 7,  'damage': 40},
    'GrenadeLauncher': {'reload': 30,  'speed': 15, 'damage': 75},
    'RPG':             {'reload': 40,  'speed': 4,  'damage': 75},
    'RocketLauncher':  {'reload': 50,  'speed': 7,  'damage': 100},
    'SeekerLauncher':  {'reload': 55,  'speed': 7,  'damage': 100},
    'FlameThrower':    {'reload': 1,   'speed': 8,  'damage': 2},
    'FireMines':       {'reload': 100, 'speed': 3,  'damage': 5},
    'ABombLauncher':   {'reload': 150, 'speed': 3,  'damage': 300},
    'RailGun':         {'reload': 75,  'speed': 20, 'damage': 150},
    'GrappleCannon':   {'reload': 250, 'speed': 20, 'damage': 300},
    'ShoulderCannon':  {'reload': 100, 'speed': 20, 'damage': 300}
}

# --- MAP DATA ---
PLAYER_SPAWN_INDEX = (0, 13)
COLLISION_GRID = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]
