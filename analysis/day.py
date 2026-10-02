import pandas as pd, numpy as np
F=pd.read_pickle('F.pkl'); F=F[F.t>='2026-07-27']; S=F[F.s==2].copy()
mkt=pd.read_pickle('D_SPY.pkl'); mkt.index=mkt.t
rows=[]
for tk,T in S.groupby('tk'):
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tod']=d.t.dt.time
    rth=d[(d.tod>=pd.Timestamp('09:30').time())&(d.tod<pd.Timestamp('16:00').time())]
    drng=rth.groupby('date').agg(h=('high','max'),l=('low','min'),o=('open','first'),c=('close','last'))
    drng['rng']=drng.h-drng.l; drng['avg']=drng.rng.shift().rolling(10,min_periods=3).mean()
    drng['full']=(drng.c-drng.o)/drng.rng  # hindsight
    for idx,x in T.iterrows():
        r=d.loc[x.i]; dt=r.date; so=rth[(rth.date==dt)&(rth.index<=x.i)]
        if len(so)<2: continue
        net=so.close.iloc[-1]-so.open.iloc[0]; path=so.close.diff().abs().sum()+1e-9
        side=np.sign(so.close-so.VWAP).mean()
        m=mkt.loc[:r.t]; mo=m[m.date==dt]; mo=mo[mo.t.dt.time>=pd.Timestamp('09:30').time()]
        mtr=(mo.close.iloc[-1]-mo.open.iloc[0])/mo.atr.iloc[-1] if len(mo) else 0
        a=drng.loc[dt]
        rows.append(dict(idx=idx, er=net/path*x.dir, side=side*x.dir,
            rngx=(so.high.max()-so.low.min())/a.avg if a.avg==a.avg else np.nan,
            mkt=mtr*x.dir, hind=a.full*x.dir))
X=S.join(pd.DataFrame(rows).set_index('idx')); X.to_pickle('S2day.pkl')
for c in ['hind','er','side','rngx','mkt']:
    for lab,P in [('early',X[X.t<'2026-09-04']),('late',X[X.t>='2026-09-04'])]:
        q=pd.qcut(P[c].rank(method='first'),4,labels=False)
        g=P.groupby(q).agg(lo=(c,'min'),hi=(c,'max'),n=('R','size'),win=('win','mean'),Rper=('R','mean'))
        print('--',c,lab); print(g.round(2).to_string())
