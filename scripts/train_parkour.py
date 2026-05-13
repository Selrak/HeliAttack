from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ha2_env import HeliAttack2Env
from scripts.experiment_utils import (
    create_experiment_layout,
    git_info_text,
    write_json_file,
    write_text_file,
)


def _load_sb3():
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
        from stable_baselines3.common.monitor import Monitor
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "stable-baselines3 is not installed. Install requirements before training."
        ) from exc
    return PPO, CheckpointCallback, EvalCallback, Monitor, DummyVecEnv


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal HA2 parkour PPO training.")
    parser.add_argument("--total-timesteps", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-envs", type=int, default=1)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--tensorboard-log", type=Path, default=None)
    parser.add_argument("--wandb", choices=["off", "on"], default="off")
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1"], default="combat_v1")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    parser.add_argument("--experiments-root", type=Path, default=Path("experiments"))
    parser.add_argument("--experiment-dir", type=Path, default=None)
    parser.add_argument("--experiment-name", type=str, default=None)
    parser.add_argument("--resume-from", type=Path, default=None)
    parser.add_argument("--mirror-root-models", action="store_true")
    args = parser.parse_args()

    PPO, CheckpointCallback, EvalCallback, Monitor, DummyVecEnv = _load_sb3()
    repo_root = Path(__file__).resolve().parents[1]
    layout = create_experiment_layout(
        experiments_root=args.experiments_root,
        experiment_dir=args.experiment_dir,
        experiment_name=args.experiment_name,
        training_profile=args.training_profile,
        total_timesteps=args.total_timesteps,
        now=datetime.now(),
    )
    tensorboard_log = args.tensorboard_log or layout.tensorboard_dir
    tensorboard_log.mkdir(parents=True, exist_ok=True)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_dir": str(layout.path),
        "experiments_root": str(layout.root),
        "total_timesteps": int(args.total_timesteps),
        "seed": int(args.seed),
        "n_envs": int(args.n_envs),
        "device": args.device,
        "training_profile": args.training_profile,
        "max_episode_steps": int(args.max_episode_steps),
        "wandb": args.wandb,
        "tensorboard_log": str(tensorboard_log),
        "mirror_root_models": bool(args.mirror_root_models),
        "resume_from": str(args.resume_from) if args.resume_from is not None else None,
    }
    write_json_file(layout.config_path, config)
    write_text_file(layout.git_info_path, git_info_text(repo_root), allow_overwrite=True)

    def make_env(rank: int):
        def _init():
            env = HeliAttack2Env(
                render_mode=None,
                training_profile=args.training_profile,
                max_episode_steps=args.max_episode_steps,
            )
            env.reset(seed=args.seed + rank)
            return Monitor(env)

        return _init

    env = DummyVecEnv([make_env(i) for i in range(args.n_envs)])
    eval_env = Monitor(
        HeliAttack2Env(
            render_mode=None,
            training_profile=args.training_profile,
            max_episode_steps=args.max_episode_steps,
        )
    )

    callbacks = [
        CheckpointCallback(save_freq=5_000, save_path=str(layout.checkpoints_dir), name_prefix="ha2"),
        EvalCallback(
            eval_env,
            best_model_save_path=str(layout.models_dir),
            log_path=str(layout.reports_dir),
            eval_freq=max(1_000, args.n_envs),
            deterministic=True,
        ),
    ]

    if args.wandb == "on":
        # Set API key in environment BEFORE importing/initializing wandb
        api_key = os.environ.get("WANDB_API_KEY")
        if api_key:
            os.environ["WANDB_API_KEY"] = api_key
            
        try:
            import wandb
            from wandb.integration.sb3 import WandbCallback
        except ModuleNotFoundError as exc:
            raise SystemExit("wandb is not installed; rerun with --wandb off.") from exc
        
        entity = os.environ.get("WANDB_ENTITY")
        project = os.environ.get("WANDB_PROJECT", "heliattack")
        
        wandb.init(
            project=project,
            entity=entity,
            dir=str(layout.path / "wandb"),
            config=config,
            sync_tensorboard=True
        )
        callbacks.append(WandbCallback(verbose=1))

    if args.resume_from is not None:
        model = PPO.load(args.resume_from, env=env, device=args.device)
        model.tensorboard_log = str(tensorboard_log)
    else:
        model = PPO(
            "MlpPolicy",
            env,
            seed=args.seed,
            verbose=1,
            tensorboard_log=str(tensorboard_log),
            device=args.device,
        )
    model.learn(total_timesteps=args.total_timesteps, callback=callbacks)
    latest_model = layout.models_dir / "latest"
    model.save(latest_model)

    best_model = layout.models_dir / "best_model.zip"
    if best_model.exists():
        shutil.copyfile(best_model, layout.models_dir / "best.zip")

    if args.mirror_root_models:
        root_models = Path("models")
        root_models.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(latest_model.with_suffix(".zip"), root_models / "latest.zip")
        if best_model.exists():
            shutil.copyfile(layout.models_dir / "best.zip", root_models / "best.zip")

    summary_lines = [
        "# HA2 Experiment Summary",
        "",
        f"- experiment: `{layout.path}`",
        f"- training_profile: `{args.training_profile}`",
        f"- total_timesteps: `{args.total_timesteps}`",
        f"- seed: `{args.seed}`",
        f"- n_envs: `{args.n_envs}`",
        f"- device: `{args.device}`",
        f"- tensorboard_log: `{tensorboard_log}`",
        f"- latest_model: `{layout.models_dir / 'latest.zip'}`",
        f"- best_model: `{layout.models_dir / 'best.zip'}`" if best_model.exists() else "- best_model: `not produced`",
        f"- checkpoints: `{layout.checkpoints_dir}`",
        f"- reports: `{layout.reports_dir}`",
        f"- replays: `{layout.replays_dir}`",
    ]
    write_text_file(layout.summary_path, "\n".join(summary_lines) + "\n", allow_overwrite=True)

    env.close()
    eval_env.close()
    print(f"Saved latest model to {layout.models_dir / 'latest.zip'}")
    print(f"Experiment directory: {layout.path}")

    if args.wandb == "on":
        import wandb

        print(f"Uploading experiment artifacts to wandb...")
        artifact = wandb.Artifact(
            name=layout.path.name,
            type="experiment",
            metadata=config,
        )
        # Upload all files in the experiment directory except the wandb/ folder itself
        for item in layout.path.iterdir():
            if item.name == "wandb":
                continue
            if item.is_dir():
                artifact.add_dir(str(item), name=item.name)
            else:
                artifact.add_file(str(item), name=item.name)
        wandb.log_artifact(artifact)
        wandb.finish()


if __name__ == "__main__":
    main()
