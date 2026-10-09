# Step 4 (10/9): the strategy family rebuilt on 10-min and 30-min candles, regular hours only (NO premarket data).
# Candles built exactly from the 2m data (9:30 anchored). Signals on the candle close; exits checked on the 2m bars after entry.
# Setups (one trade at a time per ticker, max 2 losses/day, no entries 12:30-14:00, entries until 15:00):
#  ORB : close beyond the 30-min opening range, then a pullback that touches the 20 EMA and a candle closing back beyond the 9 EMA (S1 idea)
#  PB  : trend (9>20 EMA, beyond VWAP) -> pullback touches the 20 EMA -> candle closes back beyond the 9 EMA (S5 idea)
#  VW  : close back across VWAP with 9>20 EMA in that direction, after being on the other side (S3 idea)
#  SW  : sweep of the prior-day low/high or opening-range low/high, candle closes back inside (S2 idea; 400-SMA rule not used: no history on 10m)
# Stop: beyond the setup candle / pullback extreme. Exits: T1 = 1R sell half, stop -> breakeven, trail on the previous candle of that timeframe, flat 15:44.
# Costs: round trip 0.02% and 0.04% of the stock price, charged in R.
import pandas as pd, numpy as np, glob
from datetime import time as T
def candles(d,tf):
    x=d[(d.t.dt.time>=T(9,30))&(d.t.dt.time<T(16,0))].copy()
    x['g']=((x.t.dt.hour*60+x.t.dt.minute-570)//tf)
    c=x.groupby(['date','g']).agg(t=('t','first'),i1=('t',lambda s:s.index[-1]),open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),
        vw=('VWAP','last'),pdh=('Prior-day high','first'),pdl=('Prior-day low','first'),vol=('Volume','sum')).reset_index()
    c['e9']=c.close.ewm(span=9,adjust=False).mean(); c['e20']=c.close.ewm(span=20,adjust=False).mean()
    tr=pd.concat([c.high-c.low,(c.high-c.close.shift()).abs(),(c.low-c.close.shift()).abs()],axis=1).max(axis=1); c['atr']=tr.rolling(14).mean()
    c['tend']=c.t+pd.Timedelta(minutes=tf); return c
def exit_on(d,c,k0,dr,e,st,tf):
    risk=abs(e-st); half=False; got=0; i0=c.i1[k0]; day=c.date[k0]; trail=st
    cc=c[(c.date==day)&(c.index>k0)]
    for i in range(i0+1,len(d)):
        r=d.iloc[i]
        if r.date!=day: break
        done=cc[cc.tend<=r.t]                                    # completed candles of this tf
        if half and len(done): trail=max(trail,done.low.iloc[-1]) if dr==1 else min(trail,done.high.iloc[-1])
        stp=trail if half else st
        lo,hi=(r.low,r.high) if dr==1 else (-r.high,-r.low)
        if lo<=stp*dr: return (got+(stp-e)*dr*(0.5 if half else 1))/risk
        if not half and hi>=e*dr+risk: half=True; got=0.5*risk; trail=e
        if r.t.time()>=T(15,44): return (got+(r.close-e)*dr*(0.5 if half else 1))/risk
    return (got+(d.close[i-1]-e)*dr*(0.5 if half else 1))/risk
def run(tf):
    rows=[]
    for f in sorted(glob.glob('D_*.pkl')):
        tk=f[2:-4]; d=pd.read_pickle(f).reset_index(drop=True); c=candles(d,tf)
        for day,g in c.groupby('date'):
            idx=list(g.index); orc=g[g.t.dt.time<T(10,0)]
            if len(orc)==0: continue
            oh,ol=orc.high.max(),orc.low.min(); broke={1:False,-1:False}; pb={1:None,-1:None}; losses=0; busy_until=None
            for k in idx:
                b=c.loc[k]; tm=b.tend.time()
                if b.t.time()<T(10,0) or pd.isna(b.atr): continue
                for dr in (1,-1):
                    if (b.close-(oh if dr==1 else ol))*dr>0: broke[dr]=True
                    if ((b.low if dr==1 else b.high)-b.e20)*dr<=0: pb[dr]=(b.low if dr==1 else b.high) if pb[dr] is None else (min(pb[dr],b.low) if dr==1 else max(pb[dr],b.high))
                if busy_until is not None and b.tend<=busy_until: continue
                if losses>=2 or not(T(10,0)<tm<=T(15,0)) or T(12,30)<tm<=T(14,0): continue
                p=c.loc[k-1] if k-1 in c.index else None
                for dr in (1,-1):
                    sig=None
                    trend=(b.e9-b.e20)*dr>0 and (b.close-b.vw)*dr>0
                    reclaim=(b.close-b.e9)*dr>0 and (b.close-b.open)*dr>0 and pb[dr] is not None
                    if broke[dr] and trend and reclaim: sig=('ORB',pb[dr])
                    elif trend and reclaim: sig=('PB',pb[dr])
                    elif p is not None and p.date==b.date and (p.close-p.vw)*dr<0 and (b.close-b.vw)*dr>0 and (b.e9-b.e20)*dr>0: sig=('VW',b.low if dr==1 else b.high)
                    else:
                        for L in ([b.pdl,ol] if dr==1 else [b.pdh,oh]):
                            if not pd.isna(L) and ((b.low<L<b.close) if dr==1 else (b.high>L>b.close)) and b.t.time()>=T(10,0): sig=('SW',b.low if dr==1 else b.high); break
                    if sig is None: continue
                    st=sig[1]-dr*0.05*b.atr; e=b.close
                    if (e-st)*dr<=0 or abs(e-st)>2.5*b.atr: continue
                    R=exit_on(d,c,k,dr,e,st,tf)
                    rows.append(dict(tf=tf,tk=tk,t=b.tend,dr=dr,s=sig[0],R=R,stp=abs(e-st)/e*100))
                    losses+=R<=0; pb={1:None,-1:None}
                    busy_until=b.tend+pd.Timedelta(minutes=tf*3); break
    P=pd.DataFrame(rows); P=P[P.t>='2026-07-27']; P['per']=np.where(P.t>='2026-09-04','late','early'); return P
def show(P,name):
    print(f'\n##### {name}')
    for p,lab in [('early','good month'),('late','bad month ')]:
        q=P[P.per==p]
        c2=(q.R-0.02/q.stp).sum(); c4=(q.R-0.04/q.stp).sum()
        print(f"  {lab}: {len(q):3d} tr {(q.R>0).mean()*100:3.0f}% wins | before costs {q.R.sum():+6.1f}R | cost 0.02%: {c2:+6.1f}R | cost 0.04%: {c4:+6.1f}R | median stop {q.stp.median():.2f}%")
    g=P.groupby(['s','per']).apply(lambda q:pd.Series({'n':len(q),'win':(q.R>0).mean(),'R_after_0.02':(q.R-0.02/q.stp).sum()})).unstack().round(2)
    print(g.to_string())
    t=P.assign(Rc=P.R-0.02/P.stp).groupby(['tk','per']).Rc.sum().unstack().round(1); print('  by ticker after 0.02% cost:'); print(t.T.to_string()); print('  tickers positive both months:',((t.early>0)&(t.late>0)).sum(),'/',len(t))
if __name__=='__main__':
    import sys
    for tf in [int(a) for a in sys.argv[1:]] or [10,30]:
        P=run(tf); P.to_pickle(f'TF{tf}.pkl'); show(P,f'{tf}-minute version (no premarket)')
