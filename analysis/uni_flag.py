# Python copy of uni_flag/uni_flag_simple.pine, run on candles built from the user's 5-minute exports (9 tickers, ~May-Oct 8)
# and from the 2-minute data (12 tickers, Jul 27-Oct 2). Regular hours candles anchored at 9:30.
# Signal on candle close -> market entry at next candle open (TradingView default). Stop/target checked inside the candle,
# break-even after 1R, 8-EMA close exit at next open. Entries 9:45-15:30.
# Two exit modes: 'hold' = may hold overnight (what TradingView's backtest does), 'flat' = forced exit at 15:55 (0DTE options can't be held).
# Returns in % of price per trade; costs: 0.02% per side (strategy's own commission) and an extra 0.02% round trip for options spread.
import pandas as pd, numpy as np, glob, re, sys
from datetime import time as T
def bars(d,tf):
    x=d[(d.t.dt.time>=T(9,30))&(d.t.dt.time<T(16,0))].copy(); x['g']=(x.t.dt.hour*60+x.t.dt.minute-570)//tf
    return x.groupby([x.t.dt.date,'g']).agg(t=('t','first'),open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last')).reset_index(drop=True)
def sim(b,tf,mode):
    c=b.close; e8=c.ewm(span=8,adjust=False).mean(); s20=c.rolling(20).mean()
    tr=pd.concat([b.high-b.low,(b.high-c.shift()).abs(),(b.low-c.shift()).abs()],axis=1).max(axis=1); atr=tr.ewm(alpha=1/14,adjust=False).mean()
    hb=b.high.rolling(15).apply(lambda a:14-a.argmax(),raw=True); lb=b.low.rolling(15).apply(lambda a:14-a.argmin(),raw=True)
    pl=b.low.rolling(5).min(); ph=b.high.rolling(5).max()
    bull=(hb>=2)&(hb<=5)&(pl>s20-0.25*atr)&(e8>s20)&(s20>s20.shift(3)); bear=(lb>=2)&(lb<=5)&(ph<s20+0.25*atr)&(e8<s20)&(s20<s20.shift(3))
    tm=b.t.dt.time; ins=(tm>=T(9,45))&(tm<=T(15,30))
    L=ins&bull.shift(1,fill_value=False)&(b.high>b.high.shift())&(c>e8); S=ins&bear.shift(1,fill_value=False)&(b.low<b.low.shift())&(c<e8)
    out=[]; pos=0; i=0; n=len(b)
    while i<n-1:
        if pos==0:
            if L[i] or S[i]:
                dr=1 if L[i] else -1; ep=c[i]; st=(pl[i]-0.1*atr[i]) if dr==1 else (ph[i]+0.1*atr[i]); tg=ep+dr*2*(ep-st)*dr*dr
                tg=ep+2*(ep-st) if dr==1 else ep-2*(st-ep)
                fill=b.open[i+1]; risk=abs(ep-st); pos=dr; j=i+1
                while j<n:
                    lo,hi=b.low[j],b.high[j]; px=None
                    if dr==1:
                        if lo<=st: px=min(st,b.open[j])
                        elif hi>=tg: px=max(tg,b.open[j])
                    else:
                        if hi>=st: px=max(st,b.open[j])
                        elif lo<=tg: px=min(tg,b.open[j])
                    if px is None and mode=='flat' and (j+1>=n or b.t[j+1].date()!=b.t[j].date()): px=c[j]
                    if px is None and j>i+1 and ((c[j]<e8[j]) if dr==1 else (c[j]>e8[j])):
                        px=b.open[j+1] if j+1<n else c[j]
                        if mode=='flat' and (j+1>=n or b.t[j+1].date()!=b.t[j].date()): px=c[j]
                    if px is not None:
                        out.append(dict(t=b.t[i],dr=dr,ret=(px-fill)/fill*100*dr,risk=risk/fill*100)); break
                    if ((hi>=ep+risk) if dr==1 else (lo<=ep-risk)) and (st-ep)*dr<0: st=ep
                    j+=1
                pos=0; i=j
                continue
        i+=1
    return pd.DataFrame(out)
def summary(R,cost):
    r=R.ret-cost
    if len(r)==0: return "  0 tr"
    pf=r[r>0].sum()/max(1e-9,-r[r<0].sum())
    return f"{len(r):4d} tr {(r>0).mean()*100:3.0f}% PF {pf:4.2f} total {r.sum():+6.1f}%"
if __name__=='__main__':
    src=sys.argv[1]; files={}
    for f in sorted(glob.glob(src)):
        m=re.search(r'_([A-Z]+)_(\d+)_',f); 
        if m and m.group(1) not in files: files[m.group(1)]=f
    tfs=[int(a) for a in sys.argv[2].split(',')]
    allr=[]
    for tk,f in files.items():
        d=pd.read_csv(f,usecols=['time','open','high','low','close'])
        d['t']=pd.to_datetime(d.time,unit='s',utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None) if pd.api.types.is_numeric_dtype(d.time) else pd.to_datetime(d.time.str[:19])
        for tf in tfs:
            b=bars(d,tf)
            for mode in ['hold','flat']:
                R=sim(b,tf,mode)
                if len(R): R['tk']=tk; R['tf']=tf; R['mode']=mode; allr.append(R)
    A=pd.concat(allr); A.to_pickle('UNI.pkl')
    for tf in tfs:
        for mode in ['hold','flat']:
            Q=A[(A.tf==tf)&(A['mode']==mode)]
            print(f"\n=== {tf}-min, {'may hold overnight (like TradingView)' if mode=='hold' else 'flat by 15:55 (0DTE reality)'}")
            print(f"  ALL   stock cost 0.04%: {summary(Q,0.04)} | + option spread 0.06%: {summary(Q,0.06)}")
            for tk,q in Q.groupby('tk'): print(f"  {tk:5s} stock cost 0.04%: {summary(q,0.04)} | + option spread 0.06%: {summary(q,0.06)}")
