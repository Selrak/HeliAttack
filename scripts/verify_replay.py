from __future__ import annotations

import argparse
from pathlib import Path

from ha2_replay import verify_replay_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a deterministic HA2 replay.")
    parser.add_argument("replay", type=Path)
    args = parser.parse_args()

    steps = verify_replay_file(args.replay)
    print(f"Replay verified: {args.replay} ({steps} steps)")


if __name__ == "__main__":
    main()
