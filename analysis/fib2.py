import pandas as pd, numpy as np
from datetime import time as T
TK=['SPY','QQQ','IWM','AAPL','MSFT','NVDA','AMZN','META','TSLA','AMD','GLD','SPX']
D={tk:pd.read_pickle(f'D_{tk}.pkl').reset_index(drop=True) for tk in TK}
def exit2(d,j,dr,e,st,t1=None):
    """script-like: half at T1 (default 1R) -> stop to BE; trail on last 3 bars once in profit; flat 15:44. returns (R, exit index)"""
    risk=abs(e-st); half=False; got=0; trail=False; t1=e+dr*risk if t1 is None else t1
    H=d.high.values;L=d.low.values;C=d.close.values;tm=d.t.dt.time.values
    for k in range(j+1,len(d)):
        if k-j>=3:
            if (C[k-1]-e)*dr>0: trail=True
            if trail: st=max(st,L[k-3:k].min()) if dr==1 else min(st,H[k-3:k].max())
        hi=H[k] if dr==1 else -L[k]; lo=L[k] if dr==1 else -H[k]; E=e*dr; S=st*dr
        if lo<=S: return (got+(S-E)*(0.5 if half else 1))/risk,k
        if not half and hi>=t1*dr: half=True; got=0.5*(t1*dr-E); st=max(st,e) if dr==1 else min(st,e)
        if tm[k]>=T(15,44): return (got+(C[k]*dr-E)*(0.5 if half else 1))/risk,k
    return got/risk,len(d)-1
def bars(d,m):
    r=d[(d.t.dt.time>=T(9,30))&(d.t.dt.time<T(16,0))].set_index('t')
    if m==2: o=r[['open','high','low','close','VWAP','EMA 9','EMA 20']].copy()
    else:
        o=r.resample(f'{m}min',origin='start_day',offset='30min').agg({'open':'first','high':'max','low':'min','close':'last','VWAP':'last'}).dropna()
        o['EMA 9']=o.close.ewm(span=9,adjust=False).mean(); o['EMA 20']=o.close.ewm(span=20,adjust=False).mean()
    tr=np.maximum(o.high-o.low,np.maximum(abs(o.high-o.close.shift()),abs(o.low-o.close.shift())))
    o['atr']=tr.ewm(alpha=1/14,adjust=False).mean(); o['date']=o.index.date; o['tend']=o.index+pd.Timedelta(f'{m}min'); return o
def run(m,n=3,mv=1.0,flt='none',ex='1R',zone=(0.382,0.618),maxwait=15):
    rows=[]
    for tk,d in D.items():
        o=bars(d,m); tend=d.t.values
        for day,g in o.groupby('date'):
            O=g.open.values;H=g.high.values;L=g.low.values;C=g.close.values;A=g.atr.values;V=g.VWAP.values;E9=g['EMA 9'].values;E20=g['EMA 20'].values
            tt=g.index.time; te=g.tend.values; busy_until=None; j=n
            while j<len(g):
                if tt[j]>=T(15,30): break
                if busy_until is not None and te[j]<=busy_until: j+=1; continue
                win=slice(j-n+1,j+1); up=(C[win]>O[win]).all(); dn=(C[win]<O[win]).all()
                if not(up or dn) or abs(C[j]-O[j-n+1])<mv*A[j]: j+=1; continue
                dr=1 if up else -1
                lo0=j-n+1; back=max(0,lo0-5)
                start=L[back:j+1].min() if dr==1 else H[back:j+1].max(); ext=H[j] if dr==1 else L[j]
                touched=False; k=j+1; done=False
                while k<len(g) and k-j<=maxwait and tt[k]<T(15,30):
                    if not touched and ((H[k]>ext) if dr==1 else (L[k]<ext)): ext=H[k] if dr==1 else L[k]
                    leg=abs(ext-start); z1=ext-dr*zone[0]*leg; f786=ext-dr*0.786*leg
                    if (L[k]<f786) if dr==1 else (H[k]>f786): break
                    if (L[k]<=z1) if dr==1 else (H[k]>=z1): touched=True
                    if touched and (C[k]-O[k])*dr>0 and ((C[k]>H[k-1]) if dr==1 else (C[k]<L[k-1])):
                        ok = flt=='none' or (flt=='vwap' and (C[k]-V[k])*dr>0) or (flt=='ema' and (E9[k]-E20[k])*dr>0 and (C[k]-V[k])*dr>0)
                        st=f786-dr*0.1*A[k]
                        if ok and abs(C[k]-st)<=2.5*A[k]:
                            ii=np.searchsorted(tend,te[k])-1
                            R,xk=exit2(d,ii,dr,C[k],st, ext if ex=='swing' else None)
                            rows.append(dict(tk=tk,t=pd.Timestamp(te[k]),R=R,mins=tt[k].hour*60+tt[k].minute)); busy_until=d.t.values[xk]; done=True
                        break
                    k+=1
                j = k+1 if done else j+1
    F=pd.DataFrame(rows); F=F[F.t>='2026-07-27']; F['per']=np.where(F.t>='2026-09-04','late','early'); return F
def s(P): return f"{len(P):4d} {(P.R>0).mean()*100:3.0f}% {P.R.sum():6.1f}R" if len(P) else '   0'
if __name__=='__main__':
    print(f"{'TF':3} {'filter':5} {'exit':6} | {'Jul27-Sep3':>17} | {'Sep4-Oct2':>17} | tickers+")
    out=[]
    for m in [2,5]:
        for flt in ['none','vwap','ema']:
            for ex in ['1R','swing']:
                F=run(m,flt=flt,ex=ex)
                print(f"{m:2d}m {flt:5} {ex:6} | {s(F[F.per=='early'])} | {s(F[F.per=='late'])} | {(F.groupby('tk').R.sum()>0).sum()}/12", flush=True)
