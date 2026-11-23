"""Export a validated, read-only dashboard snapshot from a V3 result export."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from awareml.development_benchmark import METRICS, digest, validate_snapshot


def export(source, output):
    source, output = Path(source), Path(output)
    data = json.loads(source.read_text(encoding="utf-8"))
    campaign = data["campaign_manifest"]
    rows = []
    for item in data["records"]:
        r, t = item["result"], item["manifest_task"]
        if r["campaign_sha256"] != campaign["campaign_sha256"]:
            raise ValueError("Result campaign hash differs from manifest.")
        for field in ("task_id", "dataset_id", "framework", "seed", "cohort", "expected_samples"):
            if str(r["task"][field]) != str(t[field]):
                raise ValueError("Result task differs from its manifest: " + field)
        rows.append({**r["task"], **{k: r[k] for k in METRICS},
                     "samples_processed": r["samples_processed"], "status": r["status"], "eligible": r["eligible"],
                     "cpu_power_mode": r["measurement_provenance"].get("cpu_power_mode", "unknown"),
                     "node": r["environment"]["node"], "cpu_model": r["environment"]["cpu_model"]})
    frozen = {"schema": "awareml_development_benchmark_v1", "cohort": "dev",
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "campaign_sha256": campaign["campaign_sha256"], "exported_utc": data["exported_utc"],
              "protocol": campaign["frozen"]["protocol"],
              "dataset_ids": sorted({r["dataset_id"] for r in rows}),
              "frameworks": campaign["frozen"]["protocol"]["frameworks"], "runs": rows}
    payload = {"frozen": frozen, "sha256": digest(frozen)}
    validate_snapshot(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default=str(ROOT / "artifacts/recommender_v3/development_benchmark.json"))
    args = parser.parse_args()
    print("Completed development runs exported:", export(args.source, args.output))
