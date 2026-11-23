"""Local asset pointers. Model and report validation remains in the evidence bridge."""
from __future__ import annotations
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parents[2]
POINTER = ROOT / "artifacts/recommender/dashboard_assets.json"
FRAMEWORKS = {"AutoStreamML", "AutoClass", "EvoAutoML", "OAML", "ChaCha"}

def asset_settings():
    if not POINTER.exists():
        return {}
    value = json.loads(POINTER.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Dashboard asset settings must be a JSON object.")
    return value

def asset_path(kind):
    value = asset_settings().get(kind)
    if not value:
        return None
    path = Path(value).expanduser()
    return (ROOT / path).resolve() if not path.is_absolute() else path.resolve()

def activate_assets(bundle, development=None, external=None):
    from . import recommender_bridge as bridge
    bundle = Path(bundle).expanduser().resolve()
    explicit = os.environ.get('AWAREML_RECOMMENDER_BUNDLE') or os.environ.get('AWAREML_RECOMMENDER_V3_BUNDLE')
    if explicit and Path(explicit).expanduser().resolve() != bundle:
        raise ValueError('A model-folder environment setting points elsewhere. Clear that setting before connecting a different folder.')
    status = bridge.bundle_status(bundle)
    if not status["ready"]:
        raise ValueError(status["message"])
    if set(status["manifest"]["frameworks"]) != FRAMEWORKS:
        raise ValueError("Connect the complete five-framework model portfolio.")
    resolved = {"bundle": str(bundle)}
    for kind, directory in [("development", development), ("external", external)]:
        if directory:
            path = Path(directory).expanduser().resolve()
            explicit_report = os.environ.get('AWAREML_V3_' + kind.upper() + '_EVALUATION')
            if explicit_report and Path(explicit_report).expanduser().resolve() != path:
                raise ValueError('An evaluation-folder environment setting points elsewhere. Clear that setting before connecting this report.')
            evidence = bridge.evaluation_evidence(kind, bundle, evaluation_directory=path)
            if evidence is None:
                raise ValueError("No evaluation report found in " + str(path))
            resolved[kind] = str(path)
    POINTER.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=str(POINTER.parent), delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(resolved, handle, indent=2)
        handle.write("\n")
    try:
        os.replace(str(temporary), str(POINTER))
    finally:
        if temporary.exists():
            temporary.unlink()
    return status

