import pandas as pd, numpy as np
F=pd.read_pickle('F.pkl').sort_values(['tk','t']); F['date']=F.t.dt.date
S=F[F.s==2].copy()
S['nth']=S.groupby(['tk','date']).cumcount()+1
S['prevloss']=S.groupby(['tk','date']).win.shift().eq(False)
IN=S[S.t>='2026-09-04']; OUT=S[S.t<'2026-09-04']
for c in ['nth']:
    print(IN.groupby(IN[c].clip(upper=4)).agg(n=('R','size'),win=('win','mean'),Rper=('R','mean')).round(2))
print(IN.groupby('prevloss').agg(n=('R','size'),win=('win','mean'),Rper=('R','mean')).round(2))
rules={'A: S2 only before 11:30':lambda x:x.mins<120,
 'B: S2 max 1 per day per ticker':lambda x:x.nth<=1,
 'C: no S2 after an S2 loss same day':lambda x:~x.prevloss,
 'D: S2 big candle <=0.85 ATR':lambda x:x.body<=0.85,
 'E: S2 max 2 per day':lambda x:x.nth<=2}
def summ(X): return f"{len(X):4d} {X.win.mean()*100:4.0f}% {X.R.sum():7.1f}R"
for nm,f in rules.items():
    print('\n==',nm)
    for lab,X in [('Sep4-Oct2',IN),('Earlier (check)',OUT)]:
        k=X[f(X)]; better=sum((k[k.tk==t].R.sum()>X[X.tk==t].R.sum()) for t in X.tk.unique())
        print(f"{lab:16s} before {summ(X)}  after {summ(k)}  tickers improved {better}/{X.tk.nunique()}")
