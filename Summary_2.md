Heli Attack 2 AI Project: Phase 1 Summary
The project has established a high-fidelity reinforcement learning pipeline for Heli Attack 2 (HA2), successfully replicating the original Flash game logic within a modern AI training framework.

1. High-Fidelity Physics Simulation
A custom Python environment (HeliAttack2Env) has been built to serve as the core simulator.

Bit-for-Bit Logic: The simulator reproduces the exact physics of the original ActionScript code, including gravity, velocity clamping, and complex player states like ducking, double-jumping, and "HyperJumping" (boosts).

Collision System: It utilizes a tile-based collision grid system that exactly matches the original game's map data and player hitboxes.

Graphics & Debugging: The environment features a Pygame renderer using original assets and includes a --record mode for visual debugging and training evaluation.

2. Strategic AI Architecture
Observation Space: The AI utilizes a vectorized RAM state approach rather than raw pixels. It currently observes a 1D state vector containing the player's precise coordinates and velocity ([x, y, xspeed, yspeed]).

Action Space: The control scheme is mapped to a MultiDiscrete action space, allowing the AI to simultaneously control movement (Left/Idle/Right), jumping, ducking, and boosting.

Learning Algorithm: The project uses Proximal Policy Optimization (PPO) with a Multi-Layer Perceptron (MlpPolicy). This setup is specifically chosen for its stability and efficiency with vectorized physics data.

3. Training & Experiment Tracking
Integrated Pipeline: The training workflow is powered by Stable Baselines 3 and fully integrated with Weights & Biases (W&B).

Telemetry: All training metrics, including rewards, policy entropy, and episode lengths, are streamed in real-time to a cloud dashboard.

Cloud Checkpointing: The system automatically manages model checkpoints and gradient logging, allowing for a seamless development workflow between local Windows machines and remote Ubuntu workstations.

4. Current Objective: Parkour Survival
The project is currently in the "Parkour Survival" phase. The AI is incentivized via a dense reward structure (+0.1 per tick) to navigate the terrain and survive indefinitely, with a significant penalty (-10.0) for falling off the map. This provides a stable baseline for movement before combat mechanics and enemy helicopters are introduced.