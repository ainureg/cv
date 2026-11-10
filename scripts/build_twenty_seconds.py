"""One-off Twenty Seconds export; keep this helper on archive/twenty-seconds."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
from resume import ROOT, build_resume


def main():
    parser = argparse.ArgumentParser(description='Build the archived Twenty Seconds layout using current JSON data.')
    parser.add_argument('--content', type=Path, default=ROOT / 'content.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/twenty-seconds/ainur-karimov-cv.pdf')
    args = parser.parse_args()
    data = copy.deepcopy(json.loads(args.content.read_text()))
    # Accept both the archived inline companies and the current central company directory.
    for job in data['experience']:
        if 'companyId' in job:
            company = data['companies'][job['companyId']]
            job['company'] = company['name']
            job['url'] = company['url']
    destination = args.output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cv-twenty-seconds-') as directory:
        root = Path(directory)
        pdf = build_resume(data, root=root)
        shutil.copyfile(pdf, destination)
        shutil.copytree(root / 'generated', destination.parent / (destination.stem + '-source'), dirs_exist_ok=True)
    print(f'Twenty Seconds PDF: {destination}')
    print('Source bundle saved next to the PDF; current website was not changed.')


if __name__ == '__main__':
    main()
