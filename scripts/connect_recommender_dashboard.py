"""Connect downloaded, trusted experiment assets without retraining."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, help='Folder containing manifest.json and the trained models')
    parser.add_argument('--development', help='Optional development evaluation folder')
    parser.add_argument('--external', help='Optional external evaluation folder')
    args = parser.parse_args()
    from awareml.ui_v2.recommender_assets import activate_assets
    try:
        status = activate_assets(args.bundle, args.development, args.external)
    except Exception as exc:
        parser.exit(1, str(exc) + '\n')
    print('Connected: {} datasets, {} frameworks, {} development runs.'.format(
        status['development_datasets'], status['framework_count'], status['underlying_runs']))
    print('Restart the dashboard to use this connection.')

if __name__ == '__main__':
    main()
