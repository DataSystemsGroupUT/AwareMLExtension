"""Export a completed five-framework model and matching reports for the dashboard."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path.cwd().resolve()
FRAMEWORKS = {'AutoStreamML','AutoClass','EvoAutoML','OAML','ChaCha'}

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def verified_files(directory, hashes):
    result=[]
    for relative, expected in hashes.items():
        path=(directory/relative).resolve()
        if directory not in path.parents or sha(path)!=expected:
            raise ValueError('Missing, changed or unsafe artifact: '+str(path))
        result.append((path,relative))
    return result

def export(bundle, output):
    bundle=bundle.resolve()
    payload=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
    meta=payload['frozen']
    actual=hashlib.sha256(json.dumps(meta,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()
    if actual!=payload['bundle_sha256'] or meta['feature_set']!='prefix' or set(meta['frameworks'])!=FRAMEWORKS:
        raise ValueError('Select a valid prefix-only model for all five frameworks.')
    files=[(bundle/'manifest.json','models/manifest.json')]
    files.extend((p,'models/'+name) for p,name in verified_files(bundle,meta['file_hashes']))
    expected={'development':'nested_LODO_development_four_predeclared_profiles',
              'external':'revised_external_evaluation_of_previously_evaluated_cohort'}
    reports={}
    for kind, role in expected.items():
        matches=[]
        for path in (ROOT/'artifacts').rglob('evaluation.json'):
            try:
                record=json.loads(path.read_text(encoding='utf-8'))
                if record.get('bundle_manifest_sha256')==sha(bundle/'manifest.json') and record.get('portfolio')==meta['portfolio'] and record.get('role')==role:
                    matches.append((path,record))
            except (OSError, ValueError, KeyError, TypeError):continue
        if matches:
            path, record=max(matches,key=lambda item:item[0].stat().st_mtime)
            directory=path.parent.resolve()
            files.append((path,kind+'/evaluation.json'))
            files.extend((p,kind+'/'+name) for p,name in verified_files(directory,record['file_hashes']))
            reports[kind]=str(directory)
    output=output.resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as archive:
        for path,name in files:archive.write(path,name)
    print('Model:',bundle)
    print('Datasets:',len(meta['training_dataset_ids']),'Frameworks:',len(meta['frameworks']))
    print('Reports:',', '.join(reports) or 'No matching reports found')
    print('Saved:',output)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,help='Specific trained model folder; otherwise locate the newest complete five-framework prefix model')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/AwareML_Dashboard_Evidence.zip')
    args=parser.parse_args()
    bundle=args.bundle
    if bundle is None:
        candidates=[]
        for path in (ROOT/'artifacts').rglob('manifest.json'):
            try:
                item=json.loads(path.read_text(encoding='utf-8'))['frozen']
                if 'copilot_ui_backups' in path.parts or 'copilot_asset_backups' in path.parts:continue
                if item.get('feature_set')=='prefix' and set(item.get('frameworks',[]))==FRAMEWORKS:
                    verified_files(path.parent.resolve(),item['file_hashes'])
                    candidates.append(path.parent)
            except (KeyError,TypeError,ValueError,OSError):continue
        if not candidates:parser.error('No completed five-framework prefix model found. Specify --bundle.')
        bundle=max(candidates,key=lambda p:(p/'manifest.json').stat().st_mtime)
    try:export(bundle,args.output)
    except Exception as exc:parser.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
