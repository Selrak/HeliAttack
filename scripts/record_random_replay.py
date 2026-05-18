from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter
from scripts.runtime_config import parse_human_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a deterministic random HA2 replay.")
    parser.add_argument("--steps", type=parse_human_count, default=300)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=Path("replays/smoke.jsonl"))
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    env = HeliAttack2Env(render_mode=None)
    obs, _info = env.reset(seed=args.seed)

    steps_written = 0
    try:
        with JsonlReplayWriter(args.out, env, args.seed, obs) as writer:
            nvec = np.asarray(env.action_space.nvec, dtype=np.int64)
            for _ in range(args.steps):
                action = rng.integers(0, nvec).astype(int).tolist()
                obs, reward, terminated, truncated, info = env.step(action)
                writer.append_step(env, action, obs, reward, terminated, truncated, info)
                steps_written += 1
                if terminated or truncated:
                    break
    finally:
        env.close()

    print(f"Wrote {steps_written} steps to {args.out}")


if __name__ == "__main__":
    main()
