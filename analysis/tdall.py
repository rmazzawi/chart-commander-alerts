import pandas as pd, numpy as np
from datetime import time as T
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def days(tk):
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time; rows=[]
    for day,g in d.groupby('date'):
        r=g[(g.tm>=T(9,30))&(g.tm<T(16,0))]
        if len(r)<150: continue
        o,c,h,l=r.open.iloc[0],r.close.iloc[-1],r.high.max(),r.low.min()
        m=r[r.tm<T(9,45)]; m15c=(m.close.iloc[-1]-m.low.min())/max(m.high.max()-m.low.min(),1e-9)
        h1=r[r.tm<T(10,30)]; side=np.sign(h1.close-h1.VWAP)
        rows.append(dict(date=pd.Timestamp(day),o=o,c=c,rng=h-l,net=c-o,m15_clo=m15c,m15_up=m.close.iloc[-1]>m.open.iloc[0],
            h1_cross=int((side!=side.shift()).iloc[1:].sum()),h1_move=abs(h1.close.iloc[-1]-o)))
    D=pd.DataFrame(rows).set_index('date')
    D['rng%']=D.rng/D.o*100; D['avg']=D['rng%'].shift().rolling(10,min_periods=5).mean()
    D['eff']=D.net.abs()/D.rng; D['trend']=(D.eff>=0.6)&(D['rng%']>=D.avg*1.2)
    D['y_chop']=(D.eff.shift()<0.35); D['m15_strong']=(D.m15_clo>=0.8)|(D.m15_clo<=0.2)
    D['h1_ratio']=(D.h1_move/D.o*100)/D.avg; D['tk']=tk
    return D.dropna(subset=['avg'])
A=pd.concat([days(t) for t in TK]); A.to_pickle('TDALL.pkl')
spy=A[A.tk=='SPX'][['trend']].rename(columns={'trend':'spx_trend'})
A=A.join(spy,how='left'); A=A[A.index>='2026-07-27']   # common window for all tickers
def stats(X):
    n=int(X.trend.sum()); s=X[X.m15_strong]; m=X[~X.m15_strong]; c=X[X.m15_strong&X.y_chop]
    dirok=(np.sign(s[s.trend].net)==np.where(s[s.trend].m15_clo>=0.5,1,-1)).mean() if len(s[s.trend]) else np.nan
    return dict(days=len(X),trend_days=n,per_month=round(n/len(X)*21,1),
        caught_by_15m=f"{int(s.trend.sum())}/{n}", trend_if_15m_strong=f"{s.trend.mean()*100:.0f}%", trend_if_15m_middle=f"{m.trend.mean()*100:.0f}%",
        trend_if_strong_and_ychop=f"{c.trend.mean()*100:.0f}% (n={len(c)})", direction_matches_15m=f"{dirok*100:.0f}%")
out=pd.DataFrame({tk:stats(A[A.tk==tk]) for tk in TK}).T
out.loc['ALL STOCKS (excl SPY/SPX/QQQ/IWM)']=stats(A[~A.tk.isin(['SPY','SPX','QQQ','IWM'])])
print(out.to_string())
S=A[~A.tk.isin(['SPY','SPX'])]
print('\nStock trend day on the SAME day as an SPX trend day:',f"{S[S.trend].spx_trend.mean()*100:.0f}% of stock trend days",'| chance a stock trends when SPX trends:',f"{S[S.spx_trend==True].trend.mean()*100:.0f}%",'vs other days',f"{S[S.spx_trend==False].trend.mean()*100:.0f}%")
print('\nTSLA trend days:'); t=A[(A.tk=='TSLA')&A.trend]; print(t[['net','rng%','avg','eff','m15_clo','y_chop','h1_cross','spx_trend']].round(2).to_string())
