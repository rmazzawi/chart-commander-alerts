import pandas as pd, numpy as np
from datetime import time as T
from orb15 import exit_sim  # reuse trail exit (re-runs orb15 prints; ignore)
A=pd.read_pickle('DOC.pkl'); D={tk:pd.read_pickle(f'D_{tk}.pkl').reset_index(drop=True) for tk in A.tk.unique()}
LV=['PM high','PM low','Prior-day high','Prior-day low','OR high (30m)','OR low (30m)','Equal highs','Equal lows','VWAP']
def targets(r):
    d=D[r.tk]; b=d.iloc[r.i]; e=r.entry; dr=r.dir; risk=abs(e-r.stop)
    day=d[(d.date==b.date)&(d.index<=r.i)&(d.t.dt.time>=T(9,30))]
    lv=[b[c] for c in LV if not pd.isna(b[c])]+([day.high.max(),day.low.min()] if len(day) else [])
    def nxt(px):
        c=[l for l in lv if (l-px)*dr>risk*0.5]; return min(c,key=lambda l:abs(l-px)) if c else None
    a=nxt(e); t1=e+dr*risk if a is None else (min(a,e+risk*1.5) if dr==1 else max(a,e-risk*1.5))
    if r.s==2 and (b.VWAP-e)*dr>risk*0.5: t1=b.VWAP
    return t1
def sim_pp(r,t1,frac,lock):
    d=D[r.tk]; e=r.entry; dr=r.dir; st=r.stop; risk=abs(e-st); half=False; got=0; trail=False; armed=False
    if risk<=0: return 0
    for k in range(r.i+1,len(d)):
        x=d.iloc[k]; tm=x.t.time()
        if k-r.i>=3:
            w=d.iloc[k-3:k]
            if (w.close.iloc[-1]-e)*dr>0: trail=True
            if trail: st=max(st,w.low.min()) if dr==1 else min(st,w.high.max())
        hi=x.high if dr==1 else -x.low; lo=x.low if dr==1 else -x.high; E=e*dr; S=st*dr; T1=t1*dr
        if lo<=S: return (got+(S-E)*(0.5 if half else 1))/risk
        if frac and not armed and hi>=E+frac*(T1-E): armed=True; st=max(st,e+lock*(t1-e)) if dr==1 else min(st,e+lock*(t1-e))
        if not half and hi>=T1: half=True; got=0.5*(T1-E); st=max(st,e) if dr==1 else min(st,e)
        if tm>=T(15,44): return (got+(x.close*dr-E)*(0.5 if half else 1))/risk
    return got/risk
A['t1']=A.apply(targets,axis=1)
def s(v,P): return f"{len(P):4d} {(v>0).mean()*100:3.0f}% {v.sum():7.1f}R"
print('\n#5 PROFIT PROTECTION (same simulator for all rows, so compare rows to each other)')
for nm,fr,lk in [('no protection (script-like)',None,0),('at 80% of T1 -> lock 50%',0.8,0.5),('at 85% of T1 -> lock 60%',0.85,0.6),('at 90% of T1 -> lock 70%',0.9,0.7)]:
    v=A.apply(lambda r:sim_pp(r,r.t1,fr,lk),axis=1); A[nm]=v
    print(f"  {nm:30s}", ' | '.join(f"{p}: {s(v[A.per==p],A[A.per==p])}" for p in ['early','late']))
# #6 FIB PULLBACK
rows=[]
for tk,d in D.items():
    for day,g in d.groupby('date'):
        g=g[(g.t.dt.time>=T(9,30))&(g.t.dt.time<T(11,0))]
        if len(g)<10: continue
        idx=list(g.index); f=d.loc[idx[0]]; dr=1 if f.close>=f.open else -1
        start=f.low if dr==1 else f.high; ext=f.high if dr==1 else f.low; k=1
        while k<len(idx):
            c=d.loc[idx[k]]
            if (c.close-c.open)*dr<0: break
            ext=max(ext,c.high) if dr==1 else min(ext,c.low); k+=1
        leg=abs(ext-start)
        if leg<f.atr*0.5 or k>=len(idx): continue
        f50=ext-dr*0.5*leg; f618=ext-dr*0.618*leg; f786=ext-dr*0.786*leg; touched=False
        for j in idx[k:]:
            c=d.loc[j]
            if (c.low-f786 if dr==1 else f786-c.high)<0: break          # broke 0.786 -> idea dead
            if (c.low<=f50) if dr==1 else (c.high>=f50): touched=True
            if touched and (c.close-c.open)*dr>0 and (c.close-d.loc[j-1].high if dr==1 else d.loc[j-1].low-c.close)>0:
                st=f786-dr*0.1*c.atr; R=exit_sim(d,j,dr,c.close,st) if abs(c.close-st)<=1.5*c.atr else None
                if R is not None: rows.append(dict(tk=tk,t=c.t,R=R))
                break
F=pd.DataFrame(rows); F=F[F.t>='2026-07-27']; F['per']=np.where(F.t>='2026-09-04','late','early')
print('\n#6 FIB PULLBACK (first move of the day -> pullback to 0.5-0.618 -> continuation candle; stop beyond 0.786)')
for p in ['early','late']: P=F[F.per==p]; print(f"  {'Jul27-Sep3' if p=='early' else 'Sep4-Oct2 '}", s(P.R,P))
print(F.groupby('tk').R.agg(['size','sum']).round(1).T.to_string())
print('\n#5 per ticker (80%->lock 50% minus no protection), R')
A['gain']=A['at 80% of T1 -> lock 50%']-A['no protection (script-like)']
g=A.groupby(['tk','per']).gain.sum().unstack().round(1); print(g.T.to_string()); print('tickers better: early',(g.early>=0).sum(),'late',(g.late>=0).sum())
# with #1 combined
k=pd.Series(True,index=A.index)
for (tk,dd),gg in A.sort_values('t').groupby(['tk','d']):
    l=0
    for i,r in gg.iterrows():
        if l>=2: k[i]=False
        else: l+=(r['at 80% of T1 -> lock 50%']<=0)
for p in ['early','late']: P=A[(A.per==p)&k]; print('  #1 + #5 together',p,s(P['at 80% of T1 -> lock 50%'],P))
# #6 loose: leg = opening move over first 15 min (9:30-9:45) extreme in direction of 9:45 close vs open
rows=[]
for tk,d in D.items():
    for day,g in d.groupby('date'):
        g=g[(g.t.dt.time>=T(9,30))&(g.t.dt.time<T(11,30))]; o=g[g.t.dt.time<T(9,45)]
        if len(o)<7: continue
        dr=1 if o.close.iloc[-1]>o.open.iloc[0] else -1
        start=o.low.min() if dr==1 else o.high.max(); ext=o.high.max() if dr==1 else o.low.min(); leg=abs(ext-start)
        if leg<o.atr.iloc[-1]*1.0: continue
        f50=ext-dr*0.5*leg; f786=ext-dr*0.786*leg; touched=False
        for j in g[g.t.dt.time>=T(9,45)].index:
            c=d.loc[j]
            if (c.high>ext) if dr==1 else (c.low<ext):
                if not touched: ext=c.high if dr==1 else c.low; leg=abs(ext-start); f50=ext-dr*0.5*leg; f786=ext-dr*0.786*leg; continue
            if (c.low<f786) if dr==1 else (c.high>f786): break
            if (c.low<=f50) if dr==1 else (c.high>=f50): touched=True
            if touched and (c.close-c.open)*dr>0 and ((c.close>d.loc[j-1].high) if dr==1 else (c.close<d.loc[j-1].low)):
                st=f786-dr*0.1*c.atr
                if abs(c.close-st)<=1.5*c.atr: rows.append(dict(tk=tk,t=c.t,R=exit_sim(d,j,dr,c.close,st)))
                break
F=pd.DataFrame(rows); F=F[F.t>='2026-07-27']; F['per']=np.where(F.t>='2026-09-04','late','early')
print('\n#6b FIB PULLBACK of the first 15-min move (loosened)')
for p in ['early','late']: P=F[F.per==p]; print(f"  {'Jul27-Sep3' if p=='early' else 'Sep4-Oct2 '}", s(P.R,P))
