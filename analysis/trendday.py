import pandas as pd, numpy as np
from datetime import time as T
def days(tk):
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time
    rows=[]
    for day,g in d.groupby('date'):
        r=g[(g.tm>=T(9,30))&(g.tm<T(16,0))]; pm=g[(g.tm>=T(4,0))&(g.tm<T(9,30))]
        if len(r)<150: continue
        o,c,h,l=r.open.iloc[0],r.close.iloc[-1],r.high.max(),r.low.min()
        f=r[r.tm<T(10,0)]; f60=r[r.tm<T(10,30)]
        rows.append(dict(date=pd.Timestamp(day),o=o,c=c,h=h,l=l,rng=h-l,net=c-o,
            f30_net=f.close.iloc[-1]-o, f30_rng=f.high.max()-f.low.min(), f60_net=f60.close.iloc[-1]-o,
            f30_vol=f.Volume.sum(), pm_rng=(pm.high.max()-pm.low.min()) if len(pm) else np.nan,
            pdh=r['Prior-day high'].iloc[0], pdl=r['Prior-day low'].iloc[0],
            vw_side30=np.sign(f.close.iloc[-1]-f.VWAP.iloc[-1]),
            vw_cross=((r.close>r.VWAP)!=(r.close.shift()>r.VWAP.shift())).sum(),
            s200=r['SMA 200'].iloc[0], e89=r['EMA 89'].iloc[0]))
    D=pd.DataFrame(rows).set_index('date')
    D['pc']=D.c.shift(); D['gap']=(D.o-D.pc)/D.pc*100
    D['rng%']=D.rng/D.o*100; D['avg_rng']=D['rng%'].shift().rolling(10,min_periods=3).mean()
    D['eff']=D.net.abs()/D.rng                       # 1.0 = opened at one extreme, closed at the other
    D['trend']=(D.eff>=0.6)&(D['rng%']>=D.avg_rng*1.2)
    D['prev_rng_ratio']=(D['rng%'].shift()/D.avg_rng)   # yesterday quiet?  (<0.8 = compression)
    D['f30_rng_ratio']=(D.f30_rng/D.o*100)/D.avg_rng
    D['f30_vol_ratio']=D.f30_vol/D.f30_vol.shift().rolling(10,min_periods=3).mean()
    D['pm_ratio']=(D.pm_rng/D.o*100)/D.avg_rng
    D['open_out']=np.where(D.o>D.pdh,'above PDH',np.where(D.o<D.pdl,'below PDL','inside'))
    D['f30_dir_same']=np.sign(D.f30_net)==np.sign(D.net)
    D['f60_dir_same']=np.sign(D.f60_net)==np.sign(D.net)
    D['dow']=D.index.day_name().str[:3]
    return D.dropna(subset=['avg_rng'])
for tk in ['SPY','SPX']:
    D=days(tk); D.to_pickle(f'TD_{tk}.pkl')
    print(f'===== {tk}: {len(D)} days, {D.trend.sum()} trend days')
    print(D[D.trend][['net','rng%','avg_rng','eff','gap','prev_rng_ratio','f30_rng_ratio','f30_vol_ratio','pm_ratio','open_out','vw_side30','vw_cross','f30_dir_same','f60_dir_same','dow']].round(2).to_string())
    cols=['gap','prev_rng_ratio','f30_rng_ratio','f30_vol_ratio','pm_ratio','vw_cross']
    D['absgap']=D.gap.abs()
    print('\nmedians  trend vs normal days:'); print(D.groupby('trend')[cols+['absgap']].median().round(2).T)
    print('first-30m direction = day direction:',D.groupby('trend').f30_dir_same.mean().round(2).to_dict(),' first-60m:',D.groupby('trend').f60_dir_same.mean().round(2).to_dict())
    print('open outside prior-day range:',D.groupby('trend').open_out.apply(lambda s:(s!='inside').mean()).round(2).to_dict())
