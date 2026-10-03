import pandas as pd, numpy as np
A=pd.read_pickle('SIM.pkl'); A=A[~((A.mins>=180)&(A.mins<270))].copy()   # current script: 400SMA + lunch
A=A.sort_values(['tk','t']); A['d']=A.t.dt.date
D={tk:pd.read_pickle(f'D_{tk}.pkl') for tk in A.tk.unique()}
# features at entry
ch=[];h1=[]
for tk,d in D.items():
    vx=((d.close>d.VWAP)!=(d.close.shift()>d.VWAP.shift())).astype(int).rolling(20).sum()
    flat=(d.VWAP-d.VWAP.shift(15)).abs()<d.atr*0.3
    d['chop']=(vx>=4)|flat
    h=d.set_index('t').close.resample('60min').last().dropna(); e=h.ewm(span=20,adjust=False).mean()
    hh=pd.DataFrame({'hc':h,'he':e}); hh.index=hh.index+pd.Timedelta('60min')  # only completed hour usable
    m=pd.merge_asof(d[['t']],hh.reset_index().rename(columns={'t':'t'}).sort_values('t'),on='t'); d['h1']=np.sign(m.hc-m.he).values
A['chop']=[D[r.tk].chop.iloc[r.i] for r in A.itertuples()]
A['h1']=[D[r.tk].h1.iloc[r.i] for r in A.itertuples()]*A.dir
def s(P): return f"{len(P):4d} {P.win.mean()*100:3.0f}% {P.R.sum():7.1f}R"
def show(name,keep):
    print('\n==',name)
    for per in ['early','late']:
        P=A[A.per==per]; K=P[keep[P.index]]
        imp=sum(K[K.tk==t].R.sum()>=P[P.tk==t].R.sum()-1e-9 for t in P.tk.unique())
        print(f"  {'Jul27-Sep3' if per=='early' else 'Sep4-Oct2 '} before {s(P)}  after {s(K)}  tickers same/better {imp}/12")
print('CURRENT SCRIPT by period:'); [print(' ',p,s(A[A.per==p])) for p in ['early','late']]
# 1 stop after 2 losses/day/ticker
k=pd.Series(True,index=A.index)
for (tk,d),g in A.groupby(['tk','d']):
    l=0
    for i,r in g.iterrows():
        if l>=2: k[i]=False
        else: l+= (not r.win)
show('1: stop after 2 losing trades per ticker per day',k)
for n in [1,3]:
    k=pd.Series(True,index=A.index)
    for (tk,d),g in A.groupby(['tk','d']):
        l=0
        for i,r in g.iterrows():
            if l>=n: k[i]=False
            else: l+=(not r.win)
    show(f'1b: stop after {n} losing trades per ticker per day',k)
# 2 trend/chop router
trend=A.s.isin([1,4,5,6]); rev=A.s.isin([2,3])
show('2a: trend strategies (S1,S4,S5,S6) only when NOT chop',~(trend&A.chop))
show('2b: S2/S3 only when chop',~(rev&~A.chop))
show('2c: full router (2a + 2b)',~(trend&A.chop)&~(rev&~A.chop))
# 3 1H alignment
show('3: all trades must agree with 1H trend (1H close vs 1H 20 EMA)',A.h1>0)
show('3b: 1H alignment for trend strategies only (S1,S4,S5,S6)',~(trend&(A.h1<=0)))
A.to_pickle('DOC.pkl')
