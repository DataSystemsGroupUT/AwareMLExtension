"""Read-only benchmark evidence; never a substitute for a trained recommender."""
from __future__ import annotations
import hashlib
import itertools
import json
import math
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("accuracy", "f1_macro", "runtime_sec", "peak_process_tree_rss_mib", "energy_kwh", "co2_kg")
FRAMEWORKS = ("AutoStreamML", "AutoClass", "EvoAutoML", "OAML", "ChaCha")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def evidence_path():
    return Path(os.environ.get("AWAREML_V3_DEVELOPMENT_RESULTS") or ROOT / "artifacts/recommender_v3/development_benchmark.json").expanduser().resolve()


def validate_snapshot(payload):
    frozen = payload["frozen"]
    if payload["sha256"] != digest(frozen):
        raise ValueError("Development benchmark checksum mismatch.")
    if frozen["schema"] != "awareml_development_benchmark_v1" or frozen["cohort"] != "dev":
        raise ValueError("Expected development-only benchmark evidence.")
    protocol = frozen["protocol"]
    seeds = protocol["seeds"]
    if len(seeds) < 5 or len(set(seeds)) != len(seeds):
        raise ValueError("Expected at least five distinct seeds.")
    if protocol["scientific_time_limit_sec"] is not None or protocol["profile_size"] != 1000:
        raise ValueError("Development evidence uses an incompatible stream protocol.")
    ids, frameworks, rows = frozen["dataset_ids"], frozen["frameworks"], frozen["runs"]
    if not ids or len(ids) != len(set(ids)) or set(frameworks) != set(FRAMEWORKS) or len(frameworks) != 5:
        raise ValueError("Invalid dataset or five-framework inventory.")
    expected = set(itertools.product(ids, frameworks, seeds))
    seen, task_ids, samples = set(), set(), {}
    for r in rows:
        key = (r["dataset_id"], r["framework"], r["seed"])
        if key in seen or r["task_id"] in task_ids:
            raise ValueError("Duplicate development task or seed.")
        seen.add(key); task_ids.add(r["task_id"])
        if r["cohort"] != "dev" or r["status"] != "completed" or r["eligible"] is not True:
            raise ValueError("Incomplete or non-development result.")
        if r["samples_processed"] != r["expected_samples"] or r["samples_processed"] <= 0:
            raise ValueError("Incomplete sample coverage.")
        previous = samples.setdefault(r["dataset_id"], r["samples_processed"])
        if previous != r["samples_processed"]:
            raise ValueError("Frameworks evaluated different stream lengths.")
        for metric in METRICS:
            v = r[metric]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError("Invalid benchmark metric: " + metric)
            if v < 0 or (metric in ("accuracy", "f1_macro") and v > 1):
                raise ValueError("Out-of-range benchmark metric: " + metric)
        if any(r[m] <= 0 for m in METRICS[2:]):
            raise ValueError("Resource metrics must be positive.")
    if seen != expected or len(rows) != len(expected):
        raise ValueError("Development framework/seed coverage is incomplete.")
    return frozen


def load_evidence(path=None):
    path = Path(path) if path is not None else evidence_path()
    if not path.exists():
        return {"ready": False, "state": "absent"}
    try:
        frozen = validate_snapshot(json.loads(path.read_text(encoding="utf-8")))
        return {"ready": True, "state": "available", "data": frozen,
                "datasets": len(frozen["dataset_ids"]), "runs": len(frozen["runs"]),
                "groups": len(frozen["dataset_ids"]) * len(frozen["frameworks"]),
                "seeds": frozen["protocol"]["seeds"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"ready": False, "state": "invalid", "message": str(exc)}


def mean_sd_rows(frozen):
    groups = {}
    for r in frozen["runs"]:
        groups.setdefault((r["dataset_id"], r["framework"]), []).append(r)
    result = []
    for (dataset, framework), rows in sorted(groups.items()):
        row = {"dataset_id": dataset, "framework": framework, "seed_count": len(rows),
               "samples_processed": rows[0]["samples_processed"]}
        for metric in METRICS:
            values = [r[metric] for r in rows]
            row[metric + "_mean"] = statistics.mean(values)
            row[metric + "_sd"] = statistics.stdev(values)
        result.append(row)
    return result


def render_benchmark(evidence, key):
    import pandas as pd
    import streamlit as st
    if not evidence["ready"]:
        if evidence["state"] == "invalid":
            st.warning("Development results could not be loaded: " + evidence["message"])
        return
    data = evidence["data"]
    with st.expander("Completed development benchmark results", expanded=False):
        st.caption("Observed framework outcomes on development streams. These are not dataset-specific model predictions or recommender validation scores.")
        st.write("{} datasets · {:,} completed runs · {} seeds · {} dataset–framework summaries.".format(
            evidence["datasets"], evidence["runs"], len(evidence["seeds"]), evidence["groups"]))
        st.caption("Seeds: {}. Stream cap: {:,} or end of stream. No scientific time cutoff. Safety watchdog: {:g} hours.".format(
            ", ".join(map(str, evidence["seeds"])), data["protocol"]["max_samples"], data["protocol"]["safety_timeout_sec"] / 3600))
        dataset = st.selectbox("Development dataset", data["dataset_ids"], key=key + "_dataset")
        rows = mean_sd_rows(data)
        shown = []
        for r in rows:
            if r["dataset_id"] != dataset:
                continue
            row = {"Framework": "ChaCha-OVR (supplementary)" if r["framework"] == "ChaCha" else r["framework"]}
            for metric, title, factor in (("accuracy", "Accuracy %", 100), ("f1_macro", "Macro-F1", 1),
                ("runtime_sec", "Runtime s", 1), ("peak_process_tree_rss_mib", "Peak RSS MiB", 1),
                ("energy_kwh", "Energy Wh", 1000), ("co2_kg", "CO₂ g", 1000)):
                row[title] = "{:.4f} ± {:.4f}".format(r[metric + "_mean"] * factor, r[metric + "_sd"] * factor)
            shown.append(row)
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
        st.caption("Mean ± sample SD across the declared seeds (ddof=1). Accuracy SD is in percentage points. ChaCha-OVR is supplementary to the primary four-framework portfolio.")
        st.download_button("Download all development mean and SD results", pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
            file_name="AwareML_V3_Development_Mean_SD.csv", mime="text/csv", key=key + "_download")
        st.caption("Downloaded numeric CSV uses accuracy/F1 fractions, seconds, MiB, kWh and kg CO₂. This evidence does not enable a model bundle or claim held-out performance.")
