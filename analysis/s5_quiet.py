# Test A (10/7): S5 trend pullback without the volume rule on "quiet trend" days.
# Approximate S5: 10m trend (last completed 10m close above VWAP and above its 34/50 EMAs) -> 2m low dips into the 2m 34/50 cloud or VWAP
# -> within 20 bars a 2m close reclaims the 9 & 20 EMA (prev close <= 20 EMA) -> enter at that close (no retest step here), stop below the pullback low.
# Compare: volume rule ON (RVOL>=1 on the reclaim, like the script) vs OFF, and OFF only when price stayed above VWAP >=80% of the last 60 min.
# Run from work/: python ../analysis/s5_quiet.py
import pandas as pd, numpy as np, glob, sys, os, contextlib, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()): from pinbar import exit_trail, exit_fixed
from datetime import time as T
rows=[]
for f in sorted(glob.glob('D_*.pkl')):
    tk=f[2:-4]; d=pd.read_pickle(f).reset_index(drop=True)
    b10=d.t.dt.floor('10min'); g=d.groupby(b10).agg(c10=('close','last'),v10=('VWAP','last'))
    g['h34']=g.c10.ewm(span=34,adjust=False).mean(); g['h50']=g.c10.ewm(span=50,adjust=False).mean(); g=g.shift(1)
    d=d.join(g,on=b10)
    bull=(d.c10>d.v10)&(d.c10>d[['h34','h50']].max(axis=1)); bear=(d.c10<d.v10)&(d.c10<d[['h34','h50']].min(axis=1))
    side=np.sign(d.close-d.VWAP); d['vwL']=(side>0).rolling(30).mean(); d['vwS']=(side<0).rolling(30).mean()
    tm=d.t.dt.time
    for dr,tr in ((1,bull),(-1,bear)):
        cl=d[['EMA 34','EMA 50']].max(axis=1) if dr==1 else d[['EMA 34','EMA 50']].min(axis=1)
        touch=tr&(((d.low-cl)*dr<=0)|((d.low if dr==1 else d.high)-d.VWAP)*dr<=0) if dr==1 else tr&(((d.high-cl)*dr<=0)|((d.high-d.VWAP)*dr<=0))
        last=None; ext=None; lastTrade=-99
        for i in range(1,len(d)):
            if touch[i]:
                ext=(d.low[i] if dr==1 else d.high[i]) if last is None or i-last>30 else (min(ext,d.low[i]) if dr==1 else max(ext,d.high[i]))
                last=i
            if last is None or i-last>20 or not tr[i] or not(T(10,0)<=tm[i]<T(15,0)) or T(12,30)<=tm[i]<T(14,0) or i-lastTrade<10: continue
            c=d.close[i]
            if (c-d['EMA 9'][i])*dr>0 and (c-d['EMA 20'][i])*dr>0 and (d.close[i-1]-d['EMA 20'][i-1])*dr<=0:
                st=ext-dr*0.05*d.atr[i]
                if (c-st)*dr<=0 or abs(c-st)>2*d.atr[i]: continue
                lastTrade=i
                rows.append(dict(tk=tk,t=d.t[i],dr=dr,rvol=d.RVOL[i],quiet=(d.vwL[i] if dr==1 else d.vwS[i])>=0.8,stp=abs(c-st)/c*100,
                    R1=exit_fixed(d,i,dr,c,st,1),R=exit_trail(d,i,dr,c,st)))
P=pd.DataFrame(rows); P=P[P.t>='2026-07-27']; P['per']=np.where(P.t>='2026-09-04','late','early'); P.to_pickle('S5Q.pkl')
def s(Q): return f"{len(Q):4d} tr | script exits: {(Q.R>0).mean()*100:3.0f}% {Q.R.sum():+6.1f}R ({Q.R.mean():+.2f}/tr) | 1R: {(Q.R1>0).mean()*100:3.0f}% {Q.R1.sum():+6.1f}R"
V=[('NOW: volume rule ON (RVOL>=1)',P.rvol>=1),('A: volume rule OFF (all)',P.rvol>-1),
   ('A2: volume OFF only when trend is clean (>=80% of last hour on VWAP side)',(P.rvol>=1)|P.quiet),
   ('only the NEW trades A2 adds (low volume + clean trend)',(P.rvol<1)&P.quiet),('low volume + NOT clean trend',(P.rvol<1)&~P.quiet)]
for n,k in V:
    print('\n==',n)
    for p,lab in [('early','good month'),('late','bad month ')]: print('  ',lab,s(P[k&(P.per==p)]))
K=P[(P.rvol<1)&P.quiet]; g=K.groupby(['tk','per']).R.sum().unstack().round(1); print('\nnew trades by ticker (script exits R):'); print(g.T.to_string()); print('positive both months:',((g.early>0)&(g.late>0)).sum(),'/',len(g))
