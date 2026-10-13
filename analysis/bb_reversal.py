# 10/13: "catch the turns" - Bollinger Band reversal test on the user's 5m exports (9 tickers, May-Oct 8) and 2m data.
# Setup (short; long is the mirror): a candle pokes ABOVE the upper Bollinger Band (20,2), then a candle closes back INSIDE
# the band and red. Entry when price breaks that candle's low within the next 2 candles. Stop above the highest high of the last
# 3 candles + 0.1 ATR. Target: (a) middle band (20 MA) if it is >= 1.5x risk away, else skip; (b) fixed 2R.
# Regular hours only (entries 9:35-15:30, flat 15:55). Costs: 0.02% round trip on top.
import pandas as pd, numpy as np, glob, re, sys
from datetime import time as T
def run(d,mode):
    d=d.reset_index(drop=True); c=d.close; m=c.rolling(20).mean(); sd=c.rolling(20).std(); u=m+2*sd; l=m-2*sd
    tr=pd.concat([d.high-d.low,(d.high-c.shift()).abs(),(d.low-c.shift()).abs()],axis=1).max(axis=1); atr=tr.rolling(14).mean()
    tm=d.t.dt.time; out=[]; i=21; n=len(d)
    while i<n-3:
        if not (T(9,35)<=tm[i]<=T(15,30)): i+=1; continue
        for dr in (-1,1):
            poke = d.high[i-1]>u[i-1] if dr==-1 else d.low[i-1]<l[i-1]
            back = (c[i]<u[i] and c[i]<d.open[i]) if dr==-1 else (c[i]>l[i] and c[i]>d.open[i])
            if not(poke and back): continue
            trig=d.low[i] if dr==-1 else d.high[i]
            ext=d.high[i-2:i+1].max() if dr==-1 else d.low[i-2:i+1].min(); st=ext-dr*0.1*atr[i]
            for k in range(i+1,min(i+3,n)):
                if d.t[k].date()!=d.t[i].date(): break
                if (dr==-1 and d.low[k]<trig) or (dr==1 and d.high[k]>trig):
                    e=trig; risk=abs(st-e)
                    if risk<=0: break
                    tg=m[k] if mode=='mid' else e+dr*2*risk
                    if mode=='mid' and (tg-e)*dr<1.5*risk: break
                    res=None
                    for j in range(k,n):
                        if d.t[j].date()!=d.t[k].date() or d.t[j].time()>=T(15,55): res=(d.close[j-1 if d.t[j].date()!=d.t[k].date() else j]-e)*dr; break
                        if (dr==-1 and d.high[j]>=st) or (dr==1 and d.low[j]<=st): res=-risk; break
                        if j>k and ((dr==-1 and d.low[j]<=tg) or (dr==1 and d.high[j]>=tg)): res=abs(tg-e); break
                    if res is None: res=(d.close[n-1]-e)*dr
                    out.append(dict(t=d.t[i],dr=dr,R=res/risk,Rc=res/risk-0.02/(risk/e*100)))
                    i=k; break
            break
        i+=1
    return pd.DataFrame(out)
rows=[]
for f in sorted(glob.glob(sys.argv[1])):
    mm=re.search(r'_([A-Z]+)_(\d+)_',f)
    if not mm: continue
    tk=mm.group(1)
    if any(r['tk']==tk for r in rows): continue
    d=pd.read_csv(f,usecols=['time','open','high','low','close']); d['t']=pd.to_datetime(d.time,unit='s',utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
    d=d[(d.t.dt.time>=T(9,30))&(d.t.dt.time<T(16,0))]
    for mode in ['mid','2R']:
        P=run(d,mode)
        if len(P): rows.append(dict(tk=tk,mode=mode,n=len(P),win=(P.R>0).mean(),R=P.R.sum(),Rc=P.Rc.sum(),per=P.R.mean()))
S=pd.DataFrame(rows)
for mode,g in S.groupby('mode'):
    print(f"\n== target: {'middle band (min 1.5R)' if mode=='mid' else 'fixed 2R'}")
    print(g[['tk','n','win','R','Rc','per']].round(2).to_string(index=False))
    print(f"  ALL: {g.n.sum()} trades, win {np.average(g.win,weights=g.n)*100:.0f}%, {g.R.sum():+.1f}R before costs, {g.Rc.sum():+.1f}R after costs")
