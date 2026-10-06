import pandas as pd, numpy as np
from datetime import time as T
F=pd.read_pickle('TD_SPX.pkl'); d=pd.read_pickle('D_SPX.pkl'); d['tm']=d.t.dt.time
r=d[(d.tm>=T(9,30))&(d.tm<T(16,0))].set_index('t')
# ---- calendar
ev={'CPI':['2026-05-12','2026-06-10','2026-07-14','2026-08-12','2026-09-11'],'JOBS':['2026-06-05','2026-07-02','2026-08-07','2026-09-04','2026-10-02'],'FOMC':['2026-06-17','2026-07-29','2026-09-16']}
E={pd.Timestamp(x):k for k,v in ev.items() for x in v}
F['event']=[E.get(i,'') for i in F.index]; F['event_prev']=[E.get(F.index[k-1],'') if k else '' for k in range(len(F))]
ed=F[F.event!='']; print('EVENT DAYS in data:',len(ed),'| trend days among them:',int(ed.trend.sum()),f'({ed.trend.mean()*100:.0f}%)  vs all days {F.trend.mean()*100:.0f}%')
print(ed[['event','trend','eff','rng%','avg_rng']].round(2).to_string())
nd=F[F.event_prev!='']; print('DAY AFTER an event: trend',int(nd.trend.sum()),'of',len(nd))
# ---- higher timeframe bars
def ema(s,n): return s.ewm(span=n,adjust=False).mean()
D1=r.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
H4=r.resample('4h',origin='start_day',offset='9h30min').agg({'close':'last'}).dropna()
H1=r.resample('60min',origin='start_day',offset='30min').agg({'close':'last'}).dropna()
M15=r.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
D1['e9']=ema(D1.close,9); D1['e20']=ema(D1.close,20)
H4['e9']=ema(H4.close,9); H4['e20']=ema(H4.close,20); H1['e9']=ema(H1.close,9); H1['e20']=ema(H1.close,20)
D1['rng']=D1.high-D1.low; D1['nr7']=D1.rng==D1.rng.rolling(7).min(); D1['inside']=(D1.high<D1.high.shift())&(D1.low>D1.low.shift())
D1['clo_loc']=(D1.close-D1.low)/D1.rng
D1['r3']=(D1.high.rolling(3).max()-D1.low.rolling(3).min())/D1.close*100
rows={}
for day in F.index:
    p=D1[D1.index<day]
    if len(p)<21: continue
    y=p.iloc[-1]; open_t=day+pd.Timedelta('9h30min')
    h4=H4[H4.index<open_t].iloc[-1]; h1=H1[H1.index+pd.Timedelta('60min')<=open_t].iloc[-1]
    m=M15[(M15.index>=open_t)].iloc[0]
    a=lambda x: np.sign(x.e9-x.e20)
    rows[day]=dict(y_trend=bool(F.trend.get(p.index[-1],False)), y_eff=abs(y.close-y.open)/y.rng, y_clo=y.clo_loc,
        nr7=bool(y.nr7), inside=bool(y.inside), r3=y.r3, d_al=a(y), h4_al=a(h4), h1_al=a(h1),
        all_al=int(a(y)==a(h4)==a(h1)), ext=(y.close-y.e20)/y.e20*100,
        m15_size=(m.high-m.low)/m.open*100, m15_clo=(m.close-m.low)/(m.high-m.low) if m.high>m.low else .5)
X=F.join(pd.DataFrame(rows).T, how='inner'); X['dirn']=np.sign(X.net)
for c in ['y_eff','y_clo','r3','ext','m15_size','m15_clo']: X[c]=X[c].astype(float)
print(f'\nTIMEFRAME CHECK on {len(X)} days ({int(X.trend.sum())} trend days)')
print(X.groupby('trend')[['y_eff','r3','m15_size']].median().round(2).T)
for nm,col in [('yesterday was a trend day','y_trend'),('yesterday NR7 (narrowest of 7)','nr7'),('yesterday inside day','inside'),('daily+4h+1h EMAs all aligned at open','all_al')]:
    s=X[col].astype(bool); print(f"  {nm:40} trend rate when TRUE {X[s].trend.mean()*100:4.0f}% (n={s.sum()})  when FALSE {X[~s].trend.mean()*100:4.0f}%")
al=X[X.all_al==1]; print('  when all aligned: day went WITH the alignment',f"{(al.dirn==al.d_al).mean()*100:.0f}%",'| trend days with alignment matching direction:',int(((X.all_al==1)&(X.dirn==X.d_al)&X.trend).sum()),'of',int(X.trend.sum()))
X['ext_abs']=X.ext.abs(); print('  stretch from daily 20 EMA (median |%|): trend',round(X[X.trend].ext_abs.median(),2),'normal',round(X[~X.trend].ext_abs.median(),2))
q=pd.qcut(X.m15_size,3,labels=['small','mid','big']); print('  first 15-min candle size -> trend rate:',(X.groupby(q).trend.mean()*100).round(0).to_dict())
X['m15_strong']=(X.m15_clo>=0.8)|(X.m15_clo<=0.2); print('  first 15-min candle closes at its extreme -> trend rate',round(X[X.m15_strong].trend.mean()*100),'% vs',round(X[~X.m15_strong].trend.mean()*100),'%')
X.to_pickle('TDX.pkl')
