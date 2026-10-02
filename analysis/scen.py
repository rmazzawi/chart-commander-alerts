import pandas as pd, numpy as np
T=pd.read_pickle('MY.pkl'); A=pd.read_pickle('SIM.pkl')
T['dir']=np.where(T.typ=='CALL',1,-1)
T['capnet']=np.maximum(T.net,-0.40*T.entry*100*T.qty-T.fees)
mins=T.open.dt.hour*60+T.open.dt.minute
T['lunch']=(mins>=750)&(mins<840)
def m(r):
  c=A[(A.tk==r.und)&((A.t-r.open).abs()<=pd.Timedelta('10min'))]
  return len(c)>0 and (c.dir==r.dir).any()
W0=T.open>='2026-07-27'
T['sig']=False; T.loc[W0,'sig']=T[W0].apply(m,axis=1)
def row(nm,X,col='net'): return dict(scenario=nm,trades=len(X),win=f"{(X[col]>0).mean()*100:.0f}%",net=round(X[col].sum()),per_trade=round(X[col].mean(),1))
for lab,P in [('ALL HISTORY Mar25-Sep26',T),('Jul27-Sep23 2026',T[W0])]:
  print('====',lab)
  R=[row('1 Actual',P),row('2 Exit at -40% (no zeros)',P,'capnet'),row('3 = 2 + no trades 12:30-2:00',P[~P.lunch],'capnet')]
  if lab.startswith('Jul'): R.append(row('4 = 3 + only script-signal trades',P[~P.lunch&P.sig],'capnet'))
  print(pd.DataFrame(R).to_string(index=False))
# Script alone, user tickers, Jul27-Sep23, 400SMA on, lunch block, 1 contract delta .5
tk=['SPY','TSLA','SPX','IWM','AMD','QQQ','AAPL','NVDA']
S=A[A.tk.isin(tk)&(A.t<'2026-09-24')].copy()
S=S[~((S.mins>=180)&(S.mins<270))]
S['usd']=S.pts*0.5*100-1.30
print('==== SCRIPT ONLY (5 rule: 400SMA on, no lunch, script exits), 1 contract, delta 0.5, no time decay')
g=S.groupby('tk').agg(trades=('usd','size'),win=('win','mean'),pts=('pts','sum'),usd=('usd','sum')).round(1)
g.loc['TOTAL']=[len(S),S.win.mean(),S.pts.sum(),S.usd.sum()]; g.win=(g.win.astype(float)*100).round(); print(g.round(0).to_string())
for per,X in [('Jul27-Sep3',S[S.t<'2026-09-04']),('Sep4-Sep23',S[S.t>='2026-09-04'])]: print(per,len(X),round(X.usd.sum()))
