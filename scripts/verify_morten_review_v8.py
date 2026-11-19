from pathlib import Path
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from awareml.studies.trust_morten_v2 import StimulusBankV2
from awareml.studies.morten_review_v3 import validate_claims, review_status, scenario_coverage
import pandas as pd


def main():
    errors=validate_claims()
    bank=StimulusBankV2()
    for rel in ['data/journal/trust_calibration_phase16_v3/frozen_design/manifest.json','data/journal/information_seeking_v3/frozen/design_manifest.json']:
        path=ROOT/rel;m=json.loads(path.read_text())
        for name,meta in m['files'].items():
            if hashlib.sha256((path.parent/name).read_bytes()).hexdigest()!=meta['sha256']:errors.append(rel+': '+name+' hash mismatch')
    coverage=scenario_coverage(pd.DataFrame())
    result={'software_checks':'pass' if not errors else 'fail','errors':errors,'matched_families':len(bank.pairs),'scenario_bank_size':len(coverage),
            'human_exact_stimulus_review':review_status(),'next_step':'Review revised exact stimuli using assessor_review_app.py and import genuine assessor CSVs before final collection. Pilot inspection can run now.'}
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 1 if errors else 0


if __name__=='__main__':raise SystemExit(main())
