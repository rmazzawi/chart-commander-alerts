import pandas as pd, numpy as np
from math import log, sqrt, exp, erf
N=lambda x:0.5*(1+erf(x/sqrt(2)))
def bs(S,K,T,v,cp,r=0.04):
    T=max(T,1e-6); d1=(log(S/K)+(r+v*v/2)*T)/(v*sqrt(T)); d2=d1-v*sqrt(T)
    return S*N(d1)-K*exp(-r*T)*N(d2) if cp==1 else K*exp(-r*T)*N(-d2)-S*N(-d1)
T=pd.read_pickle('MY.pkl'); A=pd.read_pickle('SIM.pkl')
D={tk:pd.read_pickle(f'D_{tk}.pkl') for tk in A.tk.unique()}
DC={}
for tk,d in D.items():
    r=d[(d.t.dt.time>=pd.Timestamp('09:30').time())&(d.t.dt.time<pd.Timestamp('16:00').time())]
    dc=r.groupby('date').agg(c=('close','last'),t=('t','last')); dc['vol']=np.log(dc.c).diff().rolling(20,min_periods=5).std()*sqrt(252)*1.1
    DC[tk]=dc
def px(tk,ts):
    d=D[tk]; k=d.t.searchsorted(ts); k=min(max(k,0),len(d)-1); return d.close.iloc[k], d.t.iloc[k]
def yrs(a,b): return (b-a).total_seconds()/(365*86400)
def run(tk,t_in,t_out,cp,hold_days):
    if tk not in D: return None
    S0,t0=px(tk,t_in); dc=DC[tk]; day=t0.date()
    if day not in dc.index or np.isnan(dc.vol.get(day,np.nan)): return None
    v=dc.vol[day]; exp_=pd.Timestamp(day)+pd.Timedelta(days=14+(4-pd.Timestamp(day).weekday())%7)+pd.Timedelta(hours=16)
    K=round(S0); P0=bs(S0,K,yrs(t0,exp_),v,cp)
    S1,t1=px(tk,t_out); P1=bs(S1,K,yrs(t1,exp_),v,cp)
    if P1>P0 or hold_days==0: return (P1-P0)*100-1.3, 0
    days=[x for x in dc.index if x>t1.date()][:hold_days]
    if not days: return (P1-P0)*100-1.3, 0
    for i,x in enumerate(days):
        Pd=bs(dc.c[x],K,yrs(dc.t[x],exp_),v,cp)
        if Pd>P0: return (Pd-P0)*100-1.3, i+1
    return (Pd-P0)*100-1.3, len(days)
W=T[(T.open>='2026-07-27')&(T.und.isin(list(D)))].copy(); W['cp']=np.where(W.typ=='CALL',1,-1)
out=[]
for h,lab in [(0,'weekly, exit same time as you did'),(5,'weekly, hold losers up to 1 week'),(10,'weekly, hold losers up to 2 weeks')]:
    res=[run(r.und,r.open,r.close,r.cp,h) for r in W.itertuples()]
    v=pd.Series([x[0] if x else np.nan for x in res]).dropna()
    out.append(dict(scenario='YOUR TRADES: '+lab,trades=len(v),win=f"{(v>0).mean()*100:.0f}%",net=round(v.sum()),avg_win=round(v[v>0].mean()),avg_loss=round(v[v<=0].mean())))
ok=W.index[[run(r.und,r.open,r.close,r.cp,0) is not None for r in W.itertuples()]]
a=W.loc[ok]; out.insert(0,dict(scenario='YOUR TRADES: actual 0DTE (real fills)',trades=len(a),win=f"{a.win.mean()*100:.0f}%",net=round(a.net.sum()),avg_win=round(a.net[a.net>0].mean()),avg_loss=round(a.net[a.net<=0].mean())))
c=np.maximum(a.net,-0.4*a.entry*100*a.qty-a.fees); out.insert(1,dict(scenario='YOUR TRADES: 0DTE with -40% exit',trades=len(a),win=f"{(c>0).mean()*100:.0f}%",net=round(c.sum()),avg_win=round(c[c>0].mean()),avg_loss=round(c[c<=0].mean())))
# script signals: exit time = next exit bar
S=A[(A.t<'2026-09-24')&A.tk.isin(['SPY','TSLA','SPX','IWM','AMD','QQQ','AAPL','NVDA'])].copy()
def exit_t(r):
    d=D[r.tk]; e=d.loc[r.i+1:r.i+300]; k=e[e.ActionCode.abs()==3]
    return k.t.iloc[0] if len(k) else d.t.iloc[min(r.i+1,len(d)-1)]
S['tout']=S.apply(exit_t,axis=1)
for h,lab in [(0,'weekly, script exit'),(5,'weekly, hold losers up to 1 week'),(10,'weekly, hold losers up to 2 weeks')]:
    v=pd.Series([ (lambda x: x[0] if x else np.nan)(run(r.tk,r.t,r.tout,r.dir,h)) for r in S.itertuples()]).dropna()
    out.append(dict(scenario='SCRIPT SIGNALS: '+lab,trades=len(v),win=f"{(v>0).mean()*100:.0f}%",net=round(v.sum()),avg_win=round(v[v>0].mean()),avg_loss=round(v[v<=0].mean())))
print(pd.DataFrame(out).to_string(index=False))
print('---- by ticker, script signals, net $')
rows={}
for h in [0,5,10]:
    S['v%d'%h]=[ (lambda x: x[0] if x else np.nan)(run(r.tk,r.t,r.tout,r.dir,h)) for r in S.itertuples()]
print(S.groupby('tk')[['v0','v5','v10']].sum().round(0).to_string())
X=S[S.tk!='SPX']; print('excluding SPX:',X[['v0','v5','v10']].sum().round(0).to_dict())
