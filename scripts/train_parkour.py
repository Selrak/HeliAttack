from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from ha2_env import HeliAttack2Env


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
    parser.add_argument("--tensorboard-log", type=Path, default=Path("runs/tensorboard"))
    parser.add_argument("--wandb", choices=["off", "on"], default="off")
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1"], default="combat_v1")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    args = parser.parse_args()

    PPO, CheckpointCallback, EvalCallback, Monitor, DummyVecEnv = _load_sb3()
    models_dir = Path("models")
    checkpoint_dir = models_dir / "checkpoints"
    models_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    args.tensorboard_log.mkdir(parents=True, exist_ok=True)

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
        CheckpointCallback(save_freq=5_000, save_path=str(checkpoint_dir), name_prefix="ha2"),
        EvalCallback(
            eval_env,
            best_model_save_path=str(models_dir),
            log_path=str(Path("reports")),
            eval_freq=max(1_000, args.n_envs),
            deterministic=True,
        ),
    ]

    if args.wandb == "on":
        try:
            import wandb
            from wandb.integration.sb3 import WandbCallback
        except ModuleNotFoundError as exc:
            raise SystemExit("wandb is not installed; rerun with --wandb off.") from exc
        wandb.init(project="heliattack", config=vars(args), sync_tensorboard=True)
        callbacks.append(WandbCallback(verbose=1))

    model = PPO(
        "MlpPolicy",
        env,
        seed=args.seed,
        verbose=1,
        tensorboard_log=str(args.tensorboard_log),
        device=args.device,
    )
    model.learn(total_timesteps=args.total_timesteps, callback=callbacks)
    model.save(models_dir / "latest")

    best_model = models_dir / "best_model.zip"
    if best_model.exists():
        shutil.copyfile(best_model, models_dir / "best.zip")

    env.close()
    eval_env.close()
    print(f"Saved latest model to {models_dir / 'latest.zip'}")


if __name__ == "__main__":
    main()
