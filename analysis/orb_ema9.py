# User idea (10/7): break of the first 30-min range (9:30-10:00), then a retest of the 9 EMA on the 2m AND 5m charts,
# then entry only if the trend agrees. Calls above the range high, puts below the range low (mirror).
#  - break: a 2m candle closes beyond the 30m range high (low) after 10:00
#  - retest: later a 2m candle touches the 2m EMA9 and the 5m EMA9 (last completed 5m candle) - "interaction"
#  - entry: the first 2m candle after the touch that closes back beyond the 2m EMA9 in the trade direction
#  - trend filter (variants): above VWAP, 2m EMA9>EMA20, 5m close>5m EMA9, still beyond the range
#  - stop: beyond the lowest low (highest high) since the touch, minus 0.05 ATR. One trade per side per day. Entries 10:00-15:00.
# 5m candles are built from 2m bars (each 2m bar goes to the 5m bucket it starts in) - a close approximation.
# Run from work/: python ../analysis/orb_ema9.py
import pandas as pd, numpy as np, glob, sys, os, contextlib, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()): from pinbar import exit_trail, exit_fixed
from datetime import time as T
rows=[]
for f in sorted(glob.glob('D_*.pkl')):
    tk=f[2:-4]; d=pd.read_pickle(f).reset_index(drop=True)
    d['e9']=d.close.ewm(span=9,adjust=False).mean(); d['e20']=d.close.ewm(span=20,adjust=False).mean()
    b5=d.t.dt.floor('5min'); g=d.groupby(b5).agg(c5=('close','last'))
    g['e95']=g.c5.ewm(span=9,adjust=False).mean(); g=g.shift(1)            # last COMPLETED 5m candle
    d=d.join(g,on=b5)
    for day,x in d.groupby('date'):
        tm=x.t.dt.time; o=x[(tm>=T(9,30))&(tm<T(10,0))]
        if len(o)<14: continue
        H,L=o.high.max(),o.low.min(); idx=list(x[(tm>=T(10,0))&(tm<T(15,0))].index)
        for dr in (1,-1):
            lvl=H if dr==1 else L; broke=False; touch=None
            for i in idx:
                b=d.loc[i]
                if not broke:
                    if (b.close-lvl)*dr>0: broke=True
                    continue
                if touch is None:
                    lo=b.low if dr==1 else b.high
                    if (lo-b.e9)*dr<=0 and (lo-b.e95)*dr<=0: touch=i
                    continue
                if (b.close-b.e9)*dr>0 and (b.close-b.open)*dr>0:
                    seg=d.loc[touch:i]; ext=seg.low.min() if dr==1 else seg.high.max()
                    st=ext-dr*0.05*b.atr; e=b.close
                    if (e-st)*dr<=0: break
                    rows.append(dict(tk=tk,t=b.t,dr=dr,
                        vw=(b.close-b.VWAP)*dr>0, stk=(b.e9-b.e20)*dr>0, m5=(b.c5-b.e95)*dr>0, outside=(ext-lvl)*dr>0,
                        lunch=T(12,30)<=b.t.time()<T(14,0), stp=abs(e-st)/e*100,
                        R1=exit_fixed(d,i,dr,e,st,1),R2=exit_fixed(d,i,dr,e,st,2),R=exit_trail(d,i,dr,e,st)))
                    break
P=pd.DataFrame(rows); P=P[P.t>='2026-07-27']; P['per']=np.where(P.t>='2026-09-04','late','early'); P.to_pickle('ORBE9.pkl')
def s(Q): return f"{len(Q):3d} tr | 1R: {(Q.R1>0).mean()*100:3.0f}% {Q.R1.sum():+6.1f}R | 2R: {(Q.R2>0).mean()*100:3.0f}% {Q.R2.sum():+6.1f}R | script exits: {(Q.R>0).mean()*100:3.0f}% {Q.R.sum():+6.1f}R | stop {Q.stp.median():.2f}%"
nl=~P.lunch; tr=P.vw&P.stk&P.m5
for n,k in [('A every break + 9 EMA retest (no trend filter)',nl),
            ('B + trend agrees (VWAP side, 9>20 on 2m, 5m above its 9 EMA)',nl&tr),
            ('C B + retest held outside the 30m range',nl&tr&P.outside),
            ('D B + before 12:30 only',nl&tr&(P.t.dt.time<T(12,30)))]:
    print('\n==',n)
    for p,lab in [('early','good month'),('late','bad month ')]: print('  ',lab,s(P[k&(P.per==p)]))
K=P[nl&tr]; g=K.groupby(['tk','per']).R1.sum().unstack().round(1)
print('\nB by ticker (1R):'); print(g.T.to_string()); print('tickers positive in both months:',((g.early>0)&(g.late>0)).sum(),'/',len(g))
