from __future__ import annotations

import argparse
from pathlib import Path

from ha2_replay import REPLAY_ENV_CHOICES, verify_replay_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a deterministic HA2 replay.")
    parser.add_argument("replay", type=Path)
    parser.add_argument("--replay-env", choices=REPLAY_ENV_CHOICES, default="recorded")
    args = parser.parse_args()

    steps = verify_replay_file(args.replay, replay_env=args.replay_env)
    print(f"Replay verified: {args.replay} ({steps} steps, replay_env={args.replay_env})")


if __name__ == "__main__":
    main()
