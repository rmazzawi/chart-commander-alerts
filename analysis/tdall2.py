import pandas as pd, numpy as np
A=pd.read_pickle('TDALL.pkl'); A=A[A.index>='2026-07-27']
A['h1_rule']=(A.h1_cross<=1)&(A.h1_ratio>=0.4)
A['combo']=A.m15_strong&A.h1_rule
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def st(X,c):
    n=int(X.trend.sum()); f=X[X[c]]; return f"{int(f.trend.sum())}/{n} caught, {len(f)} flagged, {f.trend.mean()*100 if len(f) else 0:.0f}% right"
rows={tk:{'10:30 rule: first hour 1 side of VWAP + big move':st(A[A.tk==tk],'h1_rule'),'9:45 strong 15m AND 10:30 rule':st(A[A.tk==tk],'combo')} for tk in TK}
S=A[~A.tk.isin(['SPY','SPX','QQQ','IWM'])]
rows['ALL STOCKS']={'10:30 rule: first hour 1 side of VWAP + big move':st(S,'h1_rule'),'9:45 strong 15m AND 10:30 rule':st(S,'combo')}
print(pd.DataFrame(rows).T.to_string())
# direction from first hour on flagged days + ride 10:30 -> close
rows=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time
    for day,g in d.groupby('date'):
        day=pd.Timestamp(day)
        if day not in A[A.tk==tk].index: continue
        r=g[(g.tm>=pd.Timestamp('09:30').time())&(g.tm<pd.Timestamp('16:00').time())]
        o=r.open.iloc[0]; p=r[r.tm<pd.Timestamp('10:30').time()].close.iloc[-1]; c=r.close.iloc[-1]
        rows.append(dict(tk=tk,date=day,rest=(c-p)*np.sign(p-o)/o*100))
R=pd.DataFrame(rows).set_index(['tk','date']); B=A.reset_index().set_index(['tk','date']).join(R)
for nm,m in [('flagged by 10:30 rule',B.h1_rule),('flagged by 9:45+10:30 combo',B.combo),('all other days',~B.h1_rule)]:
    X=B[m & ~B.index.get_level_values(0).isin(['SPY','SPX','QQQ','IWM'])]
    print(f"stocks, {nm:28}: {len(X):3d} days | kept first-hour direction to close {(X.rest>0).mean()*100:3.0f}% | avg 10:30->close {X.rest.mean():+.2f}% | avg win {X.rest[X.rest>0].mean():.2f}% / avg loss {X.rest[X.rest<=0].mean():.2f}%")
