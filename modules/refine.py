import csv,sys,time,collections,ast
from pathlib import Path
import numpy as np
R=Path('/mnt/data');sys.path[:0]=[str(R/'pceo_fgs_alignment_fix'),str(R/'pceo_fgs_integrated'),str(R/'pceo_fgs_integrated/pceo_full_bundle_v32/project_original/src')]
from validate_alignment import select
from timing_corrected import TimingPreservingGroup
from pceo.tubes import Tube
from pceo.sequential import pceo_sequential

def build(vid):
    import importlib.util
    spec=importlib.util.spec_from_file_location('fgs_duration',R/'pceo_fgs_duration_corrected/synopsis.py');fg=importlib.util.module_from_spec(spec);spec.loader.exec_module(fg)
    ts=select(vid);byid={str(t.id):t for t in ts}
    groups=fg.group_tubes(ts,25,1,.5,1);ts,groups=fg.sort_and_adjust_groups(ts,groups);ts,_=fg.arrange_tubes(ts,groups,[],.99,1,.1)
    fshifts={str(t.id):int(t.first_frame_synopsis-t.first_frame) for t in ts}
    frames=[int(f+fshifts[str(t.id)]) for t in ts for f in t.frame_number]
    span=max(frames)-min(frames)+1
    gg=[]
    for j,ids in enumerate(groups):
        gg.append(TimingPreservingGroup(str(j),[Tube(str(oid),np.asarray(byid[str(oid)].frame_number),np.asarray(byid[str(oid)].boxes,float),original_start=byid[str(oid)].first_frame,group=str(j)) for oid in ids]))
    return gg,span

def cost(groups,starts):
    at=collections.defaultdict(list)
    for g in groups:
        anchor=min(int(t.frames[0]) for t in g.tubes)
        for t in g.tubes:
            for f,b in zip(t.frames,t.boxes):
                at[int(f-anchor+starts[g.id])].append((int(f),b))
    val=0.
    for obs in at.values():
        for i in range(len(obs)):
            f,a=obs[i]
            for j in range(i+1,len(obs)):
                ff,b=obs[j]
                if f==ff:continue
                val+=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    return val

def actual_span(groups,starts):
    ends=[(starts[g.id],starts[g.id]+g.length-1) for g in groups]
    return max(e for s,e in ends)-min(s for s,e in ends)+1

def refine(groups,initial,budget,exact=False,max_passes=4):
    starts=dict(initial);base=cost(groups,starts);initial_span=actual_span(groups,starts)
    if any(starts[g.id]<1 or starts[g.id]+g.length-1>budget for g in groups):raise ValueError('infeasible initial placement')
    moves=0; t0=time.perf_counter()
    for p in range(max_passes):
        improved=False
        for g in sorted(groups,key=lambda x:x.id):
            cur=starts[g.id];best=base;best_start=cur
            candidates={1,budget-g.length+1}
            for delta in (-32,-16,-8,-4,-2,-1,1,2,4,8,16,32):candidates.add(cur+delta)
            for st in sorted(candidates):
                if st<1 or st+g.length-1>budget or st==cur:continue
                starts[g.id]=st
                if exact and actual_span(groups,starts)!=budget:continue
                value=cost(groups,starts)
                if value<best-1e-8:best=value;best_start=st
            starts[g.id]=best_start
            if best_start!=cur:base=best;improved=True;moves+=1
        if not improved:break
    return starts,base,moves,time.perf_counter()-t0,initial_span

def main():
    rows=[]
    for vid in range(1,7):
        groups,budget=build(vid)
        for seed in (7,17):
            result=pceo_sequential(groups,budget,cube_size=128,iterations=8,seed=seed)
            starts={k:int(v) for k,v in result['placements'].items()}
            initial=cost(groups,starts);init_span=actual_span(groups,starts)
            final,after,moves,elapsed,_=refine(groups,starts,budget,exact=(init_span==budget))
            rows.append(dict(video=f'Vid{vid}',seed=seed,budget=budget,initial_span=init_span,final_span=actual_span(groups,final),exact_match_initial=init_span==budget,initial_false_overlap=round(initial,2),refined_false_overlap=round(after,2),improvement=round(initial-after,2),moves=moves,refinement_seconds=round(elapsed,4)))
            print(rows[-1],flush=True)
    out=R/'pceo_collision_refinement/results.csv'
    with out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
if __name__=='__main__':main()
