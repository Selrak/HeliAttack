# Heli Attack 2 (HA2) Python Simulator: Project Summary

This document outlines the architectural decisions and technical implementation of the native Python port of Heli Attack 2, designed for high-performance Reinforcement Learning (RL) training using Gymnasium and Stable Baselines 3.

---

## 1. Architectural & Technical Decisions

The development of this simulator was guided by several high-level technical decisions to ensure that an AI trained in this environment would have a high degree of transferability to the original game logic.

* **Decision: "Bit-for-Bit" Parity**
    * **Philosophy**: Prioritize absolute logic and physics parity over modern game development approximations.
    * **Rationale**: To ensure the AI learns the exact "jank" and quirks of the 2004 Flash engine (e.g., specific pixel-snapping, double-jump windows), every physics calculation is a direct 1:1 translation of the decompiled ActionScript 2 (AS2) source.
* **Decision: Automated Data Extraction**
    * **Philosophy**: Decouple static game data (maps, weapon stats) from simulation logic.
    * **Rationale**: By using a dedicated parser to convert AS2 arrays into Python-native formats, the environment remains robust to source code updates and simplifies the management of the 14+ distinct weapon systems and complex tilemaps.
* **Decision: Multi-Mode Gymnasium Interface**
    * **Philosophy**: Support high-speed headless training on Linux servers while maintaining visual debug capabilities for Windows developers.
    * **Rationale**: The environment supports `human` (live Pygame window), `rgb_array` (pixel-buffer for recording), and `console` modes.
* **Decision: Multi-Discrete Action Space**
    * **Philosophy**: Model the AI's interaction as a physical keyboard.
    * **Rationale**: Using a `MultiDiscrete` action space allows the agent to learn simultaneous key combinations (e.g., Jump + Move Right + Shoot) which are required for high-level survival in HA2.
* **Decision: Asynchronous Data I/O**
    * **Philosophy**: Offload heavy rendering and file-writing tasks to background threads.
    * **Rationale**: A threaded recorder ensures that GIF generation during evaluations does not slow down the simulation steps, maximizing training FPS.

---

## 2. Implementation: What Was Built

### A. Data Extraction Layer (`extract_ha2_data.py`)
A custom extraction script was built to bridge the gap between the Flash repo and the Python workspace:
* **Map Parsing**: Uses Regex and `ast.literal_eval` to rip the multi-dimensional `map1` array directly from the source.
* **Constant Generation**: Automatically generates `ha2_constants.py`, containing ground-truth physics values (Gravity: 1.0, Max Walk Speed: 5.0, Friction: 1.0) and weapon dictionaries.

### B. Gymnasium Environment (`ha2_env.py`)
The core simulation engine that implements the Gymnasium standard:
* **Physics Engine**: Replicates the original ActionScript logic, including the 6-frame thrust-based jumping, the inverted Y-axis coordinate system, and exact pixel-perfect AABB collision resolution with "anti-snag" offsets.
* **State Management**: Tracks the 150-tick "HyperJump" meter, player health, velocities, and directional facing.
* **Ducking Mechanics**: Implements the native AS2 behavior of shrinking the hitbox from the center and applying a 6.66-pixel upward shift when standing to prevent floor clipping.

### C. Rendering & Recording Engine
* **Native Asset Mapping**: Uses the original `.png` assets (`guy.png`, `Floor2.png`, etc.). It implements a specialized mapping to handle Flash's 1-indexed frame behavior (`tile[1] + 1`), ensuring a continuous, non-fragmented floor surface.
* **Parallax Camera**: Replicates the Flash engine’s dynamic camera tracking and background parallax scrolling logic.
* **Threaded GifRecorder**: A background `daemon` thread that collects frames via a `queue` and compiles them asynchronously into `.gif` files, allowing the main training loop to run at maximum speed.

---

## 3. Current State of the Simulator

The environment currently features a fully functional **Phase 1: Foundation**:
1.  **Bit-Perfect Physics**: The player can move, jump, double-jump, duck, and use HyperJumps exactly as in the original game.
2.  **Environment Parity**: The world map is correctly loaded with physical collision and visual tile alignment.
3.  **Headless Support**: Ready for training on SSH-only Linux servers with automated replay generation.

**Next Phase**: Implementation of the Helicopter AI (fractional acceleration tracking), projectile management (bullets, rockets, grenades), and RL reward shaping.