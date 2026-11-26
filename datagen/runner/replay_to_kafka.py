"""Deferred: replay harvested trace events onto a Kafka/Redpanda topic.

Not wired in this data-generation phase. When the real AgentTrace ingestion path
exists, this will read each trace JSON in data/traces/finance/ and produce its
``events`` (already in the canonical schema) to the configured topic, keyed by
run_id so events stay ordered per run.
"""
from __future__ import annotations

import json

from datagen.finance.utils.utils import TRACES_DIR


def iter_canonical_events():
    """Yield canonical trace events from all harvested traces (producer-ready)."""
    for path in sorted(TRACES_DIR.glob("*.json")):
        trace = json.loads(path.read_text())
        for event in trace["events"]:
            yield event


def main() -> None:
    raise SystemExit(
        "replay_to_kafka is a deferred stub; no Kafka in the data-gen phase. "
        "Use iter_canonical_events() once the ingestion topic exists."
    )


if __name__ == "__main__":
    main()
