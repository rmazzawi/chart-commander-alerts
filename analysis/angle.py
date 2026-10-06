import pandas as pd, numpy as np
from datetime import time as T
A=pd.read_pickle('TDALL.pkl'); A=A[A.index>='2026-07-27']
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def ang(y,avg_pct,o):
    # regression slope per 2m bar -> normalized: 1.0 = pace of one average daily range over 195 bars (6.5h) -> 45 deg
    x=np.arange(len(y)); s=np.polyfit(x,y,1)[0]; pace=(avg_pct/100*o)/195
    return np.degrees(np.arctan(s/pace))
rows=[];fade=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time
    for day,g in d.groupby('date'):
        day=pd.Timestamp(day)
        if (tk,day) not in set(zip(A.tk,A.index)): continue
        info=A[(A.tk==tk)&(A.index==day)].iloc[0]
        r=g[(g.tm>=T(9,30))&(g.tm<T(16,0))].reset_index(drop=True); o=r.open.iloc[0]
        h1=r[r.tm<T(10,30)]
        a1=ang(h1.close.values,info.avg,o); dr=np.sign(a1) if a1!=0 else 1
        p=h1.close.iloc[-1]; c=r.close.iloc[-1]
        rows.append(dict(tk=tk,date=day,angle=a1,trend=info.trend,rest=(c-p)*dr/o*100, rest_atr=(c-p)*dr/(info.avg/100*o)))
        # fade test on steep mornings: rolling 30-min (15 bars) angle after 10:30; first time it drops below 20 deg (in trend direction)
        if abs(a1)>=45:
            cl=r.close.values; k0=len(h1)
            for k in range(k0,len(r)-1):
                a=ang(cl[k-14:k+1],info.avg,o)*dr
                if a<20:
                    fade.append(dict(tk=tk,date=day,fade_time=r.tm[k],before=(cl[k]-p)*dr/o*100,after=(c-cl[k])*dr/o*100)); break
            else: fade.append(dict(tk=tk,date=day,fade_time=None,before=(c-p)*dr/o*100,after=0.0))
R=pd.DataFrame(rows); R['abs']=R.angle.abs()
R['bucket']=pd.cut(R['abs'],[0,15,30,45,60,90],labels=['0-15°','15-30°','30-45°','45-60°','60°+'])
g=R.groupby('bucket',observed=True).agg(days=('rest','size'),trend_day=('trend','mean'),kept_dir=('rest',lambda s:(s>0).mean()),avg_move=('rest','mean'),avg_in_day_ranges=('rest_atr','mean'))
g['trend_day']=(g.trend_day*100).round(0); g['kept_dir']=(g.kept_dir*100).round(0)
print('FIRST-HOUR ANGLE at 10:30 (all 12 tickers) -> what happened 10:30 to close'); print(g.round(2).to_string())
S=R[~R.tk.isin(['SPY','SPX','QQQ','IWM'])]; print('\nper ticker, days with angle>=45 at 10:30: kept direction / avg move to close')
print(R[R['abs']>=45].groupby('tk').agg(days=('rest','size'),kept=('rest',lambda s:f"{(s>0).mean()*100:.0f}%"),avg=('rest',lambda s:f"{s.mean():+.2f}%")).T.to_string())
Fd=pd.DataFrame(fade)
print(f'\nFADE TEST: {len(Fd)} steep mornings (>=45 deg). Rolling 30-min angle dropped below 20 deg on {Fd.fade_time.notna().sum()}')
f=Fd[Fd.fade_time.notna()]
print(f"  move from 10:30 until the fade: {f.before.mean():+.2f}%   |   move from the fade to close: {f.after.mean():+.2f}% (kept going {(f.after>0).mean()*100:.0f}% of the time)")
f['ft']=pd.to_datetime(f.fade_time.astype(str)); print('  when the fade happened:',f.ft.dt.hour.value_counts().sort_index().to_dict())
R.to_pickle('ANG.pkl'); Fd.to_pickle('FADE.pkl')
