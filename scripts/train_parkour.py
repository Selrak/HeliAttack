from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import shutil

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ha2_env import (
    CONTROL_MODE_FULL,
    CONTROL_MODES,
    FULL_SIM_ACTION_NVEC,
    make_controlled_env,
)
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
        from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "stable-baselines3 is not installed. Install requirements before training."
        ) from exc
    return PPO, CheckpointCallback, EvalCallback, Monitor, DummyVecEnv, SubprocVecEnv


@dataclass(frozen=True)
class EnvFactory:
    rank: int
    seed: int
    training_profile: str
    max_episode_steps: int
    control_mode: str = "full"

    def __call__(self):
        from stable_baselines3.common.monitor import Monitor

        env = make_controlled_env(
            render_mode=None,
            control_mode=self.control_mode,
            training_profile=self.training_profile,
            max_episode_steps=self.max_episode_steps,
        )
        env.reset(seed=self.seed + self.rank)
        return Monitor(env)


def make_vec_env(
    *,
    vec_env: str,
    n_envs: int,
    seed: int,
    training_profile: str,
    max_episode_steps: int,
    monitor_cls,
    dummy_vec_env_cls,
    subproc_vec_env_cls,
    control_mode: str = "full",
):
    env_fns = [
        EnvFactory(
            rank=i,
            seed=seed,
            training_profile=training_profile,
            max_episode_steps=max_episode_steps,
            control_mode=control_mode,
        )
        for i in range(n_envs)
    ]
    if vec_env == "dummy":
        return dummy_vec_env_cls(env_fns)
    if vec_env == "subproc":
        return subproc_vec_env_cls(env_fns)
    raise ValueError(f"Unknown vec_env: {vec_env}")


def effective_eval_vec_env(train_vec_env: str, eval_vec_env: str) -> str:
    if eval_vec_env == "same":
        return train_vec_env
    return eval_vec_env

def main(args_list: list[str] | None = None) -> ExperimentLayout:
    parser = argparse.ArgumentParser(description="Minimal HA2 parkour PPO training.")
    parser.add_argument("--total-timesteps", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-envs", type=int, default=1)
    parser.add_argument("--vec-env", choices=["dummy", "subproc"], default="dummy")
    parser.add_argument("--train-eval", choices=["on", "off"], default="on")
    parser.add_argument("--eval-freq", type=int, default=None, help="Evaluation frequency in vector steps (once per n-envs).")
    parser.add_argument("--eval-freq-timesteps", type=int, default=None, help="Evaluation frequency in total timesteps (will be divided by n-envs).")
    parser.add_argument("--train-eval-episodes", type=int, default=5)
    parser.add_argument("--eval-vec-env", choices=["dummy", "subproc", "same"], default="dummy")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--tensorboard-log", type=Path, default=None)
    parser.add_argument("--wandb", choices=["off", "on"], default="off")
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1", "combat_bullets_v1"], default="combat_v1")
    parser.add_argument("--control-mode", choices=sorted(CONTROL_MODES), default=CONTROL_MODE_FULL)
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    parser.add_argument("--experiments-root", type=Path, default=Path("experiments"))
    parser.add_argument("--experiment-dir", type=Path, default=None)
    parser.add_argument("--experiment-name", type=str, default=None)
    parser.add_argument("--resume-from", type=Path, default=None)
    parser.add_argument("--no-wandb-finish", action="store_true", help="Skip artifact upload and wandb finish (for orchestration).")
    parser.add_argument("--mirror-root-models", action="store_true")
    parser.add_argument("--net-arch", type=str, default=None, help="Comma-separated list of hidden layer sizes (e.g. '128,128')")
    parser.add_argument("--timing-profile", choices=["on", "off"], default="off")
    parser.add_argument("--torch-num-threads", type=int, default=None)
    args = parser.parse_args(args_list)

    # Compute effective eval_freq
    effective_eval_freq = args.eval_freq
    if args.eval_freq_timesteps is not None:
        effective_eval_freq = max(1, args.eval_freq_timesteps // args.n_envs)
    if effective_eval_freq is None:
        effective_eval_freq = max(1000, args.n_envs) # Default

    if effective_eval_freq <= 0:
        raise SystemExit("--eval-freq must be positive")
    if args.train_eval_episodes <= 0:
        raise SystemExit("--train-eval-episodes must be positive")

    import torch
    effective_torch_threads = args.torch_num_threads or int(os.environ.get("HA2_TORCH_NUM_THREADS", 0)) or None
    if effective_torch_threads:
        torch.set_num_threads(effective_torch_threads)

    policy_kwargs = {}
    if args.net_arch:
        try:
            net_arch = [int(x.strip()) for x in args.net_arch.split(",")]
            policy_kwargs["net_arch"] = dict(pi=net_arch, vf=net_arch)
        except ValueError as exc:
            raise SystemExit(f"Invalid --net-arch format. Expected comma-separated integers, got: {args.net_arch}") from exc

    PPO, CheckpointCallback, EvalCallback, Monitor, DummyVecEnv, SubprocVecEnv = _load_sb3()
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
        "vec_env": args.vec_env,
        "train_eval": args.train_eval,
        "eval_freq": int(args.eval_freq) if args.eval_freq is not None else None,
        "train_eval_episodes": int(args.train_eval_episodes),
        "eval_vec_env": args.eval_vec_env,
        "effective_eval_vec_env": effective_eval_vec_env(args.vec_env, args.eval_vec_env),
        "device": args.device,
        "training_profile": args.training_profile,
        "control_mode": args.control_mode,
        "max_episode_steps": int(args.max_episode_steps),
        "wandb": args.wandb,
        "tensorboard_log": str(tensorboard_log),
        "mirror_root_models": bool(args.mirror_root_models),
        "resume_from": str(args.resume_from) if args.resume_from is not None else None,
        "net_arch": args.net_arch if args.net_arch else "default",
    }
    write_json_file(layout.config_path, config)
    write_text_file(layout.git_info_path, git_info_text(repo_root), allow_overwrite=True)

    training_timing = None
    if args.timing_profile == "on":
        from scripts.runtime_timing import TrainingTiming
        training_timing = TrainingTiming(
            total_requested_timesteps=args.total_timesteps,
            n_envs=args.n_envs,
            vec_env=args.vec_env,
            training_profile=args.training_profile,
            net_arch=args.net_arch or "default",
            torch_num_threads=effective_torch_threads,
            omp_num_threads=os.environ.get("OMP_NUM_THREADS"),
            mkl_num_threads=os.environ.get("MKL_NUM_THREADS"),
        )

    env = make_vec_env(
        vec_env=args.vec_env,
        n_envs=args.n_envs,
        seed=args.seed,
        training_profile=args.training_profile,
        control_mode=args.control_mode,
        max_episode_steps=args.max_episode_steps,
        monitor_cls=Monitor,
        dummy_vec_env_cls=DummyVecEnv,
        subproc_vec_env_cls=SubprocVecEnv,
    )
    config["policy_action_space_nvec"] = [int(v) for v in env.action_space.nvec.tolist()]
    config["sim_action_space_nvec"] = FULL_SIM_ACTION_NVEC.copy()
    write_json_file(layout.config_path, config, allow_overwrite=True)

    callbacks = [
        CheckpointCallback(save_freq=5_000, save_path=str(layout.checkpoints_dir), name_prefix="ha2"),
    ]
    eval_env = None
    if args.train_eval == "on":
        eval_env_name = effective_eval_vec_env(args.vec_env, args.eval_vec_env)
        eval_env = make_vec_env(
            vec_env=eval_env_name,
            n_envs=1,
            seed=args.seed + 10_000,
            training_profile=args.training_profile,
            control_mode=args.control_mode,
            max_episode_steps=args.max_episode_steps,
            monitor_cls=Monitor,
            dummy_vec_env_cls=DummyVecEnv,
            subproc_vec_env_cls=SubprocVecEnv,
        )
        callbacks.append(
            EvalCallback(
                eval_env,
                best_model_save_path=str(layout.models_dir),
                log_path=str(layout.reports_dir),
                eval_freq=effective_eval_freq,
                n_eval_episodes=args.train_eval_episodes,
                deterministic=True,
            )
        )

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
        PPOClass = PPO
        if training_timing:
            from scripts.runtime_timing import TimedPPO, set_current_timing
            PPOClass = TimedPPO
            set_current_timing(training_timing)
            
        model = PPOClass(
            "MlpPolicy",
            env,
            seed=args.seed,
            verbose=1,
            tensorboard_log=str(tensorboard_log),
            device=args.device,
            policy_kwargs=policy_kwargs if policy_kwargs else None,
        )

    # Try to extract parameter count and activation fn to update config
    try:
        total_params = sum(p.numel() for p in model.policy.parameters() if p.requires_grad)
        config["trainable_parameters"] = total_params
        if hasattr(model.policy, "activation_fn"):
            config["activation_fn"] = model.policy.activation_fn.__name__
        write_json_file(layout.config_path, config, allow_overwrite=True)
    except Exception as e:
        print(f"Warning: Could not update config with policy metadata: {e}")

    if training_timing:
        from scripts.runtime_timing import wrap_eval_callback_timing
        # Find EvalCallback in callbacks list
        eval_cb = next((cb for cb in callbacks if isinstance(cb, EvalCallback)), None)
        if eval_cb:
            wrap_eval_callback_timing(eval_cb, training_timing)

    import time
    train_start_wall = time.perf_counter()
    model.learn(total_timesteps=args.total_timesteps, callback=callbacks)
    train_duration = time.perf_counter() - train_start_wall

    if training_timing:
        from scripts.runtime_timing import set_current_timing
        set_current_timing(None)
        training_timing.total_training_wallclock = train_duration
        timing_dir = layout.path / "reports" / "timing"
        timing_dir.mkdir(parents=True, exist_ok=True)
        training_timing.to_json(timing_dir / "train_timing.json")
        training_timing.to_markdown(timing_dir / "train_timing.md")
        print(f"Wrote training timing report to {timing_dir}")

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
        f"- control_mode: `{args.control_mode}`",
        f"- policy_action_space_nvec: `{config.get('policy_action_space_nvec')}`",
        f"- sim_action_space_nvec: `{config.get('sim_action_space_nvec')}`",
        f"- total_timesteps: `{args.total_timesteps}`",
        f"- seed: `{args.seed}`",
        f"- n_envs: `{args.n_envs}`",
        f"- vec_env: `{args.vec_env}`",
        f"- train_eval: `{args.train_eval}`",
        f"- eval_vec_env: `{args.eval_vec_env}`",
        f"- effective_eval_vec_env: `{effective_eval_vec_env(args.vec_env, args.eval_vec_env)}`",
        f"- eval_freq: `{effective_eval_freq}`",
        f"- eval_freq_timesteps: `{args.eval_freq_timesteps}`",
        f"- train_eval_episodes: `{args.train_eval_episodes}`",
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
    if eval_env is not None:
        eval_env.close()
    print(f"Saved latest model to {layout.models_dir / 'latest.zip'}")
    print(f"Experiment directory: {layout.path}")

    if args.wandb == "on" and not args.no_wandb_finish:
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

    return layout

if __name__ == "__main__":
    main()
