#!/usr/bin/env python3
"""
Opti step runner.
Every control-cycle step is written to disk and committed as its own git commit
inside this single repository. Re-runs always append new step commits.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

from axb_robot import AxbRobot, GroundStation


REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
STEPS_DIR = os.path.join(REPO_ROOT, "steps")
LOG_FILE = os.path.join(REPO_ROOT, "run_log.jsonl")


def git(*args: str) -> None:
    subprocess.check_call(
        ["git", "-C", REPO_ROOT, *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def ensure_steps_dir() -> None:
    os.makedirs(STEPS_DIR, exist_ok=True)


def next_step_index() -> int:
    existing = [
        int(f.split("_")[1].split(".")[0])
        for f in os.listdir(STEPS_DIR)
        if f.startswith("step_") and f.endswith(".json")
    ]
    return max(existing, default=0) + 1


def write_and_commit(step_num: int, payload: dict) -> str:
    path = os.path.join(STEPS_DIR, f"step_{step_num:04d}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    # also append to the continuous log
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(payload, default=str) + "\n")

    rel = os.path.relpath(path, REPO_ROOT)
    git("add", rel, "run_log.jsonl")
    msg = (
        f"Opti step {step_num:04d}: "
        f"pose=[{payload['pose'][0]:.4f}, {payload['pose'][1]:.4f}] "
        f"d={payload['last_d']:.3f} surprise={payload['last_surprise']:.3f} "
        f"{payload['status_msg']}"
    )
    git("commit", "-m", msg)
    return msg


def run(max_steps: int = 12) -> None:
    ensure_steps_dir()
    station = GroundStation(goal=np.array([4.0, 0.0]))
    robot = AxbRobot(station, name="Opti", seed=42)

    print(f"Opti online. Goal {station.vars['goal']}. Max steps {max_steps}.")
    print("Every step will be committed to this repo.")

    start_idx = next_step_index()
    for i in range(max_steps):
        st = robot.step()
        step_num = start_idx + i

        payload = {
            "step": step_num,
            "robot_step": st.step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pose": st.pose.tolist(),
            "goal_dist": float(st.goal_dist),
            "last_d": float(st.last_d),
            "last_surprise": float(st.last_surprise),
            "last_heard_range": float(st.last_heard_range),
            "reached": bool(st.reached),
            "status_msg": st.status_msg,
            "pushed_paths_count": len(station.pushed_paths),
            "last_pushed_path": station.pushed_paths[-1] if station.pushed_paths else None,
        }

        msg = write_and_commit(step_num, payload)
        print(f"  committed: {msg}")

        if st.reached:
            print("Demand point reached.")
            break

    # final status file
    status_path = os.path.join(REPO_ROOT, "latest_status.json")
    with open(status_path, "w") as f:
        json.dump(
            {
                "final_pose": robot.pose.tolist(),
                "steps_taken": robot.status.step,
                "reached": robot.status.reached,
                "status_msg": robot.status.status_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            f,
            indent=2,
        )
    git("add", "latest_status.json")
    git("commit", "-m", f"Opti run complete: {robot.status.status_msg} after {robot.status.step} cycles")
    print("Run finished. All steps live in the commit history of this repo.")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    run(max_steps=n)
