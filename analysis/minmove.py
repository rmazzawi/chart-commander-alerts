# Point 1: skip trades whose T1 (or stop) distance is too small as a % of price. v4-like: 400SMA + lunch + profit-protect 80/50 + 2-loss stop.
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, contextlib, io
with contextlib.redirect_stdout(io.StringIO()): import t56
A=t56.A.sort_values('t').copy(); A['R4']=A['at 80% of T1 -> lock 50%']
A['t1p']=(A.t1-A.entry).abs()/A.entry*100; A['stp']=(A.entry-A.stop).abs()/A.entry*100
def run(keep):
    K=A[keep].copy(); ok=pd.Series(True,index=K.index)
    for _,g in K.groupby(['tk','d']):
        l=0
        for i,r in g.iterrows():
            if l>=2: ok[i]=False
            else: l+=(r.R4<=0)
    return K[ok]
def s(P): return f"{len(P):4d} trades {(P.R4>0).mean()*100:3.0f}% wins {P.R4.sum():6.1f}R  ({P.R4.mean():+.2f}R/trade)"
print('median T1 %:',A.t1p.median().round(2),' median stop %:',A.stp.median().round(2))
for nm,keep in [('v4 now (no minimum)',A.t1p>=0)]+[(f'T1 at least {x}%',A.t1p>=x) for x in [0.2,0.3,0.4]]+[(f'stop at least {x}%',A.stp>=x) for x in [0.15,0.2,0.3]]:
    K=run(keep); print(f'\n== {nm}')
    for p,lab in [('early','Jul27-Sep3'),('late','Sep4-Oct2 ')]: print(' ',lab,s(K[K.per==p]))
    if nm.startswith('T1 at least 0.3'):
        print('  by ticker (R, both periods):',K.groupby('tk').R4.sum().round(1).to_dict())
