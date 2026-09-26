# opti-steps

**Opti** — branded Axb*1c/d predictive-echo robot.

Every control-cycle step Opti takes is written to `steps/step_NNNN.json` and committed as its own discrete commit in this single repository.

Re-running always appends new step commits. The commit history *is* the run log.

## Cycle

```
predict echo → decide → PUSH path → do → hear real echo → correct → repeat
```

Invariants preserved:

1. No world mapping.
2. Risk divisor `d` comes only from the predicted echo.
3. Path is pushed to the ground station before the robot moves.
4. Solve form: `x = pinv(A) @ b * (1.0 / c) / d`

## Run

```bash
python run_opti_steps.py          # default 12 steps
python run_opti_steps.py 8        # custom step count
```

Each step produces one commit. The continuous log is also appended to `run_log.jsonl`.

## Layout

- `axb_robot.py` / `axb_predictive_echo.py` — control loop
- `run_opti_steps.py` — step runner that commits
- `steps/` — one JSON file per step
- `run_log.jsonl` — append-only log
- `latest_status.json` — last run summary

Repo: https://github.com/fitzyracing1/opti-steps
