from __future__ import annotations

import time
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
except ImportError:
    # Fallback for environments without SB3
    class PPO:
        pass
    class BaseCallback:
        def __init__(self, verbose: int = 0): pass

@dataclass
class TrainingTiming:
    total_training_wallclock: float = 0.0
    rollout_total: float = 0.0
    rollout_count: int = 0
    train_update_total: float = 0.0
    train_update_count: int = 0
    train_eval_total: float = 0.0
    train_eval_count: int = 0
    
    # Metadata
    total_requested_timesteps: int = 0
    n_envs: int = 1
    vec_env: str = "dummy"
    training_profile: str = "combat_v1"
    net_arch: str = "default"
    torch_num_threads: int | None = None
    omp_num_threads: str | None = None
    mkl_num_threads: str | None = None
    
    @property
    def other_overhead(self) -> float:
        return self.total_training_wallclock - (self.rollout_total + self.train_update_total)

    def to_json(self, path: Path):
        data = asdict(self)
        data["other_or_unclassified_training_seconds"] = self.other_overhead
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def to_markdown(self, path: Path):
        lines = [
            "# Training Timing Report",
            "",
            "| Phase | Total Seconds | Count | Mean Seconds |",
            "|---|---|---|---|",
            f"| Rollout Collection | {self.rollout_total:.2f} | {self.rollout_count} | {self.rollout_total/self.rollout_count if self.rollout_count > 0 else 0:.4f} |",
            f"| PPO Update (Train) | {self.train_update_total:.2f} | {self.train_update_count} | {self.train_update_total/self.train_update_count if self.train_update_count > 0 else 0:.4f} |",
            f"| Unclassified Overhead | {self.other_overhead:.2f} | n/a | n/a |",
            f"| **Total Training** | **{self.total_training_wallclock:.2f}** | n/a | n/a |",
            "",
            "*(Note: Train-time eval overlaps with Rollout Collection callbacks and is not subtracted from total)*",
            f"- Overlapping Train-time Eval: {self.train_eval_total:.2f}s ({self.train_eval_count} calls)",
            "",
            "## Metadata",
            "",
            f"- Requested Timesteps: {self.total_requested_timesteps}",
            f"- n_envs: {self.n_envs}",
            f"- vec_env: {self.vec_env}",
            f"- profile: {self.training_profile}",
            f"- net_arch: {self.net_arch}",
            f"- torch_threads: {self.torch_num_threads}",
        ]
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")

_current_timing: TrainingTiming | None = None

def set_current_timing(timing: TrainingTiming | None):
    global _current_timing
    _current_timing = timing

class TimedPPO(PPO):
    """Subclass of PPO to record accurate timings without monkey-patching instances."""
    def collect_rollouts(self, env, callback, rollout_buffer, n_rollout_steps):
        if _current_timing is None:
            return super().collect_rollouts(env, callback, rollout_buffer, n_rollout_steps)
        start = time.perf_counter()
        res = super().collect_rollouts(env, callback, rollout_buffer, n_rollout_steps)
        _current_timing.rollout_total += time.perf_counter() - start
        _current_timing.rollout_count += 1
        return res

    def train(self) -> None:
        if _current_timing is None:
            return super().train()
        start = time.perf_counter()
        super().train()
        _current_timing.train_update_total += time.perf_counter() - start
        _current_timing.train_update_count += 1

def wrap_eval_callback_timing(eval_callback: Any, timing: TrainingTiming):
    """
    Monkey-patch EvalCallback._on_step to record timing.
    This is still needed because EvalCallback is not easily measured via TimingCallback
    since they run at the same 'level' in the callback list.
    """
    if eval_callback is None:
        return
    
    original_on_step = eval_callback._on_step

    def timed_on_step(*args, **kwargs):
        # In SB3, n_calls is incremented in BaseCallback.on_step() before calling _on_step()
        is_eval_step = eval_callback.eval_freq > 0 and eval_callback.n_calls % eval_callback.eval_freq == 0
        
        start = time.perf_counter()
        res = original_on_step(*args, **kwargs)
        duration = time.perf_counter() - start
        
        if is_eval_step:
            timing.train_eval_total += duration
            timing.train_eval_count += 1
        return res

    eval_callback._on_step = timed_on_step
