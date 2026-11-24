import sys,csv,ast,time,collections,random,statistics,zipfile
from pathlib import Path
R=Path('/mnt/data');sys.path.insert(0,str(R/'pceo_collision_refinement'))
from refine import build,cost,actual_span,refine

def boxes_overlap(a,b):
 return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))

class CachedCost:
 def __init__(self,groups):
  self.groups={g.id:g for g in groups};self.obs={};self.self_cost={}
  for g in groups:
   anchor=min(int(t.frames[0]) for t in g.tubes)
   records=collections.defaultdict(list)
   for t in g.tubes:
    for f,b in zip(t.frames,t.boxes):records[int(f)-anchor].append((int(f),tuple(map(float,b))))
   self.obs[g.id]=records
   v=0.
   for rec in records.values():
    for i in range(len(rec)):
     for j in range(i+1,len(rec)):
      if rec[i][0]!=rec[j][0]:v+=boxes_overlap(rec[i][1],rec[j][1])
   self.self_cost[g.id]=v
  self.pair_cache={}
 def pair(self,ga,sa,gb,sb):
  if ga>gb:ga,gb,sa,sb=gb,ga,sb,sa
  key=(ga,gb,sb-sa)
  if key not in self.pair_cache:
   a,b=self.obs[ga],self.obs[gb];d=sb-sa;v=0.
   for fa,oa in a.items():
    for fb,ob in [(fa-d,b.get(fa-d,()))]:
     for f1,b1 in oa:
      for f2,b2 in ob:
       if f1!=f2:v+=boxes_overlap(b1,b2)
   self.pair_cache[key]=v
  return self.pair_cache[key]
 def total(self,starts):
  ids=sorted(starts);return sum(self.self_cost.values())+sum(self.pair(a,starts[a],b,starts[b]) for i,a in enumerate(ids) for b in ids[i+1:])
 def delta(self,starts,gid,newstart):
  return sum(self.pair(gid,newstart,other,starts[other])-self.pair(gid,starts[gid],other,starts[other]) for other in starts if other!=gid)

def fast_refine(groups,initial,budget,exact=True,max_passes=5):
 engine=CachedCost(groups);starts=dict(initial);base=engine.total(starts);moves=0
 for _ in range(max_passes):
  improved=False
  for g in sorted(groups,key=lambda x:x.id):
   cur=starts[g.id];best=base;best_start=cur
   candidates={1,budget-g.length+1}|{cur+d for d in (-32,-16,-8,-4,-2,-1,1,2,4,8,16,32)}
   for st in sorted(candidates):
    if st<1 or st+g.length-1>budget or st==cur:continue
    starts[g.id]=st
    feasible=not exact or actual_span(groups,starts)==budget
    starts[g.id]=cur
    if not feasible:continue
    v=base+engine.delta(starts,g.id,st)
    if v<best-1e-8:best=v;best_start=st
   starts[g.id]=best_start
   if best_start!=cur:base=best;moves+=1;improved=True
  if not improved:break
 return starts,base,moves,len(engine.pair_cache)

rows=[]
for vid in range(1,7):
 groups,L=build(vid)
 with (R/'pceo_exact_refinement/results.csv').open() as f: cases=[r for r in csv.DictReader(f) if r['video']==f'Vid{vid}']
 for r in cases:
  # Saved final placements are valid exact-length starting points. This measures further refinement, not original full-pipeline speed.
  start=ast.literal_eval(r['placement']);engine=CachedCost(groups)
  for z in range(20):
   rng=random.Random(vid*1000+z);positions={g.id:rng.randint(1,L-g.length+1) for g in groups}
   assert abs(engine.total(positions)-cost(groups,positions))<1e-6
   g=rng.choice(groups);new=rng.randint(1,L-g.length+1)
   newp=dict(positions);newp[g.id]=new
   assert abs(engine.delta(positions,g.id,new)-(cost(groups,newp)-cost(groups,positions)))<1e-6
  t=time.perf_counter();old,oldval,oldmoves,_,_=refine(groups,start,L,exact=True,max_passes=5);slow=time.perf_counter()-t
  t=time.perf_counter();new,newval,newmoves,cache_size=fast_refine(groups,start,L,exact=True,max_passes=5);fast=time.perf_counter()-t
  assert old==new and abs(oldval-newval)<1e-6 and oldmoves==newmoves
  rows.append(dict(video=f'Vid{vid}',seed=r['seed'],starting_overlap=cost(groups,start),final_overlap=newval,baseline_seconds=round(slow,6),cached_seconds=round(fast,6),speedup=round(slow/fast,3),placements_equal=True,candidate_moves=newmoves,cached_pair_offsets=cache_size))
  print(rows[-1],flush=True)
out=R/'pceo_cached_refinement'
with (out/'results.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('MEDIAN SPEEDUP',statistics.median(r['speedup'] for r in rows))
