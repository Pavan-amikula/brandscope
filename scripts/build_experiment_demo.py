"""Create a labelled synthetic experiment fixture, not a business result."""
import csv
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
rng=random.Random(42)
rows=[]
for arm,p in [('control',.08),('treatment',.10)]:
    for i in range(4000):
        converted=int(rng.random()<p)
        contribution=converted*45*(.45-(.05 if arm=='treatment' else 0))-(.10 if arm=='treatment' else 0)
        rows.append(dict(participant_id=f'synthetic-{arm}-{i:04}',arm=arm,converted=converted,contribution=round(contribution,4)))
rng.shuffle(rows)
with (ROOT/'web/models/synthetic-experiment.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print('Created 8000 explicitly synthetic participant outcomes.')
