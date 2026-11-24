"""Validate source-time alignment and reproduce FGS grouping without unequal-array errors."""
import csv, collections, sys, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'fgs_patched'))
from tube import Tube
from synopsis import group_tubes

def select(video, max_tracks=12, max_frame=1200):
    path=ROOT/'annotations'/f'Vid{video}_boxes.csv'
    by=collections.defaultdict(list)
    with path.open() as f:
        for r in csv.DictReader(f):
            fr=int(r['frame'])
            if fr<=max_frame:
                x,y,w,h=(float(r[k]) for k in ('x','y','width','height'))
                by[r['object_id']].append((fr,[x,y,x+w,y+h]))
    candidates=[(oid,obs[:100]) for oid,obs in by.items() if len(obs)>=35]
    candidates.sort(key=lambda v:v[1][0][0])
    if len(candidates)>max_tracks:
        candidates=[candidates[i] for i in np.linspace(0,len(candidates)-1,max_tracks,dtype=int)]
    tubes=[]
    for oid,obs in candidates:
        t=Tube(obs[0][0],oid);t.frame_number=[v[0] for v in obs];t.boxes=np.asarray([v[1] for v in obs],float);t.last_frame=obs[-1][0];tubes.append(t)
    return tubes

def run():
    rows=[]
    for v in range(1,7):
        tubes=select(v)
        groups=group_tubes(tubes,25,1,.5,1)
        byid={t.id:t for t in tubes}
        spans=[max(byid[i].last_frame for i in g)-min(byid[i].first_frame for i in g)+1 for g in groups]
        rows.append(dict(video=f'Vid{v}',tracks=len(tubes),groups=len(groups),group_sizes=';'.join(str(len(g)) for g in groups),multi_object_groups=sum(len(g)>1 for g in groups),longest_group_span=max(spans,default=0),source_span=max((t.last_frame for t in tubes),default=0)-min((t.first_frame for t in tubes),default=0)+1,nondegenerate=(len(groups)>1 and any(len(g)>1 for g in groups))))
    with (ROOT/'alignment_feasibility.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    print(json.dumps(rows,indent=2))
if __name__=='__main__':run()
