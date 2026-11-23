"""Install the exported Rocket model package and matching evaluation reports."""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root):
    models=root/'models'
    payload=json.loads((models/'manifest.json').read_text(encoding='utf-8'))
    meta=payload['frozen']
    digest=hashlib.sha256(json.dumps(meta,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    if digest!=payload['bundle_sha256']:raise ValueError('Model manifest integrity failure.')
    if meta['feature_set']!='prefix' or set(meta['frameworks'])!={'AutoStreamML','AutoClass','EvoAutoML','OAML','ChaCha'}:
        raise ValueError('A complete five-framework prefix model package is required.')
    if set(meta['models'])!={'accuracy','runtime','energy','co2'}:raise ValueError('Four objective models are required.')
    files=meta['file_hashes']
    required={'development_aggregates.csv','training_collection.json'} | {v['file'] for v in meta['models'].values()}
    if not required.issubset(files):raise ValueError('Model package is incomplete.')
    def check(directory,hashes):
        for relative,expected in hashes.items():
            path=(directory/relative).resolve()
            if directory.resolve() not in path.parents or sha(path)!=expected:
                raise ValueError('Missing, changed or unsafe file: '+relative)
    check(models,files)
    for kind,role in [('development','nested_LODO_development_four_predeclared_profiles'),
                      ('external','revised_external_evaluation_of_previously_evaluated_cohort')]:
        directory=root/kind
        if not directory.exists():continue
        report=json.loads((directory/'evaluation.json').read_text(encoding='utf-8'))
        if report['bundle_manifest_sha256']!=sha(models/'manifest.json') or report['portfolio']!=meta['portfolio'] or report['role']!=role:
            raise ValueError('Evaluation does not match this model: '+kind)
        check(directory,report['file_hashes'])
    return meta


def install(archive,project):
    project=project.resolve()
    if not (project/'awareml/ui_v2').is_dir():raise ValueError('Run this from the AwareML_Extension project directory.')
    artifacts=project/'artifacts';artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(artifacts)) as temporary:
        staging=Path(temporary)/'package';staging.mkdir()
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                relative=Path(member.filename)
                target=(staging/relative).resolve()
                if relative.is_absolute() or staging.resolve() not in target.parents or relative.parts[0] not in ('models','development','external'):
                    raise ValueError('Unsafe or unexpected archive path: '+member.filename)
                if member.file_size>512*1024*1024:raise ValueError('Unexpectedly large file in package.')
            package.extractall(staging)
        meta=validate(staging)
        destination=artifacts/'dashboard_evidence'
        pointer=artifacts/'recommender/dashboard_assets.json'
        backup=artifacts/'copilot_asset_backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup.mkdir(parents=True)
        if pointer.exists():shutil.copy2(pointer,backup/'dashboard_assets.json')
        if destination.exists():os.replace(str(destination),str(backup/'dashboard_evidence'))
        settings={'bundle':str(destination/'models')}
        for kind in ('development','external'):
            if (staging/kind).exists():settings[kind]=str(destination/kind)
        try:
            os.replace(str(staging),str(destination))
            pointer.parent.mkdir(parents=True,exist_ok=True)
            tmp=pointer.with_suffix('.importing')
            tmp.write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
            os.replace(str(tmp),str(pointer))
        except Exception:
            if destination.exists():shutil.rmtree(destination)
            if (backup/'dashboard_evidence').exists():os.replace(str(backup/'dashboard_evidence'),str(destination))
            if (backup/'dashboard_assets.json').exists():shutil.copy2(backup/'dashboard_assets.json',pointer)
            raise
    print('Installed trained models:',destination/'models')
    print('Training datasets:',len(meta['training_dataset_ids']),'Frameworks:',len(meta['frameworks']))
    print('Required scikit-learn version:',meta['environment']['packages']['scikit-learn'])
    print('Previous assets backup:',backup)
    print('Restart Streamlit to use the models.')
    for name in ('AWAREML_RECOMMENDER_BUNDLE','AWAREML_RECOMMENDER_V3_BUNDLE'):
        if os.environ.get(name) and Path(os.environ[name]).resolve()!=destination/'models':
            print('Update or clear the old environment override:',name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--project',type=Path,default=Path.cwd())
    args=parser.parse_args()
    try:install(args.archive.expanduser(),args.project.expanduser())
    except Exception as exc:parser.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
