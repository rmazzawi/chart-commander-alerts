import pandas as pd, numpy as np
from datetime import time as T
A=pd.read_pickle('TDALL.pkl'); A=A[A.index>='2026-07-27']; key=set(zip(A.tk,A.index))
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def fit(y,avg_pct,o):
    x=np.arange(len(y)); s,b=np.polyfit(x,y,1); pred=s*x+b
    r2=1-((y-pred)**2).sum()/max(((y-y.mean())**2).sum(),1e-12)
    pace=(avg_pct/100*o)*0.5/30          # 45 deg = half an average daily range per hour (30 bars of 2m)
    return np.degrees(np.arctan(s/pace)), r2
rows=[];fade=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time
    for day,g in d.groupby('date'):
        day=pd.Timestamp(day)
        if (tk,day) not in key: continue
        info=A[(A.tk==tk)&(A.index==day)].iloc[0]
        r=g[(g.tm>=T(9,30))&(g.tm<T(16,0))].reset_index(drop=True); o=r.open.iloc[0]; cl=r.close.values
        h1=r[r.tm<T(10,30)]; k0=len(h1)
        a1,r2=fit(h1.close.values,info.avg,o); dr=1 if a1>=0 else -1; p=cl[k0-1]; c=cl[-1]
        rows.append(dict(tk=tk,date=day,angle=abs(a1),r2=r2,trend=info.trend,rest=(c-p)*dr/o*100))
        if abs(a1)>=45 and r2>=0.6:
            hit=None
            for k in range(k0+15,len(r)-1):                      # rolling 60-min line, checked every bar after 11:00
                a,_=fit(cl[k-29:k+1],info.avg,o)
                if a*dr<20: hit=k; break
            if hit is None: fade.append(dict(tk=tk,faded=False,before=(c-p)*dr/o*100,after=0.0,ftime=None))
            else: fade.append(dict(tk=tk,faded=True,before=(cl[hit]-p)*dr/o*100,after=(c-cl[hit])*dr/o*100,ftime=r.tm[hit].hour))
R=pd.DataFrame(rows)
R['bucket']=pd.cut(R.angle,[0,20,35,45,60,90],labels=['0-20° flat','20-35°','35-45°','45-60°','60°+ steep'])
def show(X,title):
    g=X.groupby('bucket',observed=True).agg(days=('rest','size'),trend_day=('trend','mean'),kept=('rest',lambda s:(s>0).mean()),avg_move=('rest','mean'),avg_win=('rest',lambda s:s[s>0].mean()),avg_loss=('rest',lambda s:s[s<=0].mean()))
    g['trend_day']=(g.trend_day*100).round(0); g['kept']=(g.kept*100).round(0); print(title); print(g.round(2).to_string())
show(R,'FIRST-HOUR ANGLE at 10:30, all 12 tickers -> 10:30 to close (moves in % of price, in the first-hour direction)')
show(R[R.r2>=0.6],'\nSAME, only STRAIGHT first hours (line fits well, R2>=0.6)')
show(R[R.r2<0.6],'\nSAME, only CHOPPY first hours (R2<0.6)')
F=pd.DataFrame(fade); f=F[F.faded]
print(f"\nFADE TEST: {len(F)} steep+straight mornings (>=45 deg, R2>=0.6)")
print(f"  never flattened (60-min angle stayed >=20 deg all day): {(~F.faded).sum()} days, avg move 10:30->close {F[~F.faded].before.mean():+.2f}%")
print(f"  flattened below 20 deg: {len(f)} days | gained {f.before.mean():+.2f}% from 10:30 until the flattening | after flattening to close: {f.after.mean():+.2f}% (kept going {(f.after>0).mean()*100:.0f}%)")
print('  hour when it flattened:',f.ftime.value_counts().sort_index().to_dict())
R.to_pickle('ANG2.pkl'); F.to_pickle('FADE2.pkl')
