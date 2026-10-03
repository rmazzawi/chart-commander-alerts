import pandas as pd, numpy as np
from datetime import time as T
D={}
import glob,re
for f in glob.glob('D_*.pkl'):
    tk=f[2:-4]
    if tk in ('SPY','QQQ','IWM','AAPL','MSFT','NVDA','AMZN','META','TSLA','AMD','GLD','SPX'): D[tk]=pd.read_pickle(f)
def exit_sim(d,j,dr,e,st):
    risk=abs(e-st); half=False; got=0; trail=False
    for k in range(j+1,len(d)):
        r=d.iloc[k]; tm=r.t.time()
        # trail on last completed 5m candle (approx: prior 3 bars low/high once in profit)
        if k-j>=3:
            w=d.iloc[k-3:k]; c5=w.close.iloc[-1]
            if (c5-e)*dr>0: trail=True
            if trail: st = max(st,w.low.min()) if dr==1 else min(st,w.high.max())
        lo,hi=(r.low,r.high) if dr==1 else (-r.high,-r.low); E=e*dr; S=st*dr
        if lo<=S: return (got+(S-E)*(0.5 if half else 1))/risk
        if not half and hi>=E+risk: half=True; got=0.5*risk; st=max(st,e) if dr==1 else min(st,e)
        if tm>=T(15,44): return (got+(r.close*dr-E)*(0.5 if half else 1))/risk
    return got/risk
rows=[]
for tk,d in D.items():
    d=d.reset_index(drop=True)
    for day,g in d.groupby('date'):
        g=g[(g.t.dt.time>=T(9,30))&(g.t.dt.time<T(16,0))]
        rg=g[g.t.dt.time<T(9,45)]
        if len(rg)<7: continue
        H,L=rg.high.max(),rg.low.min(); idx=list(g[(g.t.dt.time>=T(9,45))&(g.t.dt.time<T(11,0))].index)
        done={1:False,-1:False}
        for n,i in enumerate(idx[:-2]):
            r=d.loc[i]
            for dr,lvl in [(1,H),(-1,L)]:
                if done[dr]: continue
                if (r.close-lvl)*dr>0 and (d.loc[i-1].close-lvl)*dr<=0:
                    a,b=d.loc[i+1],d.loc[i+2]
                    ok = (a.low>lvl and b.low>lvl) if dr==1 else (a.high<lvl and b.high<lvl)
                    done[dr]=True
                    if not ok: continue
                    e=b.close; st=lvl-0.25*b.atr*dr; risk=abs(e-st)
                    if risk<=0 or risk>1.5*b.atr: continue
                    R=exit_sim(d,i+2,dr,e,st)
                    rows.append(dict(tk=tk,t=b.t,dir=dr,R=R,win=R>0))
O=pd.DataFrame(rows); O=O[O.t>='2026-07-27']; O['per']=np.where(O.t>='2026-09-04','late','early')
def s(P): return f"{len(P):4d} {P.win.mean()*100:3.0f}% {P.R.sum():7.1f}R"
for per in ['early','late']: print('15m range break', 'Jul27-Sep3' if per=='early' else 'Sep4-Oct2 ', s(O[O.per==per]))
print(O.groupby('tk').R.agg(['size','sum']).round(1).T.to_string())
A=pd.read_pickle('DOC.pkl'); S1=A[A.s==1]
for per in ['early','late']: print('existing S1 (30m)', per, s(S1[S1.per==per]))
