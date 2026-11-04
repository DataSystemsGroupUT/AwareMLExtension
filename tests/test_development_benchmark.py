import copy
import json
import tempfile
import unittest
from pathlib import Path
from awareml.development_benchmark import FRAMEWORKS, digest, load_evidence, mean_sd_rows, validate_snapshot


def example():
    rows = []
    for f in FRAMEWORKS:
        for s in range(42, 47):
            rows.append(dict(task_id=len(rows), dataset_id="test", framework=f, seed=s, cohort="dev",
                expected_samples=100, samples_processed=100, status="completed", eligible=True,
                accuracy=(s-40)/10, f1_macro=.5, runtime_sec=float(s-40),
                peak_process_tree_rss_mib=100., energy_kwh=.001, co2_kg=.0004,
                cpu_power_mode="unknown"))
    return {"schema":"awareml_development_benchmark_v1", "cohort":"dev", "dataset_ids":["test"],
            "frameworks":list(FRAMEWORKS), "protocol":{"seeds":list(range(42,47)),
            "scientific_time_limit_sec":None, "profile_size":1000}, "runs":rows}


def signed(frozen):
    return {"frozen":frozen,"sha256":digest(frozen)}


class DevelopmentEvidenceTests(unittest.TestCase):
    def test_complete_five_seed_evidence(self):
        self.assertEqual(len(validate_snapshot(signed(example()))["runs"]),25)

    def test_sample_sd_not_population_sd(self):
        row = mean_sd_rows(example())[0]
        self.assertAlmostEqual(row["runtime_sec_mean"],4)
        self.assertAlmostEqual(row["runtime_sec_sd"],(2.5)**.5)

    def test_missing_seed_rejected_even_with_recomputed_checksum(self):
        f=example();f["runs"].pop()
        with self.assertRaises(ValueError):validate_snapshot(signed(f))

    def test_duplicate_seed_rejected(self):
        f=example();f["runs"][1]["seed"]=42
        with self.assertRaises(ValueError):validate_snapshot(signed(f))

    def test_external_evidence_rejected(self):
        f=example();f["runs"][0]["cohort"]="eval"
        with self.assertRaises(ValueError):validate_snapshot(signed(f))

    def test_partial_stream_rejected(self):
        f=example();f["runs"][0]["samples_processed"]=99
        with self.assertRaises(ValueError):validate_snapshot(signed(f))

    def test_different_stream_length_rejected(self):
        f=example();f["runs"][0].update(samples_processed=90,expected_samples=90)
        with self.assertRaises(ValueError):validate_snapshot(signed(f))

    def test_out_of_range_metric_rejected(self):
        f=example();f["runs"][0]["accuracy"]=1.5
        with self.assertRaises(ValueError):validate_snapshot(signed(f))

    def test_ineligible_result_rejected(self):
        f=example();f["runs"][0]["eligible"]=False
        with self.assertRaises(ValueError):validate_snapshot(signed(f))

    def test_corrupt_snapshot_never_becomes_ready(self):
        p=signed(example());p["frozen"]["runs"][0]["runtime_sec"]=20
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"evidence.json";path.write_text(json.dumps(p),encoding="utf-8")
            status=load_evidence(path)
            self.assertFalse(status["ready"]);self.assertEqual(status["state"],"invalid")

    def test_missing_evidence_not_fabricated(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_evidence(Path(d)/"absent.json")["state"],"absent")

    def test_loading_snapshot_has_no_model_readiness_flag(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"evidence.json";path.write_text(json.dumps(signed(example())),encoding="utf-8")
            status=load_evidence(path)
            self.assertEqual((status["runs"],status["groups"]),(25,5))
            self.assertNotIn("models",status)
