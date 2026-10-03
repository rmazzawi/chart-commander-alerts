import pandas as pd, numpy as np
from datetime import time as T
from orb15 import exit_sim
TK=['SPY','QQQ','IWM','AAPL','MSFT','NVDA','AMZN','META','TSLA','AMD','GLD','SPX']
D={tk:pd.read_pickle(f'D_{tk}.pkl').reset_index(drop=True) for tk in TK}
def res(d,m):
    r=d[(d.t.dt.time>=T(9,30))&(d.t.dt.time<T(16,0))].set_index('t')
    o=r.resample(f'{m}min',origin='start_day',offset='30min').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
    tr=np.maximum(o.high-o.low,np.maximum(abs(o.high-o.close.shift()),abs(o.low-o.close.shift())))
    o['atr']=tr.ewm(alpha=1/14,adjust=False).mean(); o['date']=o.index.date; o['tend']=o.index+pd.Timedelta(f'{m}min')
    return o
def run(m,minleg,until=T(11,30)):
    rows=[]
    for tk,d in D.items():
        o=res(d,m) if m>2 else d[(d.t.dt.time>=T(9,30))&(d.t.dt.time<T(16,0))].set_index('t').assign(tend=lambda x:x.index+pd.Timedelta('2min'))
        for day,g in o.groupby('date'):
            g=g[g.index.time<until]
            if len(g)<4: continue
            f=g.iloc[0]; dr=1 if f.close>=f.open else -1
            start=f.low if dr==1 else f.high; ext=f.high if dr==1 else f.low; k=1
            while k<len(g) and (g.close.iloc[k]-g.open.iloc[k])*dr>=0:
                ext=max(ext,g.high.iloc[k]) if dr==1 else min(ext,g.low.iloc[k]); k+=1
            leg=abs(ext-start)
            if k>=len(g) or leg<minleg*f.atr: continue
            f50=ext-dr*0.5*leg; f786=ext-dr*0.786*leg; touched=False
            for j in range(k,len(g)):
                c=g.iloc[j]
                if (c.low<f786) if dr==1 else (c.high>f786): break
                if (c.low<=f50) if dr==1 else (c.high>=f50): touched=True
                p=g.iloc[j-1]
                if touched and (c.close-c.open)*dr>0 and ((c.close>p.high) if dr==1 else (c.close<p.low)):
                    st=f786-dr*0.1*c.atr
                    ii=d.t.searchsorted(c.tend)-1   # last 2m bar of the entry candle
                    a2=d.atr.iloc[ii]
                    if abs(c.close-st)<=3*a2: rows.append(dict(tk=tk,t=c.tend,R=exit_sim(d,ii,dr,c.close,st)))
                    break
    F=pd.DataFrame(rows)
    if len(F)==0: return None
    F=F[F.t>='2026-07-27']; F['per']=np.where(F.t>='2026-09-04','late','early'); return F
def s(P): return f"{len(P):3d} trades {(P.R>0).mean()*100:3.0f}% {P.R.sum():6.1f}R ({P.R.mean():+.2f}/trade)" if len(P) else '  0 trades'
print('Your exact definition: first candle -> first reversing candle = the move; pullback to 0.5-0.618; continuation candle closes past prior candle; stop beyond 0.786; entries until 11:30; script-style exits')
for m in [2,5,10,15]:
    for ml in [0,0.5]:
        F=run(m,ml)
        if F is None: print(f'{m:2d}m minleg {ml}: none'); continue
        print(f"{m:2d}m  move>={ml} ATR | Jul27-Sep3: {s(F[F.per=='early'])} | Sep4-Oct2: {s(F[F.per=='late'])} | tickers +: {(F.groupby('tk').R.sum()>0).sum()}/{F.tk.nunique()}")
