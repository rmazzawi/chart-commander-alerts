import pandas as pd, numpy as np
X=pd.read_pickle('S2day.pkl'); add=[]
for tk,T in X.groupby('tk'):
    d=pd.read_pickle(f'D_{tk}.pkl')
    for idx,x in T.iterrows():
        r=d.loc[x.i]; p=d.loc[max(0,x.i-30)]
        add.append(dict(idx=idx, vws=(r.VWAP-p.VWAP)*x.dir/r.atr, s200=np.sign(r.close-r['SMA 200'])*x.dir,
          s400=np.sign(r.close-r['SMA 400'])*x.dir, slope89=(r['EMA 89']-p['EMA 89'])*x.dir/r.atr,
          gap=(r.dopen-r['Prior-day high'])*x.dir if x.dir==1 else (r['Prior-day low']-r.dopen)))
X=X.join(pd.DataFrame(add).set_index('idx'))
rules={
 'mkt: no S2 against SPY move >1.5 ATR':lambda x:x.mkt>-1.5,
 'vws: no S2 against VWAP slope (>1 ATR/hr)':lambda x:x.vws>-1,
 's200: S2 only same side of SMA200':lambda x:x.s200>0,
 's400: S2 only same side of SMA400':lambda x:x.s400>0,
 'slope89: no S2 against falling/rising EMA89 >0.5ATR/hr':lambda x:x.slope89>-0.5,
 'mkt+vws':lambda x:(x.mkt>-1.5)&(x.vws>-1),
}
def s(P):return f"{len(P):4d} {P.win.mean()*100:3.0f}% {P.R.sum():6.1f}R"
for n,f in rules.items():
    print('\n==',n)
    for lab,P in [('early',X[X.t<'2026-09-04']),('late ',X[X.t>='2026-09-04'])]:
        k=P[f(P)]; imp=sum(k[k.tk==t].R.sum()>P[P.tk==t].R.sum() for t in P.tk.unique())
        print(lab,'before',s(P),' after',s(k),' tickers better',imp,'/12')
X.to_pickle('S2day2.pkl')
