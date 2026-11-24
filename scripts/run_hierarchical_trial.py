import sys,csv,ast,time,collections,statistics,random,zipfile
from pathlib import Path
R=Path('/mnt/data');sys.path[:0]=[str(R/'pceo_collision_refinement'),str(R/'pceo_fgs_alignment_fix')]
import refine
from validate_alignment import Tube
import numpy as np
s=(R/'pceo_heldout_trial/run.py').read_text();ns={'collections':collections,'R':R,'Tube':Tube,'np':np,'csv':csv};exec(s[s.index('def heldout('):s.index('\nrefine.select=heldout')],ns);refine.select=ns['heldout']
s=(R/'pceo_cached_refinement/run.py').read_text();ns2={'collections':collections};exec(s[s.index('def boxes_overlap('):s.index('\nrows=[]')],ns2);CachedCost=ns2['CachedCost']
def pair_delta(eng,st,a,sa,b,sb):
 return eng.delta(st,a,sa)+eng.delta(st,b,sb)+eng.pair(a,sa,b,sb)-eng.pair(a,sa,b,st[b])-eng.pair(a,st[a],b,sb)+eng.pair(a,st[a],b,st[b])
def hierarchical(groups,L,initial,limit_pairs=8,max_passes=2):
 eng=CachedCost(groups);st=dict(initial);base=eng.total(st);ids=sorted(st)
 t=time.perf_counter();accepted=0;evals=0
 for it in range(max_passes):
  # Focus on pairs currently causing most false overlap
  ranking=sorted(((eng.pair(a,st[a],b,st[b]),a,b) for i,a in enumerate(ids) for b in ids[i+1:]),reverse=True)
  chosen=[(a,b) for _,a,b in ranking[:limit_pairs]]
  best=(base,None)
  for a,b in chosen:
   ga,gb=eng.groups[a],eng.groups[b]
   def options(gid,g):
    cur=st[gid];return sorted({x for x in [1,L-g.length+1,*[cur+d for d in (-64,-32,-16,-8,-4,-2,-1,1,2,4,8,16,32,64)]] if 1<=x<=L-g.length+1 and x!=cur})
   for sa in options(a,ga):
    for sb in options(b,gb):
     candidate=dict(st);candidate[a]=sa;candidate[b]=sb
     if refine.actual_span(groups,candidate)!=L:continue
     evals+=1;value=base+pair_delta(eng,st,a,sa,b,sb)
     if value<best[0]-1e-8:best=(value,(a,sa,b,sb))
  if best[1] is None:break
  a,sa,b,sb=best[1];st[a]=sa;st[b]=sb;base=best[0];accepted+=1
 assert refine.actual_span(groups,st)==L
 assert abs(refine.cost(groups,st)-base)<1e-6
 return st,base,accepted,evals,time.perf_counter()-t
rows=[]
for vid in range(1,7):
 groups,L=refine.build(vid)
 source=[]
 for file in (R/'pceo_multistart_validation/results.csv',R/'pceo_extended_robustness/results.csv'):
  source.extend([r for r in csv.DictReader(file.open()) if r['video']==f'Vid{vid}'])
 # Two prespecified seeds for all videos plus problematic seed 107 for Vid2
 selected=[r for r in source if int(r['seed']) in ((7,17,107) if vid==2 else (7,17))]
 for r in selected:
  initial=ast.literal_eval(r['placement']);before=refine.cost(groups,initial)
  result,after,moves,checks,seconds=hierarchical(groups,L,initial)
  rows.append(dict(video=f'Vid{vid}',seed=r['seed'],groups=len(groups),length=L,fgs_overlap=float(r['fgs_overlap']),single_group_overlap=before,hierarchical_overlap=after,improvement=before-after,accepted_pair_moves=moves,feasible_pair_candidates=checks,pair_seconds=round(seconds,5),exact_length=True,placement=repr(result)))
  print(vid,r['seed'],before,after,moves,round(seconds,3),flush=True)
out=R/'pceo_hierarchical_trial';out.mkdir(exist_ok=True)
with (out/'results.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print('SUMMARY',len(rows),sum(r['improvement']>0 for r in rows),sum(r['hierarchical_overlap']<r['fgs_overlap'] for r in rows))
