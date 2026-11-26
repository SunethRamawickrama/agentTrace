# Data generation — finance A2A system

Generates labeled failing/degraded traces for AgentTrace by running a real
multi-agent A2A finance workflow against a deterministic gold set.

## Layout
- `finance/` — the A2A system: `orchestrator.py` (root) delegates over A2A to the
  specialists in `specialists/`, each served by `serve.py`. `common/` holds the
  model factory, dataset tools, and the callback-based `TraceCollector`.
- `gold/finance/` — the gold set (`cases.py`), deterministic graded `verifiers.py`,
  and `ground_truth.py` (expected answers computed from the datasets).
- `runner/` — `run_gold.py` runs the set and writes traces; `report.py` summarizes;
  `stitch.py`/`trace_schema.py` build and validate the canonical traces.
- Datasets live in `data/finance/datasets/`; output traces in `data/traces/finance/`.

## Run
```bash
cp .env.example .env        # add GOOGLE_API_KEY (Gemini free tier)
uv run python -m datagen.runner.run_gold --samples 3   # all 12 cases x 3
uv run python -m datagen.runner.run_gold --case fin-03 --samples 5  # one case
uv run python -m datagen.runner.report                 # summary of harvested traces
```

Each run writes `data/traces/finance/<task_type>-<run_id>.json`: the prompt,
expected answer, final output, graded verifier result, a `failure_category`
(`pass` / `fail_accuracy` / `fail_format` / `fail_other`), and the canonical
`events` + `edges` of the multi-agent DAG.

The runner executes runs **sequentially** — that is what lets fragments from the
separate specialist server processes be correlated by time window (see
`runner/stitch.py`). Don't parallelize runs without changing that correlation.

## If natural failures are too few
`report.py` flags when fewer than ~20 failures were harvested. Fault injection
(weaker model via `AGENTTRACE_MODEL`, corrupted tool data, or format-stripped
specialist prompts) is the planned backstop to guarantee category coverage.
