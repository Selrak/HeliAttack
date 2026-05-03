import ast
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent
INPUT_FILE = REPO_ROOT / "heliattack2_scripts" / "ha2_core_logic" / "frame_19_DoAction_2.as"
OUTPUT_FILE = REPO_ROOT / "ha2_constants.py"

def extract_data():
    if not INPUT_FILE.exists():
        print(f"Error: Could not find {INPUT_FILE}")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        content = f.read()

    # 1. Extract map1 (the full 3D array) using Regex
    print("Extracting full map1 array...")
    map1_match = re.search(r"map1\s*=\s*(\[\[\[.*?\]\]\]);", content, re.DOTALL)
    
    if not map1_match:
        print("Failed to find map1 in the source file.")
        return

    raw_map_str = map1_match.group(1)
    # Convert JS-style array string to Python nested list
    full_map_data = ast.literal_eval(raw_map_str)
    
    # 2. Extract Spawn Point (Found at map[y][x][0] == 32)
    spawn_point = (0, 0)
    for y, row in enumerate(full_map_data):
        for x, tile in enumerate(row):
            if tile[0] == 32:
                spawn_point = (x, y)

    # 3. Write ha2_constants.py
    print(f"Writing full map data and constants to {OUTPUT_FILE}...")
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
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

        f.write("# --- MAP DATA ---\n")
        f.write(f"PLAYER_SPAWN_INDEX = {spawn_point}\n")
        f.write("# Each tile is [Collision_Type, Graphic_Index]\n")
        f.write("FULL_MAP_DATA = [\n")
        for row in full_map_data:
            f.write(f"    {row},\n")
        f.write("]\n")

    print(f"Success! Map size: {len(full_map_data[0])}x{len(full_map_data)}. Spawn: {spawn_point}")

if __name__ == "__main__":
    extract_data()
