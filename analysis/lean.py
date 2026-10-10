# 10/10 "lean" 2-minute version: same v4 entries, keep only strategies/tickers that make money AFTER costs, wider stop options.
# Honest check: pick the keep-list on one month, then judge it on the OTHER month (out of sample).
import pandas as pd, numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv=[sys.argv[0]]
import importlib.util
spec=importlib.util.spec_from_file_location('se',os.path.join(os.path.dirname(os.path.abspath(__file__)),'stops_exits.py'))
src=open(spec.origin).read().split("risk0=lambda")[0]              # reuse data + run() from stops_exits.py without its prints
exec(src)
risk0=lambda x:abs(x.entry-x.stop)
liq=['SPY','QQQ','AAPL','NVDA','MSFT','AMZN']
rows=[]
for x in A.itertuples():
    d=D[x.tk]
    for nm,m,tr in [('now',1,'2m'),('x2_10m',2,'10m'),('x3_10m',3,'10m')]:
        st=x.entry-x.dir*m*risk0(x); r=run(d,x.i,x.dir,x.entry,st,tr)
        c=lambda C: r-C/(abs(x.entry-st)/x.entry*100)
        rows.append(dict(tk=x.tk,s=x.s,per=x.per,v=nm,R=r,R2=c(0.02),R4=c(0.04)))
P=pd.DataFrame(rows); P.to_pickle('LEAN.pkl')
P['Rc']=np.where(P.tk.isin(liq),P.R2,P.R4)                     # liquid names 0.02% cost, others 0.04%
print('R AFTER COSTS (liquid tickers 0.02%, others 0.04%)')
print('\nby strategy:'); print(P.pivot_table(index=['v','s'],columns='per',values='Rc',aggfunc='sum').round(1).to_string())
print('\nby ticker:'); print(P.pivot_table(index=['v','tk'],columns='per',values='Rc',aggfunc='sum').round(1).unstack(0).to_string())
def s(q): return f"{len(q):3d} tr {(q.R>0).mean()*100:3.0f}% {q.Rc.sum():+6.1f}R"
print('\nLEAN CANDIDATES (after costs)')
for v in ['now','x2_10m','x3_10m']:
    Q=P[P.v==v]
    for name,k in [('all',Q.tk.notna()),('liquid 6 only',Q.tk.isin(liq)),('S2+S6 only',Q.s.isin([2,6])),('liquid 6 + S2+S6',Q.tk.isin(liq)&Q.s.isin([2,6]))]:
        print(f"  {v:7s} {name:18s} | good: {s(Q[k&(Q.per=='early')])} | bad: {s(Q[k&(Q.per=='late')])}")
print('\nOUT-OF-SAMPLE: keep the (ticker,strategy) pairs that were positive in one month, judge them in the other month')
for v in ['now','x2_10m','x3_10m']:
    Q=P[P.v==v]; out=[]
    for a,b in [('early','late'),('late','early')]:
        g=Q[Q.per==a].groupby(['tk','s']).Rc.sum(); keep=set(g[g>0].index)
        q=Q[(Q.per==b)&Q.apply(lambda r:(r.tk,r.s) in keep,axis=1)]; out.append(f"picked on {a}, tested on {b}: {s(q)}")
    print(f"  {v:7s} | "+" | ".join(out))
