import pandas as pd, numpy as np
from datetime import time as T
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def bars(d,m):
    x=d.set_index('t')
    b=x.resample(f'{m}min',origin='start_day').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
    for n in [5,12,34,50]: b[f'e{n}']=b.close.ewm(span=n,adjust=False).mean()
    b['tm']=b.index.time; b['date']=b.index.date; return b
def run(b,setup,bias10=None,exitm='fast'):
    o=b.open.values;h=b.high.values;l=b.low.values;c=b.close.values;e5=b.e5.values;e12=b.e12.values;e34=b.e34.values;e50=b.e50.values;tm=b.tm.values;dt=b.date.values
    trades=[];pos=0
    for i in range(2,len(b)):
        t=tm[i]
        if pos:
            d,e,st,i0=pos
            ex=None
            if (l[i]<=st if d==1 else h[i]>=st): ex=st
            elif exitm=='slow' and (c[i]<min(e34[i],e50[i]) if d==1 else c[i]>max(e34[i],e50[i])): ex=c[i]
            elif exitm=='fast' and (c[i]<min(e5[i],e12[i]) if d==1 else c[i]>max(e5[i],e12[i])): ex=c[i]
            elif exitm=='2R' and (h[i]>=e+2*abs(e-st) if d==1 else l[i]<=e-2*abs(e-st)): ex=e+2*abs(e-st)*d
            elif t>=T(15,40) or dt[i]!=dt[i0]: ex=c[i]
            if ex is not None: trades.append(dict(date=dt[i0],time=tm[i0],dir=d,pct=(ex-e)*d/e*100,R=(ex-e)*d/abs(e-st))); pos=0
            continue
        if not (T(9,45)<=t<T(15,0)): continue
        up=c[i]>max(e34[i],e50[i]) and e34[i]>e50[i]; dn=c[i]<min(e34[i],e50[i]) and e34[i]<e50[i]
        if bias10 is not None:
            bb=bias10.asof(b.index[i]) if len(bias10) else 0
            up=up and bb==1; dn=dn and bb==-1
        for d,ok in [(1,up),(-1,dn)]:
            if not ok: continue
            hi5,lo5=max(e5[i],e12[i]),min(e5[i],e12[i])
            if setup=='A': sig=(e5[i]-e12[i])*d>0 and (e5[i-1]-e12[i-1])*d<=0
            elif setup=='B': sig=(e5[i]-e12[i])*d>0 and ((l[i]<=hi5 and c[i]>hi5) if d==1 else (h[i]>=lo5 and c[i]<lo5)) and (c[i]-o[i])*d>0
            else:
                t34,b34=max(e34[i],e50[i]),min(e34[i],e50[i])
                sig=((l[i]<=t34 and c[i]>t34) if d==1 else (h[i]>=b34 and c[i]<b34)) and (c[i]-o[i])*d>0
            if sig:
                st=min(l[i-2:i+1]) if d==1 else max(h[i-2:i+1])
                if abs(c[i]-st)>0: pos=(d,c[i],st,i)
                break
    return trades
rows=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d=d[d.t>='2026-07-20']
    b10=bars(d,10); bias=pd.Series(np.where((b10.close>b10[['e34','e50']].max(axis=1))&(b10.e34>b10.e50),1,np.where((b10.close<b10[['e34','e50']].min(axis=1))&(b10.e34<b10.e50),-1,0)),index=b10.index+pd.Timedelta('10min'))
    for m in [5,10]:
        b=bars(d,m)
        for s,name in [('A','5/12 flip with 34/50 trend'),('B','pullback holds 5/12 cloud'),('C','bounce off 34/50 cloud')]:
            for ex in ['slow','2R']:
                for r in run(b,s,None,ex): rows.append(dict(tk=tk,tf=f'{m}m exit:{ex}',setup=name,**r))
                if m==5:
                    for r in run(b,s,bias,ex): rows.append(dict(tk=tk,tf=f'5m+10mbias exit:{ex}',setup=name,**r))
R=pd.DataFrame(rows); R=R[pd.to_datetime(R.date)>=pd.Timestamp('2026-07-27')]; R['per']=np.where(pd.to_datetime(R.date)>=pd.Timestamp('2026-09-04'),'late','early')
def s(X): return f"{len(X):4d}  {(X.pct>0).mean()*100:3.0f}%  {X.R.sum():+7.1f}R  {X.pct.mean():+.3f}%/trade  win {X.pct[X.pct>0].mean():.2f}% loss {X.pct[X.pct<=0].mean():.2f}%"
print(f"{'setup':32}{'TF':22}| Jul27-Sep3 (n win% R avg)                                 | Sep4-Oct2")
for (st,tf),g in R.groupby(['setup','tf']):
    print(f"{st:32}{tf:22}| {s(g[g.per=='early'])} | {s(g[g.per=='late'])}")
R.to_pickle('RIP.pkl')
