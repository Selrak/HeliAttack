from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync HA2 experiments from wandb.")
    parser.add_argument("experiment_name", help="Name of the experiment artifact (e.g. ha2_000001_...)")
    parser.add_argument("--project", default="heliattack", help="Wandb project name")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY", "charles-thinnp"), help="Wandb entity/username")
    parser.add_argument("--experiments-root", type=Path, default=Path("experiments"), help="Local experiments root")
    parser.add_argument("--version", default="latest", help="Artifact version (e.g. 'v0', 'latest')")
    args = parser.parse_args()

    try:
        import wandb
    except ModuleNotFoundError:
        raise SystemExit("wandb is not installed. Run 'pip install wandb'.")

    # Initialize wandb for API access
    api = wandb.Api()
    
    # Construct artifact path
    entity = args.entity or api.default_entity
    artifact_path = f"{entity}/{args.project}/{args.experiment_name}:{args.version}"
    
    print(f"Fetching artifact: {artifact_path}")
    try:
        artifact = api.artifact(artifact_path)
    except wandb.errors.CommError as exc:
        raise SystemExit(f"Could not find artifact: {artifact_path}\nError: {exc}")

    # Define local target path
    local_path = args.experiments_root / args.experiment_name
    
    if local_path.exists():
        print(f"Warning: Local directory {local_path} already exists.")
        confirm = input("Overwrite? (y/N): ").lower()
        if confirm != "y":
            print("Sync cancelled.")
            return
        shutil.rmtree(local_path)

    local_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading to: {local_path}")
    # Artifact download usually downloads into a 'artifacts/' folder by default.
    # We want it specifically in our local_path.
    download_dir = artifact.download(root=str(local_path))
    
    print(f"\nSuccessfully synced {args.experiment_name} to {local_path}")
    print("You can now run:")
    print(f"  python -m scripts.watch_model --experiment {local_path} --model-choice best")


if __name__ == "__main__":
    main()
