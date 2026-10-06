# "Breakdown with no pullback": price chops around VWAP, then a candle closes below the chop range AND below VWAP,
# and the next 3 candles do not reclaim VWAP -> enter puts at the 3rd candle close (mirror for calls).
# Stop above the highest high since the break. Exits: 1R target, 2R target, script-like trail. Not lunch, 10:00-15:00.
# Run from work/: python ../analysis/vwap_nopb.py
import pandas as pd, numpy as np, glob, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinbar import exit_trail, exit_fixed
from datetime import time as T
rows=[]
for f in sorted(glob.glob('D_*.pkl')):
    tk=f[2:-4]; d=pd.read_pickle(f).reset_index(drop=True); tm=d.t.dt.time
    side=np.sign(d.close-d.VWAP); d['cross']=(side!=side.shift()).astype(int).rolling(20).sum()
    d['rlo']=d.low.shift().rolling(10).min(); d['rhi']=d.high.shift().rolling(10).max()
    d['vavg']=d.Volume.rolling(20).mean()
    done=set()
    for j in np.where((tm>=T(10,0))&(tm<T(15,0)))[0]:
        b=d.iloc[j]
        if T(12,24)<=b.t.time()<T(14,0) or j+4>=len(d): continue
        for dr in (1,-1):
            if (b.date,dr) in done: continue
            brk=(b.close-b.VWAP)*dr>0 and (b.close-(b.rhi if dr==1 else b.rlo))*dr>0
            if not brk: continue
            w=d.iloc[j+1:j+4]
            if ((w.close-w.VWAP)*dr<=0).any() or w.date.iloc[-1]!=b.date: continue
            k=j+3; e=d.close[k]
            st=(d.low[j:k+1].min() if dr==1 else d.high[j:k+1].max())-dr*0.05*b.atr
            if (e-st)*dr<=0: continue
            done.add((b.date,dr))
            rows.append(dict(tk=tk,t=b.t,dr=dr,chop=b.cross>=4,vol=b.Volume>=b.vavg,day=np.sign(b.close-b.dopen)*dr,
                stp=abs(e-st)/e*100,R1=exit_fixed(d,k,dr,e,st,1),R2=exit_fixed(d,k,dr,e,st,2),R=exit_trail(d,k,dr,e,st)))
P=pd.DataFrame(rows); P=P[P.t>='2026-07-27']; P['per']=np.where(P.t>='2026-09-04','late','early'); P.to_pickle('NOPB.pkl')
def s(Q): return f"{len(Q):3d} tr | 1R: {(Q.R1>0).mean()*100:3.0f}% {Q.R1.sum():+6.1f}R | 2R: {(Q.R2>0).mean()*100:3.0f}% {Q.R2.sum():+6.1f}R | trail: {(Q.R>0).mean()*100:3.0f}% {Q.R.sum():+6.1f}R | stop {Q.stp.median():.2f}%"
for n,k in [('A all breaks that hold 3 candles',P.t.notna()),('B after chop (>=4 VWAP crosses in 40 min)',P.chop),
            ('C B + break candle above-avg volume',P.chop&P.vol),('D B + with the day direction',P.chop&(P.day>0)),('E no chop before',~P.chop)]:
    print('\n==',n)
    for p,lab in [('early','good month'),('late','bad month ')]: print('  ',lab,s(P[k&(P.per==p)]))
