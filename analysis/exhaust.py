import pandas as pd, numpy as np
from datetime import time as T
TK=['TSLA','NVDA','AMD','AAPL','AMZN','META','MSFT','QQQ','IWM','GLD','SPY','SPX']
def tri(dp,n,u): adj=n*u; h=np.hypot(adj,abs(dp)); return np.degrees(np.arccos(adj/h)) if h>0 else 0
rows=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d['tm']=d.t.dt.time
    rth=d[(d.tm>=T(9,30))&(d.tm<T(16,0))].copy(); rth['br']=rth.high-rth.low
    unit=rth.groupby('date').br.mean().shift().rolling(5,min_periods=3).mean()
    dly=rth.groupby('date').agg(H=('high','max'),L=('low','min'),C=('close','last'),O=('open','first'))
    dly['P']=(dly.H+dly.L+dly.C)/3; dly['R1']=2*dly.P-dly.L; dly['S1']=2*dly.P-dly.H; dly['R2']=dly.P+(dly.H-dly.L); dly['S2']=dly.P-(dly.H-dly.L)
    dly['H5']=dly.H.rolling(5).max(); dly['L5']=dly.L.rolling(5).min(); dly['sma5']=dly.C.rolling(5).mean()
    h60=rth.set_index('t').close.resample('60min',origin='start_day',offset='30min').last().dropna(); e60=h60.ewm(span=20,adjust=False).mean()
    days=list(dly.index)
    for i,day in enumerate(days):
        if i<6 or day not in unit or pd.isna(unit[day]) or pd.Timestamp(day)<pd.Timestamp('2026-07-27'): continue
        y=dly.iloc[i-1]; u=unit[day]; r=rth[rth.date==day].reset_index(drop=True)
        if len(r)<150: continue
        o=r.open.iloc[0]; c=r.close.iloc[-1]; h1=r[r.tm<T(10,30)]; p=h1.close.iloc[-1]; up=p>=o; dr=1 if up else -1
        ti=h1.high.idxmax() if up else h1.low.idxmin(); tip=r.high[ti] if up else r.low[ti]
        ang=tri(tip-o,ti+1,u)
        if ang<20: continue                                    # only strong mornings
        # day tip (morning extreme extended until it reversed): extreme of whole day in morning direction
        dti=r.high.idxmax() if up else r.low.idxmin(); dtip=r.high[dti] if up else r.low[dti]
        outcome='REVERSED' if (c-o)*dr<0 else ('KEPT GOING' if (c-p)*dr>0 else 'faded (gave some back)')
        tol=max(2*u, 0.0015*dtip)
        def near(lv): return [n for n,v in lv.items() if pd.notna(v) and abs(dtip-v)<=tol]
        lv={'Pivot P':y.P,'R1':y.R1,'R2':y.R2,'S1':y.S1,'S2':y.S2,'Prior-day high':y.H,'Prior-day low':y.L,
            'PM high':r['PM high'].iloc[0],'PM low':r['PM low'].iloc[0],'5-day high':dly.H5.iloc[i-1],'5-day low':dly.L5.iloc[i-1],
            'SMA200 (2m)':r['SMA 200'][dti],'SMA400 (2m)':r['SMA 400'][dti]}
        step=1 if dtip<100 else (5 if dtip<500 else 10); lv['round number']=round(dtip/step)*step
        hits=near(lv)
        t60=h60[h60.index<pd.Timestamp(day)+pd.Timedelta('9h30min')]; e=e60[e60.index<pd.Timestamp(day)+pd.Timedelta('9h30min')]
        rows.append(dict(tk=tk,date=day,dir='UP' if up else 'DOWN',outcome=outcome,angle=ang,tip_time=r.tm[dti],
            levels=', '.join(hits) if hits else '-', n_levels=len(hits),
            vwap_stretch=(dtip-r.VWAP[dti])*dr/(u*10), rvol_tip=r.RVOL[max(dti-2,0):dti+1].max(),
            vol_fade=r.Volume[max(dti-5,0):dti+1].mean()/max(r.Volume[:15].mean(),1),
            h1_trend_with=int(np.sign(t60.iloc[-1]-e.iloc[-1])==dr), daily_with=int(np.sign(y.C-dly.sma5.iloc[i-1])==dr),
            gap_with=int(np.sign(o-y.C)==dr), yday_with=int(np.sign(y.C-y.O)==dr)))
X=pd.DataFrame(rows); X.to_pickle('EXH.pkl')
print(X.outcome.value_counts().to_string()); K=X[X.outcome!='faded (gave some back)']
print('\nREVERSED vs KEPT GOING (strong mornings, angle>=20):')
f=lambda s:s.mean()
comp=K.groupby('outcome').agg(days=('tk','size'),tip_at_a_level=('n_levels',lambda s:(s>0).mean()*100),levels_at_tip=('n_levels','mean'),
    vwap_stretch=('vwap_stretch','median'),rvol_at_tip=('rvol_tip','median'),vol_vs_open=('vol_fade','median'),
    hour_trend_with_move=('h1_trend_with',lambda s:s.mean()*100),daily_trend_with_move=('daily_with',lambda s:s.mean()*100),
    gap_with_move=('gap_with',lambda s:s.mean()*100),yesterday_with_move=('yday_with',lambda s:s.mean()*100))
print(comp.round(2).T.to_string())
from collections import Counter
for oc in ['REVERSED','KEPT GOING']:
    c=Counter(l for s in K[K.outcome==oc].levels for l in s.split(', ') if l!='-'); n=(K.outcome==oc).sum()
    print(f'\nlevels at the day tip on {oc} days (% of days):',{k:f"{v/n*100:.0f}%" for k,v in c.most_common()})
print('\nREVERSED days:'); print(K[K.outcome=='REVERSED'][['tk','date','dir','angle','tip_time','levels','vwap_stretch','h1_trend_with','daily_with']].round(2).to_string())
