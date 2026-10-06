# Pin bar (hammer / shooting star) at a key level -> reversal entry. Tested on all tickers, 2m RTH.
# Run from work/: python ../analysis/pinbar.py
import pandas as pd, numpy as np, glob
from datetime import time as T
def exit_trail(d,j,dr,e,st):   # same exits as the script approximation: T1=1R sell half, stop->BE, trail on 3 bars
    risk=abs(e-st); half=False; got=0; trail=False
    for k in range(j+1,len(d)):
        r=d.iloc[k]
        if k-j>=3:
            w=d.iloc[k-3:k]
            if (w.close.iloc[-1]-e)*dr>0: trail=True
            if trail: st=max(st,w.low.min()) if dr==1 else min(st,w.high.max())
        lo,hi=(r.low,r.high) if dr==1 else (-r.high,-r.low); E=e*dr; S=st*dr
        if lo<=S: return (got+(S-E)*(0.5 if half else 1))/risk
        if not half and hi>=E+risk: half=True; got=0.5*risk; st=max(st,e) if dr==1 else min(st,e)
        if r.t.time()>=T(15,44): return (got+(r.close*dr-E)*(0.5 if half else 1))/risk
    return got/risk
def exit_fixed(d,j,dr,e,st,tgt):
    risk=abs(e-st)
    for k in range(j+1,len(d)):
        r=d.iloc[k]; lo,hi=(r.low,r.high) if dr==1 else (-r.high,-r.low)
        if lo<=st*dr: return -1.0
        if hi>=e*dr+tgt*risk: return tgt
        if r.t.time()>=T(15,44): return (r.close-e)*dr/risk
    return 0
LV={1:['Prior-day low','PM low','OR low (30m)','Equal lows','VWAP','SMA 200','SMA 400','Prior-day high','PM high','OR high (30m)'],
   -1:['Prior-day high','PM high','OR high (30m)','Equal highs','VWAP','SMA 200','SMA 400','Prior-day low','PM low','OR low (30m)']}
rows=[]
for f in sorted(glob.glob('D_*.pkl')):
    tk=f[2:-4]; d=pd.read_pickle(f).reset_index(drop=True); tm=d.t.dt.time
    rth=(tm>=T(9,30))&(tm<T(16,0))
    d['lod']=d.low.where(rth).groupby(d.date).cummin(); d['hod']=d.high.where(rth).groupby(d.date).cummax()
    for j in np.where(rth&(tm>=T(9,36))&(tm<T(15,0)))[0]:
        b=d.iloc[j]; rng=b.high-b.low; a=b.atr
        if rng<0.4*a or j+4>=len(d): continue
        body=abs(b.close-b.open)
        for dr in (1,-1):
            wick=(min(b.open,b.close)-b.low) if dr==1 else (b.high-max(b.open,b.close))
            if wick<0.6*rng or body>0.35*rng: continue
            tip=b.low if dr==1 else b.high
            prev=d.iloc[j-10]; drop=(prev.close-tip)*dr
            if drop<1.0*a: continue                         # it must have moved INTO the level
            lv=[(c,b[c]) for c in LV[dr] if not pd.isna(b[c])]
            p1=d.iloc[j-1]; lod=p1.lod if dr==1 else p1.hod  # earlier day low/high = double bottom/top
            if not pd.isna(lod): lv.append(('Day low/high retest',lod))
            hit=[c for c,L in lv if abs(tip-L)<=0.15*a and (b.close-L)*dr>0]
            if not hit: continue
            # entry: next 1-3 bars break the pin's high (calls) / low (puts)
            trig=b.high if dr==1 else b.low; st=tip-dr*0.05*a
            for k in range(j+1,j+4):
                x=d.iloc[k]
                hitStop=((x.low if dr==1 else x.high)-st)*dr<=0
                if (x.high if dr==1 else x.low)*dr>trig*dr and hitStop:   # same bar reached entry and stop: count as a full loss
                    rows.append(dict(tk=tk,t=b.t,dr=dr,lvl=hit[0],rvol=b.RVOL,s400=np.sign(b.close-b['SMA 400'])*dr,vw=np.sign(b.close-b.VWAP)*dr,
                        lunch=T(12,30)<=b.t.time()<T(14,0),risk_pct=abs(trig-st)/trig*100,R=-1.0,R1=-1.0,R2=-1.0)); break
                if hitStop: break
                if (x.high if dr==1 else x.low)*dr>trig*dr:
                    e=trig; rows.append(dict(tk=tk,t=b.t,dr=dr,lvl=hit[0],rvol=b.RVOL,
                        s400=np.sign(b.close-b['SMA 400'])*dr, vw=np.sign(b.close-b.VWAP)*dr,
                        lunch=T(12,30)<=b.t.time()<T(14,0), risk_pct=abs(e-st)/e*100,
                        R=exit_trail(d,k,dr,e,st), R1=exit_fixed(d,k,dr,e,st,1), R2=exit_fixed(d,k,dr,e,st,2)))
                    break
            break
P=pd.DataFrame(rows); P=P[P.t>='2026-07-27']; P['per']=np.where(P.t>='2026-09-04','late','early'); P.to_pickle('PIN.pkl')
def s(Q): return f"{len(Q):4d} | trail: {(Q.R>0).mean()*100:3.0f}% win {Q.R.sum():6.1f}R | 1R target: {(Q.R1>0).mean()*100:3.0f}% win {Q.R1.sum():6.1f}R | 2R target: {(Q.R2>0).mean()*100:3.0f}% win {Q.R2.sum():6.1f}R"
V={'A all pin bars at a level':P.t.notna(),'B + not lunch':~P.lunch,'C + with 400 SMA trend':~P.lunch&(P.s400>0),
   'D + counter 400 SMA':~P.lunch&(P.s400<0),'E B + RVOL>=1':~P.lunch&(P.rvol>=1),'F B + first hour only':~P.lunch&(P.t.dt.time<T(10,30)),
   'G B + after 10:30':~P.lunch&(P.t.dt.time>=T(10,30))}
for n,k in V.items():
    print('\n==',n)
    for p,lab in [('early','Jul27-Sep3'),('late','Sep4-Oct2 ')]: print(' ',lab,s(P[k&(P.per==p)]))
print('\nmedian stop size % of price:',round(P.risk_pct.median(),3))
print('\nby level (B):'); B=P[~P.lunch]
print(B.groupby(['lvl','per']).agg(n=('R','size'),win=('R1',lambda v:(v>0).mean()),R=('R','sum')).round(2).unstack().to_string())
print('\nby ticker (B, trail R):'); print(B.groupby(['tk','per']).R.sum().unstack().round(1).T.to_string())
