# Day low/high retest pin (CC-Multi V8 alert) with looser 'moved into the level' rules. Based on pinbar_tf.py
# Pin bar at a key level on higher timeframes (5,10,15,20,30,60,65 min). Candles built from the 2m data (RTH, anchored 9:30).
# Entry: price breaks the pin's high/low within the next 3 candles of that timeframe (checked on 2m bars). Stop: beyond the pin tip.
# Run from work/: python ../analysis/pinbar_tf.py
import pandas as pd, numpy as np, glob
from datetime import time as T
LV=['Prior-day low','PM low','OR low (30m)','Equal lows','VWAP','SMA 200','SMA 400','Prior-day high','PM high','OR high (30m)','Equal highs']
def fixed(d,k,dr,e,st,tgt):
    risk=abs(e-st)
    for i in range(k,len(d)):
        r=d.iloc[i]; lo,hi=(r.low,r.high) if dr==1 else (-r.high,-r.low)
        if lo<=st*dr: return -1.0
        if i>k and hi>=e*dr+tgt*risk: return tgt
        if r.t.time()>=T(15,44): return (r.close-e)*dr/risk
    return 0.0
out=[]
for f in sorted(glob.glob('D_*.pkl')):
    tk=f[2:-4]; d=pd.read_pickle(f).reset_index(drop=True)
    d=d[(d.t.dt.time>=T(9,30))&(d.t.dt.time<T(16,0))].reset_index(drop=True)
    d['m']=(d.t.dt.hour*60+d.t.dt.minute)-570
    for tf in [2]:
        d['g']=d.m//tf
        agg=d.groupby(['date','g']).agg(t=('t','first'),i0=('t',lambda s:s.index[0]),i1=('t',lambda s:s.index[-1]),open=('open','first'),
            high=('high','max'),low=('low','min'),close=('close','last'),vol=('Volume','sum'),**{c:(c,'first') for c in LV}).reset_index()
        tr=pd.concat([agg.high-agg.low,(agg.high-agg.close.shift()).abs(),(agg.low-agg.close.shift()).abs()],axis=1).max(axis=1)
        agg['atr']=tr.rolling(14).mean(); agg['vavg']=agg.vol.rolling(20).mean()
        agg['lod']=agg.groupby('date').low.cummin().groupby(agg.date).shift(); agg['hod']=agg.groupby('date').high.cummax().groupby(agg.date).shift()
        agg['c3']=agg.close.shift(3); agg['h10']=agg.high.rolling(10).max(); agg['l10']=agg.low.rolling(10).min()
        for j,b in agg.iterrows():
            a=b.atr; rng=b.high-b.low
            if pd.isna(a) or rng<0.5*a or b.t.time()>=T(15,0) or b.t.time()<T(9,36): continue
            body=abs(b.close-b.open)
            for dr in (1,-1):
                wick=(min(b.open,b.close)-b.low) if dr==1 else (b.high-max(b.open,b.close))
                if wick<0.6*rng or body>0.35*rng: continue
                tip=b.low if dr==1 else b.high
                if pd.isna(b.c3): continue
                d3=(b.c3-tip)*dr/a; d10=((b.h10-tip) if dr==1 else (tip-b.l10))/a
                lv=[(c,b[c]) for c in LV if not pd.isna(b[c])]+[('Day low/high retest',b.lod if dr==1 else b.hod)]
                hit=[c for c,L in lv if not pd.isna(L) and abs(tip-L)<=0.15*a and (b.close-L)*dr>0]
                if not hit: continue
                trig=b.high if dr==1 else b.low; st=tip-dr*0.05*a; e=None
                lim=agg.i1.iloc[min(j+3,len(agg)-1)] if agg.date.iloc[min(j+3,len(agg)-1)]==b.date else d[d.date==b.date].index[-1]
                for k in range(b.i1+1,lim+1):
                    x=d.iloc[k]
                    if ((x.low if dr==1 else x.high)-st)*dr<=0: break
                    if ((x.high if dr==1 else x.low)-trig)*dr>0: e=trig; break
                if e is None: continue
                out.append(dict(d3=d3,d10=d10,dl=any(c=='Day low/high retest' for c in hit),tf=tf,tk=tk,t=b.t,dr=dr,lvl=hit[0],vol=b.vol>=b.vavg,stp=abs(e-st)/e*100,
                    R1=fixed(d,k,dr,e,st,1),R2=fixed(d,k,dr,e,st,2),lunch=T(12,30)<=b.t.time()<T(14,0)))
                break
P=pd.DataFrame(out); P=P[(P.t>='2026-07-27')&P.dl&~P.lunch]; P['per']=np.where(P.t>='2026-09-04','late','early'); P.to_pickle('PINLOOSE.pkl')
V=[('V8 now: fast drop >= 1 ATR in last 3 candles',P.d3>=1),('looser: >= 0.5 ATR in last 3 candles',P.d3>=0.5),
   ('looser: any drop in last 3 candles',P.d3>0),('slow drift: >= 1.5 ATR over last 10 candles',P.d10>=1.5),
   ('V8 OR slow drift (1.5 ATR / 10 candles)',(P.d3>=1)|(P.d10>=1.5)),('only the slow ones (not caught by V8)',(P.d3<1)&(P.d10>=1.5)),('no drop rule at all',P.d3>-99)]
for n,k in V:
    print(f"{n:48s}"," | ".join(f"{lab}: {len(q):3d} tr {(q.R1>0).mean()*100:3.0f}% {q.R1.sum():+5.1f}R" for lab,q in [('good',P[k&(P.per=='early')]),('bad',P[k&(P.per=='late')])]))
