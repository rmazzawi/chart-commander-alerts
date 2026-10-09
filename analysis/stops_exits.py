# 10/9: "right direction, shaken out too early". Same v4 entries (SIM.pkl: 400SMA rule, lunch removed), different stops / exits / entry timing.
# R is always measured in units of the stop distance actually used (= same $ risk per trade: wider stop -> fewer contracts).
# Run from work/: python ../analysis/stops_exits.py
import pandas as pd, numpy as np
from datetime import time as T
A=pd.read_pickle('SIM.pkl'); A=A[~((A.mins>=180)&(A.mins<270))].sort_values('t').copy()
D={}
for tk in A.tk.unique():
    d=pd.read_pickle(f'D_{tk}.pkl').reset_index(drop=True)
    b=d.t.dt.floor('10min'); g=d.groupby(b).agg(h10=('high','max'),l10=('low','min'),c10=('close','last'),o10=('open','first'))
    tr=pd.concat([g.h10-g.l10,(g.h10-g.c10.shift()).abs(),(g.l10-g.c10.shift()).abs()],axis=1).max(axis=1)
    g['atr10']=tr.rolling(14).mean(); g=g.shift(1)                     # last COMPLETED 10m candle
    d=d.join(g,on=b); d['new10']=b!=b.shift(); D[tk]=d
def run(d,i,dr,e,st,trail='2m',t1=1.0):
    risk=abs(e-st); half=False; got=0; on=False; day=d.date[i]
    for k in range(i+1,len(d)):
        r=d.iloc[k]
        if r.date!=day: return (got+(d.close[k-1]-e)*dr*(0.5 if half else 1))/risk
        if trail=='2m' and k-i>=3:
            w=d.iloc[k-3:k]
            if (w.close.iloc[-1]-e)*dr>0: on=True
            if on: st=max(st,w.low.min()) if dr==1 else min(st,w.high.max())
        if trail=='10m' and r.new10 and not pd.isna(r.l10) and k-i>=5:
            if (r.c10-e)*dr>0: on=True
            if on: st=max(st,r.l10) if dr==1 else min(st,r.h10)
        lo,hi=(r.low,r.high) if dr==1 else (-r.high,-r.low)
        if lo<=st*dr: return (got+(st-e)*dr*(0.5 if half else 1))/risk
        if t1 and not half and hi>=e*dr+t1*risk: half=True; got=0.5*t1*risk; st=max(st,e) if dr==1 else min(st,e)
        if r.t.time()>=T(15,44): return (got+(r.close-e)*dr*(0.5 if half else 1))/risk
    return got/risk
def variant(name,fn):
    out=[]
    for x in A.itertuples():
        d=D[x.tk]; res=fn(d,x)
        if res is None: continue
        st=getattr(fn,'st',None)
        out.append((x.per,res,d.close[x.i]))
    O=pd.DataFrame(out,columns=['per','R','px'])
    cells=[]
    for p in ['early','late']:
        q=O[O.per==p].R; cells.append(f"{len(q):3d} tr {(q>0).mean()*100:3.0f}% {q.sum():+6.1f}R ({q.mean():+.2f}/tr)")
    print(f"{name:52s} | "+" | ".join(cells))
risk0=lambda x:abs(x.entry-x.stop)
print(f"{'variant':52s} | {'good month (Jul27-Sep3)':30s} | bad month (Sep4-Oct2)")
variant('NOW: script stop, trail 2m (approx), T1 1R',lambda d,x: run(d,x.i,x.dir,x.entry,x.stop))
for m in [1.5,2.0,3.0]:
    variant(f'stop x{m} wider, trail 2m',lambda d,x,m=m: run(d,x.i,x.dir,x.entry,x.entry-x.dir*m*risk0(x)))
for m in [1.5,2.0,3.0]:
    variant(f'stop x{m} wider, trail on 10m candles',lambda d,x,m=m: run(d,x.i,x.dir,x.entry,x.entry-x.dir*m*risk0(x),'10m'))
for k in [0.5,1.0]:
    variant(f'stop {k} x 10m-ATR, trail on 10m candles',lambda d,x,k=k: None if pd.isna(d.atr10[x.i]) else run(d,x.i,x.dir,x.entry,x.entry-x.dir*k*d.atr10[x.i],'10m'))
variant('stop beyond last completed 10m candle, trail 10m',lambda d,x: None if pd.isna(d.l10[x.i]) or (x.entry-(d.l10[x.i] if x.dir==1 else d.h10[x.i]))*x.dir<=0 else
        run(d,x.i,x.dir,x.entry,(d.l10[x.i] if x.dir==1 else d.h10[x.i])-x.dir*0.02*d.atr[x.i],'10m'))
variant('original stop, trail on 10m candles',lambda d,x: run(d,x.i,x.dir,x.entry,x.stop,'10m'))
variant('stop x2, trail 10m, T1 at 1.5R',lambda d,x: run(d,x.i,x.dir,x.entry,x.entry-x.dir*2*risk0(x),'10m',1.5))
variant('stop x2, trail 10m, no T1 (let it run)',lambda d,x: run(d,x.i,x.dir,x.entry,x.entry-x.dir*2*risk0(x),'10m',None))
# entry confirmation: wait for the 10m candle that contains the alert to close in our direction, enter at that close
def conf(d,x,m=2.0):
    j=x.i+1
    while j<len(d) and not d.new10[j]: j+=1
    if j>=len(d) or d.date[j]!=d.date[x.i]: return None
    c=d.close[j-1]
    if (c-x.entry)*x.dir<=0: return None              # 10m candle did not confirm -> skip
    st=c-x.dir*m*risk0(x); return run(d,j-1,x.dir,c,st,'10m')
variant('WAIT for 10m close confirm, stop x2, trail 10m',conf)
# ---- option cost check: every trade pays a round-trip cost (spread + fees) of C% of the stock price, expressed in R = C / stop%.
print('\nWITH COSTS (round trip cost as % of stock price; 0.02% ~ liquid 0DTE, 0.04% ~ wider-spread names)')
def costed(name,stopfn,fn):
    for C in [0.02,0.04]:
        cells=[]
        for p in ['early','late']:
            tot=0;n=0
            for x in A[A.per==p].itertuples():
                d=D[x.tk]; st=stopfn(d,x)
                if st is None: continue
                r=fn(d,x,st)
                if r is None: continue
                tot+=r-C/(abs(x.entry-st)/x.entry*100); n+=1
            cells.append(f"{n:3d} tr {tot:+6.1f}R")
        print(f"{name:40s} cost {C:.2f}% | good: {cells[0]} | bad: {cells[1]}")
costed('NOW (script stop, 2m trail)',lambda d,x:x.stop,lambda d,x,st:run(d,x.i,x.dir,x.entry,st))
costed('original stop, 10m trail',lambda d,x:x.stop,lambda d,x,st:run(d,x.i,x.dir,x.entry,st,'10m'))
costed('stop x2, 10m trail',lambda d,x:x.entry-x.dir*2*risk0(x),lambda d,x,st:run(d,x.i,x.dir,x.entry,st,'10m'))
costed('stop x3, 10m trail',lambda d,x:x.entry-x.dir*3*risk0(x),lambda d,x,st:run(d,x.i,x.dir,x.entry,st,'10m'))
costed('stop 0.5 x 10m-ATR, 10m trail',lambda d,x:None if pd.isna(d.atr10[x.i]) else x.entry-x.dir*0.5*d.atr10[x.i],lambda d,x,st:run(d,x.i,x.dir,x.entry,st,'10m'))
costed('stop x2, 10m trail, no T1',lambda d,x:x.entry-x.dir*2*risk0(x),lambda d,x,st:run(d,x.i,x.dir,x.entry,st,'10m',None))
