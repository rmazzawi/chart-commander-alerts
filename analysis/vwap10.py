import pandas as pd, numpy as np
from datetime import time as T
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def bars10(d, ext):
    x=d.copy(); x['tm']=x.t.dt.time
    if not ext: x=x[(x.tm>=T(9,30))&(x.tm<T(16,0))]
    else: x=x[(x.tm>=T(4,0))&(x.tm<T(16,0))]
    x=x.set_index('t')
    b=x.resample('10min',origin='start_day',offset='0min').agg({'open':'first','high':'max','low':'min','close':'last','Volume':'sum'}).dropna()
    b['date']=b.index.date; b['tm']=b.index.time
    tp=(b.high+b.low+b.close)/3; b['pv']=tp*b.Volume
    b['vwap']=b.groupby('date').pv.cumsum()/b.groupby('date').Volume.cumsum().replace(0,np.nan)   # session VWAP (4:00 if ext, 9:30 if not)
    b['e5']=b.close.ewm(span=5,adjust=False).mean(); b['e9']=b.close.ewm(span=9,adjust=False).mean()
    tr=np.maximum(b.high-b.low,np.maximum(abs(b.high-b.close.shift()),abs(b.low-b.close.shift()))); b['atr']=tr.ewm(alpha=1/14,adjust=False).mean()
    return b
def fwd(r,k,dr,o):
    c=r.close.values; out={}
    for lab,n in [('30m',3),('60m',6)]: out[lab]=(c[min(k+n,len(c)-1)]-c[k])*dr/o*100
    out['close']=(c[-1]-c[k])*dr/o*100; return out
A=[];B=[];base=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d=d[d.t>='2026-07-27']
    for ext,store in [(True,A),(False,B)]:
        b=bars10(d,ext)
        for day,g in b.groupby('date'):
            r=g[(g.tm>=T(9,30))&(g.tm<T(16,0))].reset_index()
            if len(r)<36: continue
            o=r.open.iloc[0]; side=np.sign(r.e9-r.vwap)
            if ext:
                # A: EMAs 5&9 stayed on one side of VWAP 9:30 -> 10:20 (bars 0..5)
                s0=side[:6]; s5=np.sign(r.e5-r.vwap)[:6]
                if not ((s0==s0.iloc[0]).all() and (s5==s0.iloc[0]).all() and s0.iloc[0]!=0): continue
                tr=s0.iloc[0]
                for k in range(6,len(r)-1):
                    if r.tm[k]>=T(15,0): break
                    touch = (r.low[k]<=r.vwap[k]) if tr==1 else (r.high[k]>=r.vwap[k])
                    turn = (r.e5[k]-r.e5[k-1])*tr<0 and (r.e9[k]-r.e9[k-1])*tr<0
                    if touch and turn:
                        A.append(dict(tk=tk,date=day,time=r.tm[k],trend=tr,**{f'trend_dir_{a}':v for a,v in fwd(r,k,tr,o).items()})); break
            else:
                # B: EMA9 comes to VWAP (within 0.15 ATR) without crossing, then turns away
                for k in range(3,len(r)-1):
                    if r.tm[k]>=T(15,0): break
                    if side[k]!=side[k-1] and side[k-1]!=0 and side[k]!=0: base.append(dict(**{f'cross_{a}':v for a,v in fwd(r,k,side[k],o).items()}))
                    s=side[k-2]
                    if s==0 or side[k-1]!=s or side[k]!=s: continue
                    near=abs(r.e9[k]-r.vwap[k])<=0.15*r.atr[k]; turned=(r.e9[k]-r.e9[k-1])*s>0 and (r.e9[k-1]-r.e9[k-2])*s<0
                    if near and turned: B.append(dict(tk=tk,date=day,time=r.tm[k],side=s,**{f'bounce_{a}':v for a,v in fwd(r,k,s,o).items()}))
A=pd.DataFrame(A);B=pd.DataFrame(B);C=pd.DataFrame(base)
def sm(X,cols): return {c:f"{X[c].mean():+.2f}% (goes that way {(X[c]>0).mean()*100:.0f}%)" for c in cols}
print(f'SETUP A (premarket ON, 10m): EMAs held one side of VWAP to 10:20, then price back to VWAP + EMA5&9 turn: {len(A)} signals on {A.tk.nunique()} tickers')
print('  measured in the ORIGINAL morning-trend direction (+ = trend resumed / bounced, - = REVERSED through VWAP):')
for k,v in sm(A,['trend_dir_30m','trend_dir_60m','trend_dir_close']).items(): print('   ',k,v)
print('  signal time:',pd.Series([t.hour for t in A.time]).value_counts().sort_index().to_dict())
print(f'\nSETUP B (premarket OFF, 10m): EMA9 touches VWAP without crossing, then turns back: {len(B)} signals')
print('  measured in the bounce direction (away from VWAP, + = bounced as expected):')
for k,v in sm(B,['bounce_30m','bounce_60m','bounce_close']).items(): print('   ',k,v)
print(f'  compare - EMA9 actually CROSSED VWAP ({len(C)} times), measured in the cross direction:')
for k,v in sm(C,['cross_30m','cross_60m','cross_close']).items(): print('   ',k,v)
print('\nper ticker  A (to close) | B (60m):')
print(pd.concat([A.groupby('tk').trend_dir_close.agg(['size','mean']).rename(columns={'size':'A_n','mean':'A_avg'}),B.groupby('tk').bounce_60m.agg(['size','mean']).rename(columns={'size':'B_n','mean':'B_avg'})],axis=1).round(2).T.to_string())
A.to_pickle('SA.pkl'); B.to_pickle('SB.pkl')
