import re
import ast
import os

# Updated Paths
INPUT_FILE = r"C:\Users\cthin\AI\HeliAttack\heliattack2_scripts\frame_19_DoAction_2.as"
OUTPUT_FILE = r"C:\Users\cthin\AI\HeliAttack\ha2_constants.py"

def extract_data():
    # Fallback in case the folder was moved intact rather than contents dumped
    target_file = INPUT_FILE
    if not os.path.exists(target_file):
        alt_file = r"C:\Users\cthin\AI\HeliAttack\heliattack2_scripts\ha2_core_logic\frame_19_DoAction_2.as"
        if os.path.exists(alt_file):
            target_file = alt_file
        else:
            print(f"Error: Could not find the file at {INPUT_FILE} or {alt_file}")
            return

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Extract map1 using Regex
    print("Extracting map1 array...")
    map1_match = re.search(r"map1\s*=\s*(\[\[\[.*?\]\]\]);", content, re.DOTALL)
    
    if not map1_match:
        print("Failed to find map1 in the source file.")
        return

    raw_map_str = map1_match.group(1)
    
    # Evaluate the JS array string as a Python list
    raw_map = ast.literal_eval(raw_map_str)
    
    # 2. Process Map for Collision & Spawn
    # The AS code uses map[y][x][0] for logic. 0 = Empty, 32 = Player Spawn, Others = Solid.
    collision_grid = []
    spawn_point = (0, 0)

    for y, row in enumerate(raw_map):
        grid_row = []
        for x, tile in enumerate(row):
            tile_type = tile[0]
            if tile_type == 32:
                spawn_point = (x, y)
                grid_row.append(0) # Spawn is an empty space
            elif tile_type == 0:
                grid_row.append(0) # Empty space
            else:
                grid_row.append(1) # Solid wall/floor
        collision_grid.append(grid_row)

    # 3. Write ha2_constants.py
    print(f"Writing constants to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# --- AUTO-GENERATED HA2 CONSTANTS ---\n\n")
        f.write("# --- ENVIRONMENT ---\n")
        f.write("TILE_SIZE = 50\n")
        f.write("SCREEN_WIDTH = 450\n")
        f.write("SCREEN_HEIGHT = 320\n")
        f.write("GRAVITY = 1.0\n")
        f.write("MAX_FALL_SPEED = 50.0\n")
        f.write("TERMINAL_VELOCITY_X = 6.0\n\n")
        
        f.write("# --- PLAYER ---\n")
        f.write("PLAYER_START_HEALTH = 100\n")
        f.write("PLAYER_WIDTH = 10\n")
        f.write("PLAYER_HEIGHT = 42\n")
        f.write("PLAYER_DUCK_WIDTH = 6.66\n")
        f.write("PLAYER_DUCK_HEIGHT = 28\n")
        f.write("MOVE_ACCEL = 1.0\n")
        f.write("MAX_WALK_SPEED = 5.0\n")
        f.write("FRICTION = 1.0\n")
        f.write("JUMP_POWER = -8.0\n")
        f.write("JUMP_FRAMES = 6\n")
        f.write("HYPER_JUMP_POWER = -32.0\n")
        f.write("HYPER_JUMP_CHARGE_MAX = 150\n\n")

        f.write("# --- ENEMIES ---\n")
        f.write("HELI_START_HEALTH = 300\n")
        f.write("ENEMY_BULLET_SPEED = 7.0\n")
        f.write("ENEMY_BULLET_DAMAGE = 10\n\n")

        f.write("# --- WEAPONS ---\n")
        f.write("WEAPONS = {\n")
        f.write("    'MachineGun':      {'reload': 5,   'speed': 8,  'damage': 10},\n")
        f.write("    'AkimboMac10s':    {'reload': 4,   'speed': 8,  'damage': 9},\n")
        f.write("    'Shotgun':         {'reload': 25,  'speed': 8,  'damage': 15},\n")
        f.write("    'ShotgunRockets':  {'reload': 40,  'speed': 7,  'damage': 40},\n")
        f.write("    'GrenadeLauncher': {'reload': 30,  'speed': 15, 'damage': 75},\n")
        f.write("    'RPG':             {'reload': 40,  'speed': 4,  'damage': 75},\n")
        f.write("    'RocketLauncher':  {'reload': 50,  'speed': 7,  'damage': 100},\n")
        f.write("    'SeekerLauncher':  {'reload': 55,  'speed': 7,  'damage': 100},\n")
        f.write("    'FlameThrower':    {'reload': 1,   'speed': 8,  'damage': 2},\n")
        f.write("    'FireMines':       {'reload': 100, 'speed': 3,  'damage': 5},\n")
        f.write("    'ABombLauncher':   {'reload': 150, 'speed': 3,  'damage': 300},\n")
        f.write("    'RailGun':         {'reload': 75,  'speed': 20, 'damage': 150},\n")
        f.write("    'GrappleCannon':   {'reload': 250, 'speed': 20, 'damage': 300},\n")
        f.write("    'ShoulderCannon':  {'reload': 100, 'speed': 20, 'damage': 300}\n")
        f.write("}\n\n")

        f.write("# --- MAP DATA ---\n")
        f.write(f"PLAYER_SPAWN_INDEX = {spawn_point}\n")
        f.write("COLLISION_GRID = [\n")
        for row in collision_grid:
            f.write(f"    {row},\n")
        f.write("]\n")

    print(f"Success! Map dimensions: {len(collision_grid[0])}x{len(collision_grid)}. Spawn at: {spawn_point}")

if __name__ == "__main__":
    extract_data()