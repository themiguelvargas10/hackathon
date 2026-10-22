"""Exporta evidencia reproducible sin abrir navegador."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aquaguard.core import Project, DATA, ROOT
from aquaguard.cyber import correlate

parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,default=ROOT/'results'/'local_report.json')
args=parser.parse_args()
p=Project()
result={'created_utc':datetime.now(timezone.utc).isoformat(),
        'dataset_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),
        'dashboard':p.dashboard(),'benchmark':p.benchmark()}
result['dashboard']['cyber']=correlate(result['dashboard']['alerts'])
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
print(f'Informe guardado: {args.out}')
