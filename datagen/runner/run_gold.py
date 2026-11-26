"""Run the finance gold set through the A2A workflow and harvest labeled traces.

For each gold case, run the orchestrator N times (to surface stochastic natural
failures), verify each output, stitch the per-component trace fragments into one
canonical trace, and write it to data/traces/finance/<task_type>-<run_id>.json.

Usage:
    python -m datagen.runner.run_gold [--samples N] [--case fin-03 ...]

Requires GOOGLE_API_KEY (or GEMINI_API_KEY) for the default Gemini models.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import uuid

import httpx
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from datagen.finance.agents.orchestrator import build_orchestrator
from datagen.finance.agents.serve import SPECIALISTS_SUBAGENT
from datagen.finance.utils.tracing import TraceCollector
from datagen.finance.utils.utils import FRAGMENTS_DIR, TRACES_DIR
from datagen.gold.finance.cases import GoldCase, build_cases
from datagen.gold.finance.verifiers import verify
from datagen.runner.stitch import read_window, stitch
from datagen.runner.trace_schema import validate_event

APP_NAME = "finance"
SETTLE_SECONDS = 0.25


# --- specialist A2A servers ---------------------------------------------------
def start_servers() -> list[subprocess.Popen]:
    procs = []
    for name in SPECIALISTS_SUBAGENT:
        procs.append(subprocess.Popen([sys.executable, "-m", "datagen.finance.agents.serve", name]))
    return procs


def wait_healthy(timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    for name, module in SPECIALISTS_SUBAGENT.items():
        url = f"http://localhost:{module.PORT}{AGENT_CARD_WELL_KNOWN_PATH}"
        while True:
            try:
                if httpx.get(url, timeout=2.0).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if time.time() > deadline:
                raise RuntimeError(f"{name} did not come up at {url}")
            time.sleep(0.5)


def stop_servers(procs: list[subprocess.Popen]) -> None:
    for p in procs:
        p.terminate()
    for p in procs:
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()


# --- single run ---------------------------------------------------------------
async def run_case(runner: Runner, session_service: InMemorySessionService,
                   case: GoldCase, sample: int) -> dict:
    run_id = uuid.uuid4().hex
    session_id = f"{case.case_id}-{sample}-{run_id[:8]}"
    await session_service.create_session(app_name=APP_NAME, user_id="runner", session_id=session_id)

    t0 = time.time()
    message = types.Content(role="user", parts=[types.Part(text=case.prompt)])
    final_output = ""
    try:
        async for event in runner.run_async(user_id="runner", session_id=session_id,
                                             new_message=message):
            if event.is_final_response() and event.content and event.content.parts:
                final_output = (event.content.parts[-1].text or "").strip()
    except Exception as exc:  # keep harvesting; record the failure
        final_output = f"[runner error] {exc}"
    time.sleep(SETTLE_SECONDS)
    t1 = time.time()

    result = verify(case.verifier, final_output)
    events, edges = stitch(read_window(t0, t1 + SETTLE_SECONDS), run_id, case.task_type)

    trace = {
        "run_id": run_id,
        "case_id": case.case_id,
        "task_type": case.task_type,
        "sample_index": sample,
        "prompt": case.prompt,
        "expected": case.verifier["expected"],
        "final_output": final_output,
        "verifier": result,
        "failure_category": result["category"],
        "status": "pass" if result["passed"] else "fail",
        "events": events,
        "edges": edges,
    }
    _write_trace(trace)
    return trace


def _write_trace(trace: dict) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACES_DIR / f"{trace['task_type']}-{trace['run_id'][:8]}.json"
    path.write_text(json.dumps(trace, indent=2, default=str))


def _reset_fragments() -> None:
    FRAGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    for p in FRAGMENTS_DIR.glob("*.jsonl"):
        p.unlink()


# --- orchestration ------------------------------------------------------------
async def _run_all(cases: list[GoldCase], samples: int) -> list[dict]:
    root = build_orchestrator()
    collector = TraceCollector(component="orchestrator")
    collector.attach(root)
    for sub in root.sub_agents:  # capture the orchestrator-side delegation spans
        collector.attach_agent_only(sub)

    session_service = InMemorySessionService()
    runner = Runner(agent=root, app_name=APP_NAME, session_service=session_service)

    traces = []
    for case in cases:
        for sample in range(samples):
            trace = await run_case(runner, session_service, case, sample)
            flag = "PASS" if trace["status"] == "pass" else trace["failure_category"].upper()
            print(f"  {case.case_id} s{sample}: {flag}  -> {trace['final_output'][:60]!r}")
            traces.append(trace)
    return traces


def _summary(traces: list[dict]) -> None:
    from collections import Counter
    counts = Counter(t["failure_category"] for t in traces)
    passed = sum(t["status"] == "pass" for t in traces)
    print(f"\n{passed}/{len(traces)} passed. categories: {dict(counts)}")

    bad = [e for t in traces for e in t["events"] if validate_event(e)]
    if bad:
        print(f"WARNING: {len(bad)} events failed schema validation")
    else:
        print("all emitted events valid against canonical schema")


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--case", action="append", dest="case_ids")
    args = ap.parse_args(argv[1:])

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        print("WARNING: no GOOGLE_API_KEY / GEMINI_API_KEY set; agent calls will fail.")

    cases = build_cases()
    if args.case_ids:
        cases = [c for c in cases if c.case_id in set(args.case_ids)]

    _reset_fragments()
    procs = start_servers()
    try:
        wait_healthy()
        traces = asyncio.run(_run_all(cases, args.samples))
    finally:
        stop_servers(procs)
    _summary(traces)


if __name__ == "__main__":
    main(sys.argv)
