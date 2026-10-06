import pandas as pd, numpy as np
from datetime import time as T
A=pd.read_pickle('TDALL.pkl'); A=A[A.index>='2026-07-27']; key=set(zip(A.tk,A.index))
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def tri(dp,nbars,unit):
    adj=nbars*unit; hyp=np.hypot(adj,abs(dp))          # horizontal leg = bars x (avg 2m candle size); vertical = price diff
    return np.degrees(np.arccos(adj/hyp)) if hyp>0 else 0.0
rows=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time
    rth=d[(d.tm>=T(9,30))&(d.tm<T(16,0))].copy(); rth['bar_rng']=rth.high-rth.low
    unit_by_day=rth.groupby('date').bar_rng.mean().shift().rolling(5,min_periods=3).mean()   # avg 2m candle, previous 5 days (no peeking)
    for day,g in rth.groupby('date'):
        dd=pd.Timestamp(day)
        if (tk,dd) not in key or pd.isna(unit_by_day.get(day)): continue
        u=unit_by_day[day]; info=A[(A.tk==tk)&(A.index==dd)].iloc[0]
        r=g.reset_index(drop=True); h1=r[r.tm<T(10,30)]; o=r.open.iloc[0]; c=r.close.iloc[-1]; p=h1.close.iloc[-1]
        up=p>=o; tipi=h1.high.idxmax() if up else h1.low.idxmin(); tip=r.high[tipi] if up else r.low[tipi]
        # (1) open -> tip ; (2) swing start (lowest low before the tip for up moves) -> tip
        a_open=tri(tip-o,tipi+1,u)
        pre=h1.loc[:tipi]; si=pre.low.idxmin() if up else pre.high.idxmax(); s=r.low[si] if up else r.high[si]
        a_swing=tri(tip-s,max(tipi-si,1),u)
        dr=1 if up else -1
        rows.append(dict(tk=tk,date=dd,a_open=a_open,a_swing=a_swing,trend=info.trend,rest=(c-p)*dr/o*100,
                         tip_to_close=(c-tip)*dr/o*100))
R=pd.DataFrame(rows); R.to_pickle('TIP.pkl')
print('angle distribution (degrees):'); print(R[['a_open','a_swing']].describe(percentiles=[.25,.5,.75,.9]).round(1).loc[['25%','50%','75%','90%','max']].T)
for col,title in [('a_open','OPEN (9:30) -> TIP by 10:30'),('a_swing','SWING START -> TIP by 10:30')]:
    R['b']=pd.cut(R[col],[0,5,10,15,20,30,45,90],labels=['0-5°','5-10°','10-15°','15-20°','20-30°','30-45°','45°+'])
    g=R.groupby('b',observed=True).agg(days=('rest','size'),trend_day=('trend','mean'),kept=('rest',lambda s:(s>0).mean()),avg_10_30_to_close=('rest','mean'),avg_win=('rest',lambda s:s[s>0].mean()),avg_loss=('rest',lambda s:s[s<=0].mean()))
    g['trend_day']=(g.trend_day*100).round(0); g['kept']=(g.kept*100).round(0)
    print('\nTRIANGLE ANGLE',title); print(g.round(2).to_string())
