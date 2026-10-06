import pandas as pd, numpy as np
from datetime import time as T
for tk in ['SPX','SPY']:
    D=pd.read_pickle(f'TD_{tk}.pkl'); d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time
    feat={}
    for day,g in d.groupby('date'):
        day=pd.Timestamp(day)
        if day not in D.index: continue
        r=g[(g.tm>=T(9,30))&(g.tm<T(10,30))]; o=r.open.iloc[0]
        h1=r[r.tm<T(10,30)]; side=np.sign(h1.close-h1.VWAP)
        a30=r[r.tm<T(10,0)]
        feat[day]=dict(h1_cross=int((side!=side.shift()).iloc[1:].sum()),
                       h1_side_frac=abs(side.mean()),
                       h1_move=abs(h1.close.iloc[-1]-o)/o*100,
                       h1_eff=abs(h1.close.iloc[-1]-o)/(h1.high.max()-h1.low.min()),
                       h1_at_ext= (h1.close.iloc[-1]>=h1.high.max()-0.25*(h1.high.max()-h1.low.min())) or (h1.close.iloc[-1]<=h1.low.min()+0.25*(h1.high.max()-h1.low.min())))
    F=D.join(pd.DataFrame(feat).T.astype(float))
    F['h1_move_ratio']=F.h1_move/F.avg_rng
    print(f'===== {tk}: {len(F)} days, {int(F.trend.sum())} trend days')
    print('medians at 10:30:'); print(F.groupby('trend')[['h1_cross','h1_side_frac','h1_move_ratio','h1_eff','h1_at_ext']].median().round(2).T)
    rules={
     'A: first hour stays one side of VWAP (<=1 cross)':F.h1_cross<=1,
     'B: first-hour move >= 40% of avg daily range':F.h1_move_ratio>=0.4,
     'C: first hour closes near its high/low (top/bottom 25%)':F.h1_at_ext==1,
     'A+B':(F.h1_cross<=1)&(F.h1_move_ratio>=0.4),
     'A+B+C':(F.h1_cross<=1)&(F.h1_move_ratio>=0.4)&(F.h1_at_ext==1),
     'A+B+C + gap >= 0.15%':(F.h1_cross<=1)&(F.h1_move_ratio>=0.4)&(F.h1_at_ext==1)&(F.gap.abs()>=0.15),
    }
    print(f"{'rule (known at 10:30)':55} flagged  trend-days-caught  hit-rate")
    for n,m in rules.items():
        fl=int(m.sum()); hit=int((m&F.trend).sum())
        print(f"{n:55} {fl:5d}   {hit:3d} of {int(F.trend.sum()):2d}       {hit/max(fl,1)*100:4.0f}%")
    m=rules['A+B+C']
    print('days flagged by A+B+C:'); print(F[m][['trend','eff','rng%','avg_rng','net']].round(2).to_string())
    print('--- if flagged at 10:30 (A+B): ride first-hour direction from 10:30 to close')
    rows=[]
    for day in F.index:
        g=d[(d.date==day.date())&(d.tm>=T(9,30))&(d.tm<T(16,0))]
        o=g.open.iloc[0]; p1030=g[g.tm<T(10,30)].close.iloc[-1]; c=g.close.iloc[-1]
        dr=np.sign(p1030-o); rows.append(dict(date=day,dr=dr,rest=(c-p1030)*dr/o*100))
    R=pd.DataFrame(rows).set_index('date'); F=F.join(R)
    for n,m in [('A+B flagged',(F.h1_cross<=1)&(F.h1_move_ratio>=0.4)),('all other days',~((F.h1_cross<=1)&(F.h1_move_ratio>=0.4)))]:
        X=F[m]; print(f"  {n:16} days {len(X):3d} | same direction by close {(X.rest>0).mean()*100:3.0f}% | avg move 10:30->close {X.rest.mean():+.2f}% | avg win {X.rest[X.rest>0].mean():.2f}% avg loss {X.rest[X.rest<=0].mean():.2f}%")
