from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from ha2_env import CONTROL_MODE_FULL, CONTROL_MODES

@dataclass
class JobResult:
    command: List[str]
    stdout_log: str
    stderr_log: str
    exit_code: int = -1
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    experiment_path: str | None = None
    timing_report_path: str | None = None

def get_auto_threads() -> int:
    cpu_count = os.cpu_count() or 1
    # max(2, min(8, logical_processors // 4))
    return max(2, min(8, cpu_count // 4))

def create_thread_env(threads: int) -> Dict[str, str]:
    env = os.environ.copy()
    val = str(threads)
    env["OMP_NUM_THREADS"] = val
    env["MKL_NUM_THREADS"] = val
    env["NUMEXPR_NUM_THREADS"] = val
    env["HA2_TORCH_NUM_THREADS"] = val
    return env

def run_job(name: str, args: List[str], env: Dict[str, str], log_dir: Path) -> JobResult:
    stdout_path = log_dir / f"{name}.stdout.log"
    stderr_path = log_dir / f"{name}.stderr.log"
    
    command = [sys.executable, "-m", "scripts.run_experiment"] + args
    start_dt = datetime.now()
    start_tick = time.perf_counter()
    
    print(f"[{start_dt.strftime('%H:%M:%S')}] Starting {name}...")
    
    with open(stdout_path, "w") as f_out, open(stderr_path, "w") as f_err:
        process = subprocess.Popen(
            command,
            stdout=f_out,
            stderr=f_err,
            env=env,
            text=True
        )
        exit_code = process.wait()
    
    end_tick = time.perf_counter()
    end_dt = datetime.now()
    duration = end_tick - start_tick
    
    print(f"[{end_dt.strftime('%H:%M:%S')}] {name} finished with code {exit_code} in {duration:.2f}s")
    
    # Try to parse experiment path from stdout
    exp_path = None
    if stdout_path.exists():
        with open(stdout_path, "r") as f:
            for line in f:
                if "Experiment directory:" in line:
                    exp_path = line.split(":", 1)[1].strip()
                    break

    timing_path = None
    if exp_path:
        tp = Path(exp_path) / "reports" / "timing"
        if tp.exists():
            timing_path = str(tp)

    return JobResult(
        command=command,
        stdout_log=str(stdout_path),
        stderr_log=str(stderr_path),
        exit_code=exit_code,
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat(),
        duration_seconds=duration,
        experiment_path=exp_path,
        timing_report_path=timing_path
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Run A/B experiment pair sequentially or in parallel.")
    parser.add_argument("--mode", choices=["sequential", "parallel", "both"], default="both")
    parser.add_argument("--profile-a", default="combat_v1")
    parser.add_argument("--profile-b", default="combat_bullets_v1")
    parser.add_argument("--control-mode", choices=sorted(CONTROL_MODES), default=CONTROL_MODE_FULL, help="Default control mode for both jobs")
    parser.add_argument("--control-mode-a", choices=sorted(CONTROL_MODES), default=None, help="Control mode for job A (overrides --control-mode)")
    parser.add_argument("--control-mode-b", choices=sorted(CONTROL_MODES), default=None, help="Control mode for job B (overrides --control-mode)")
    parser.add_argument("--label-a", default="job_a")
    parser.add_argument("--label-b", default="job_b")
    parser.add_argument("--seed", type=int, default=0, help="Seed for job A (and job B if --seed-b is not set)")
    parser.add_argument("--seed-b", type=int, default=None, help="Explicit seed for job B. Defaults to the same as --seed.")
    parser.add_argument("--stagger-seconds", type=int, default=60)
    parser.add_argument("--threads-per-job", default="auto")
    
    # Common forwarded args
    parser.add_argument("--total-timesteps", type=int, default=10_000)
    parser.add_argument("--n-envs", type=int, default=1)
    parser.add_argument("--vec-env", default="dummy")
    parser.add_argument("--wandb", default="off")
    parser.add_argument("--train-eval", default="on")
    parser.add_argument("--eval-freq", type=int, default=None)
    parser.add_argument("--eval-freq-timesteps", type=int, default=None)
    parser.add_argument("--train-eval-episodes", type=int, default=5)
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument("--net-arch", type=str, default=None)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--timing-profile", default="on")
    
    args = parser.parse_args()

    num_threads = get_auto_threads() if args.threads_per_job == "auto" else int(args.threads_per_job)
    thread_env = create_thread_env(num_threads)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root_log_dir = Path(f"experiments/pair_{timestamp}")
    root_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Update latest_experiment link to point to the pair root
    latest_link = root_log_dir.parent / "latest_experiment"
    try:
        if latest_link.exists():
            if latest_link.is_symlink():
                latest_link.unlink()
            elif latest_link.is_dir():
                latest_link = None

        if latest_link:
            try:
                os.symlink(root_log_dir.relative_to(root_log_dir.parent), latest_link, target_is_directory=True)
            except (OSError, NotImplementedError):
                (root_log_dir.parent / "latest_experiment.txt").write_text(str(root_log_dir), encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not update latest_experiment link: {e}")

    print(f"Pair benchmark root: {root_log_dir}")
    print(f"Threads per job: {num_threads} (OMP/MKL/TORCH)")
    
    common_args = [
        "--total-timesteps", str(args.total_timesteps),
        "--n-envs", str(args.n_envs),
        "--vec-env", args.vec_env,
        "--wandb", args.wandb,
        "--train-eval", args.train_eval,
        "--train-eval-episodes", str(args.train_eval_episodes),
        "--eval-episodes", str(args.eval_episodes),
        "--device", args.device,
        "--timing-profile", args.timing_profile,
        "--torch-num-threads", str(num_threads)
    ]
    if args.net_arch:
        common_args.extend(["--net-arch", args.net_arch])
    if args.eval_freq:
        common_args.extend(["--eval-freq", str(args.eval_freq)])
    if args.eval_freq_timesteps:
        common_args.extend(["--eval-freq-timesteps", str(args.eval_freq_timesteps)])
    if args.save_replays:
        common_args.append("--save-replays")

    results = {}

    def run_pair(mode_name: str) -> Dict[str, JobResult]:
        pair_dir = root_log_dir / mode_name
        pair_dir.mkdir(exist_ok=True)
        
        control_mode_a = args.control_mode_a if args.control_mode_a is not None else args.control_mode
        control_mode_b = args.control_mode_b if args.control_mode_b is not None else args.control_mode

        # Prevent collisions by always adding timestamp and job suffix
        # Use the same timestamp as the pair folder for consistency
        ts = timestamp # Already defined in main()
        args_a = common_args + [
            "--training-profile", args.profile_a,
            "--control-mode", control_mode_a,
            "--seed", str(args.seed),
            "--experiment-name", f"{ts}_{args.profile_a}_{control_mode_a}_{args.total_timesteps}_a"
        ]
        seed_b = args.seed_b if args.seed_b is not None else args.seed
        args_b = common_args + [
            "--training-profile", args.profile_b,
            "--control-mode", control_mode_b,
            "--seed", str(seed_b),
            "--experiment-name", f"{ts}_{args.profile_b}_{control_mode_b}_{args.total_timesteps}_b"
        ]

        mode_results = {}
        if mode_name == "sequential":
            print(f"\n--- Running Sequential Mode ---")
            mode_results["job_a"] = run_job("sequential_job_a", args_a, thread_env, pair_dir)
            mode_results["job_b"] = run_job("sequential_job_b", args_b, thread_env, pair_dir)
        else:
            print(f"\n--- Running Parallel Mode (Stagger: {args.stagger_seconds}s) ---")
            stdout_a = pair_dir / "parallel_job_a.stdout.log"
            stderr_a = pair_dir / "parallel_job_a.stderr.log"
            stdout_b = pair_dir / "parallel_job_b.stdout.log"
            stderr_b = pair_dir / "parallel_job_b.stderr.log"
            
            cmd_a = [sys.executable, "-m", "scripts.run_experiment"] + args_a
            cmd_b = [sys.executable, "-m", "scripts.run_experiment"] + args_b
            
            start_dt_a = datetime.now()
            start_tick_total = time.perf_counter()
            start_tick_a = start_tick_total
            
            import queue
            import threading
            from collections import deque
            try:
                from rich.live import Live
                from rich.layout import Layout
                from rich.panel import Panel
                from rich.text import Text
            except ImportError as exc:
                raise SystemExit("Error: 'rich' library is required for parallel mode. Run 'pip install -r requirements.txt'") from exc

            log_q = queue.Queue()
            lines_a = deque(maxlen=25)
            lines_b = deque(maxlen=25)
            
            lines_a.append(f"[{start_dt_a.strftime('%H:%M:%S')}] Starting Job A...")
            if args.stagger_seconds > 0:
                lines_b.append(f"[{start_dt_a.strftime('%H:%M:%S')}] Waiting {args.stagger_seconds}s stagger before starting Job B...")

            def update_layout():
                l = Layout()
                l.split_column(
                    Layout(Panel(Text("\n".join(lines_a)), title="[cyan]Job A[/cyan]", border_style="cyan")),
                    Layout(Panel(Text("\n".join(lines_b)), title="[magenta]Job B[/magenta]", border_style="magenta"))
                )
                return l

            def reader_thread(proc, f_out, q_name):
                for line in iter(proc.stdout.readline, ''):
                    f_out.write(line)
                    f_out.flush()
                    log_q.put((q_name, line.rstrip('\n')))
                proc.stdout.close()

            f_out_a = open(stdout_a, "w")
            proc_a = subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=thread_env, text=True, bufsize=1)
            t_a = threading.Thread(target=reader_thread, args=(proc_a, f_out_a, "A"), daemon=True)
            t_a.start()
            
            proc_b = None
            f_out_b = None
            t_b = None
            start_dt_b = None
            start_tick_b = None

            with Live(update_layout(), refresh_per_second=10) as live:
                def process_queue():
                    updated = False
                    while not log_q.empty():
                        job, line = log_q.get_nowait()
                        if job == "A":
                            lines_a.append(line)
                        else:
                            lines_b.append(line)
                        updated = True
                    if updated:
                        live.update(update_layout())

                if args.stagger_seconds > 0:
                    start_wait = time.time()
                    while time.time() - start_wait < args.stagger_seconds:
                        process_queue()
                        if proc_a.poll() is not None:
                            break # Job A finished extremely fast
                        time.sleep(0.1)

                start_dt_b = datetime.now()
                start_tick_b = time.perf_counter()
                lines_b.append(f"[{start_dt_b.strftime('%H:%M:%S')}] Starting Job B...")
                process_queue()
                
                f_out_b = open(stdout_b, "w")
                proc_b = subprocess.Popen(cmd_b, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=thread_env, text=True, bufsize=1)
                t_b = threading.Thread(target=reader_thread, args=(proc_b, f_out_b, "B"), daemon=True)
                t_b.start()
                
                while proc_a.poll() is None or proc_b.poll() is None:
                    process_queue()
                    time.sleep(0.1)
                
                t_a.join()
                t_b.join()
                process_queue()

            exit_a = proc_a.wait()
            end_tick_a = time.perf_counter()
            f_out_a.close()
            Path(stderr_a).touch()
            
            exit_b = proc_b.wait()
            end_tick_b = time.perf_counter()
            f_out_b.close()
            Path(stderr_b).touch()
            
            total_duration = time.perf_counter() - start_tick_total
            
            # Helper to parse exp path
            def get_exp(path: Path):
                if not path.exists(): return None
                with open(path, "r") as f:
                    for line in f:
                        if "Experiment directory:" in line: return line.split(":", 1)[1].strip()
                return None

            def get_timing(exp_path: str | None):
                if exp_path:
                    tp = Path(exp_path) / "reports" / "timing"
                    if tp.exists():
                        return str(tp)
                return None

            exp_a = get_exp(stdout_a)
            exp_b = get_exp(stdout_b)
            mode_results["job_a"] = JobResult(cmd_a, str(stdout_a), str(stderr_a), exit_a, start_dt_a.isoformat(), datetime.now().isoformat(), end_tick_a - start_tick_a, exp_a, get_timing(exp_a))
            mode_results["job_b"] = JobResult(cmd_b, str(stdout_b), str(stderr_b), exit_b, start_dt_b.isoformat(), datetime.now().isoformat(), end_tick_b - start_tick_b, exp_b, get_timing(exp_b))
            mode_results["total_parallel_duration"] = total_duration

        return mode_results

    if args.mode in ["sequential", "both"]:
        results["sequential"] = run_pair("sequential")
    
    if args.mode in ["parallel", "both"]:
        results["parallel"] = run_pair("parallel")

    # Final summary
    summary_path = root_log_dir / "pair_summary.json"
    serializable_results = {}
    for mode, data in results.items():
        serializable_results[mode] = {k: (asdict(v) if isinstance(v, JobResult) else v) for k, v in data.items()}
    
    with open(summary_path, "w") as f:
        json.dump(serializable_results, f, indent=2)
    
    md_lines = ["# Experiment Pair Benchmark Summary", ""]
    md_lines.append(f"- Timestamp: {timestamp}")
    md_lines.append(f"- Threads per job: {num_threads}")
    md_lines.append(f"- Total Logical Processors: {os.cpu_count()}")
    seed_b_val = args.seed_b if args.seed_b is not None else args.seed
    md_lines.append(f"- Job A Seed: {args.seed}")
    md_lines.append(f"- Job B Seed: {seed_b_val}")
    md_lines.append("")
    
    if "sequential" in results:
        seq = results["sequential"]
        total_seq = seq["job_a"].duration_seconds + seq["job_b"].duration_seconds
        md_lines.append("## Sequential Mode")
        md_lines.append(f"- Job A: {seq['job_a'].duration_seconds:.2f}s")
        md_lines.append(f"- Job B: {seq['job_b'].duration_seconds:.2f}s")
        md_lines.append(f"- **Total Wallclock: {total_seq:.2f}s**")
        md_lines.append("")

    if "parallel" in results:
        par = results["parallel"]
        total_par = par["total_parallel_duration"]
        md_lines.append("## Parallel Mode")
        md_lines.append(f"- Job A Duration: {par['job_a'].duration_seconds:.2f}s")
        md_lines.append(f"- Job B Duration: {par['job_b'].duration_seconds:.2f}s")
        md_lines.append(f"- **Total Wallclock (Concurrent): {total_par:.2f}s**")
        md_lines.append("")
        
        md_lines.append("### Replay Inspection")
        for job_name in ["job_a", "job_b"]:
            job_res = par.get(job_name)
            if job_res and job_res.experiment_path:
                md_lines.append(f"#### {job_name} ({job_res.experiment_path})")
                md_lines.append(f"- Watch best: `python -m scripts.watch_model --experiment {job_res.experiment_path} --model-choice best`")
                md_lines.append(f"- Watch latest: `python -m scripts.watch_model --experiment {job_res.experiment_path} --model-choice latest`")
        md_lines.append("")

    if "sequential" in results and "parallel" in results:
        total_seq = results["sequential"]["job_a"].duration_seconds + results["sequential"]["job_b"].duration_seconds
        total_par = results["parallel"]["total_parallel_duration"]
        speedup = total_seq / total_par
        md_lines.append("## Comparison")
        md_lines.append(f"- **Sequential Total:** {total_seq:.2f}s")
        md_lines.append(f"- **Parallel Total:** {total_par:.2f}s")
        md_lines.append(f"- **Calculated Speedup: {speedup:.2f}x**")
        md_lines.append("")
        if speedup > 1.05:
            md_lines.append("[+] Parallel mode is significantly faster.")
        elif speedup < 0.95:
            md_lines.append("[-] Parallel mode is significantly slower (oversubscription?).")
        else:
            md_lines.append("[i] No significant difference between modes.")

    with open(root_log_dir / "pair_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    
    print(f"\nFinal summary written to {root_log_dir}")
    
    # Create the consolidated pair diagnostic bundle
    print("\n=== Creating Pair Diagnostic Bundle ===")
    import zipfile
    bundle_path = root_log_dir / f"{root_log_dir.name}_diagnostic_bundle.zip"
    bundled_count = 0
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add summary files
        for sum_file in ["pair_summary.json", "pair_summary.md"]:
            sf = root_log_dir / sum_file
            if sf.exists():
                zipf.write(sf, arcname=sum_file)
                bundled_count += 1
                
        # Define files to collect from each experiment
        exp_files = [
            "config.json",
            "git_info.txt",
            "summary.md",
            "reports/eval_best.json",
            "reports/eval_latest.json",
            "replays/best_eval_ep0.jsonl",
            "replays/latest_eval_ep0.jsonl",
            "reports/timing/train_timing.json",
            "reports/timing/train_timing.md",
            "reports/timing/orchestration_timing.json",
            "reports/timing/orchestration_timing.md",
        ]
        
        # Add job specific artifacts
        for mode, data in results.items():
            for job_name in ["job_a", "job_b"]:
                job: JobResult = data.get(job_name)
                if not job: continue
                
                # Create a subfolder name based on mode and job label to prevent collisions
                # If only one mode is used, keep it clean.
                folder_name = f"{mode}_{job_name}" if len(results) > 1 else job_name
                
                # Add stdout/stderr
                for log_file in [job.stdout_log, job.stderr_log]:
                    if log_file and Path(log_file).exists():
                        zipf.write(log_file, arcname=f"{folder_name}/{Path(log_file).name}")
                        bundled_count += 1
                
                # Add experiment artifacts
                if job.experiment_path:
                    exp_dir = Path(job.experiment_path)
                    for rel_file in exp_files:
                        f_path = exp_dir / rel_file
                        if f_path.exists():
                            zipf.write(f_path, arcname=f"{folder_name}/{f_path.name}")
                            bundled_count += 1
                            
    print(f"Created pair bundle {bundle_path} with {bundled_count} files.")
    
    # Exit status
    failed = False
    for mode in results.values():
        for k, v in mode.items():
            if isinstance(v, JobResult) and v.exit_code != 0:
                failed = True
                break
    if failed:
        print("One or more jobs failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
