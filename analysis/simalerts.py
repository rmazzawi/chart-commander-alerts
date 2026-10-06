import pandas as pd, numpy as np
from datetime import time as T
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def ang(rise,n,u): adj=n*u; h=np.hypot(adj,rise); return np.degrees(np.arccos(adj/h)) if h>0 else 0
cnt=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time; d['mins']=d.t.dt.hour*60+d.t.dt.minute
    r_all=d[(d.mins>=570)&(d.mins<960)]
    dly=r_all.groupby('date').agg(O=('open','first'),H=('high','max'),L=('low','min'),C=('close','last'),u=('high',lambda s:0))
    dly['u']=r_all.assign(br=r_all.high-r_all.low).groupby('date').br.mean(); dly['rng']=dly.H-dly.L
    unit=dly.u.shift().rolling(5,min_periods=3).mean(); avgr=dly.rng.shift().rolling(5,min_periods=3).mean()
    H5=dly.H.rolling(5).max().shift(); L5=dly.L.rolling(5).min().shift()
    days=list(dly.index)
    for i,day in enumerate(days):
        if pd.Timestamp(day)<pd.Timestamp('2026-07-27') or pd.isna(unit[day]): continue
        r=r_all[r_all.date==day].reset_index(drop=True); u=unit[day]; y=dly.iloc[i-1]; o=r.open[0]; msgs=[]
        f=r[r.mins<=584]; loc=(f.close.iloc[-1]-f.low.min())/(f.high.max()-f.low.min())
        msgs.append('15m POSSIBLE' if (loc>=.8 or loc<=.2) else '15m UNLIKELY')
        m=r[r.mins<=628]; up=m.close.iloc[-1]>=o; tb=m.high.idxmax() if up else m.low.idxmin(); tip=r.high[tb] if up else r.low[tb]
        a=ang(abs(tip-o),tb+1,u); late=tb>=22; lvl=0
        if late and a>=30: msgs.append('10:30 LIKELY'); lvl=2
        elif late and a>=20: msgs.append('10:30 POSSIBLE'); lvl=1
        elif a>=20: msgs.append('EARLY SPIKE')
        v15=r.Volume[r.mins<600].mean(); hi=r.high.cummax(); lo=r.low.cummin(); v6=r.Volume.rolling(6).mean()
        levels=[y.H,y.L,r['PM high'][0],r['PM low'][0],H5[day],L5[day]]
        for k in range(len(r)):
            if r.mins[k]<590 or r.mins[k]>=900: continue
            dl=1 if r.close[k]>=o else -1; tl=hi[k] if dl==1 else lo[k]; isnew=(r.high[k]>=hi[k]) if dl==1 else (r.low[k]<=lo[k])
            lv=levels+[r['SMA 200'][k],r['SMA 400'][k]]; tol=max(2*u,0.0015*tl)
            if isnew and ang(abs(tl-o),k+1,u)>=20 and v6[k]>=0.75*v15 and any(pd.notna(x) and abs(tl-x)<=tol for x in lv): msgs.append('EXHAUSTION'); break
        cnt.append(dict(tk=tk,date=day,**{m:1 for m in msgs}))
C=pd.DataFrame(cnt).fillna(0); cols=[c for c in ['15m POSSIBLE','15m UNLIKELY','10:30 LIKELY','10:30 POSSIBLE','EARLY SPIKE','EXHAUSTION'] if c in C]
print('alerts per ticker per day (avg) across',len(C),'ticker-days:'); print((C[cols].mean()).round(2).to_string())
print('\ntotal per day across all 12 tickers:'); print((C.groupby('date')[cols].sum().mean()).round(1).to_string())
