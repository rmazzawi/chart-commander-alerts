import pandas as pd, numpy as np
from datetime import time as T
exec(open('vwap10.py').read().split("A=[];B=[];base=[]")[0])
res=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d=d[d.t>='2026-07-27']
    for ext in [True,False]:
        mode='premarket ON ' if ext else 'premarket OFF'
        b=bars10(d,ext)
        for day,g in b.groupby('date'):
            r=g[(g.tm>=T(9,30))&(g.tm<T(16,0))].reset_index()
            if len(r)<36: continue
            o=r.open.iloc[0]; side=np.sign(r.e9-r.vwap); s5=np.sign(r.e5-r.vwap)
            start=1 if not ext else 0          # premarket OFF: VWAP starts at 9:30, skip the very first bar
            s0=side[start:6]
            if not ((s0==s0.iloc[0]).all() and (s5[start:6]==s0.iloc[0]).all()) or s0.iloc[0]==0: continue
            tr=s0.iloc[0]
            for k in range(6,len(r)-2):
                if r.tm[k]>=T(15,0): break
                touch=(r.low[k]<=r.vwap[k]) if tr==1 else (r.high[k]>=r.vwap[k])
                turn=(r.e5[k]-r.e5[k-1])*tr<0 and (r.e9[k]-r.e9[k-1])*tr<0
                if touch and turn:
                    res.append(dict(mode=mode,tk=tk,setup=f'{mode} | all signals (trend direction)',**fwd(r,k,tr,o)))
                    if (r.close[k+1]-r.close[k])*tr>0 and (r.close[k+1]-r.vwap[k+1])*tr>0:
                        res.append(dict(mode=mode,tk=tk,setup=f'{mode} | next bar BOUNCES (trade with trend)',**fwd(r,k+1,tr,o)))
                    elif (r.close[k+1]-r.vwap[k+1])*tr<0:
                        res.append(dict(mode=mode,tk=tk,setup=f'{mode} | next bar closes THROUGH VWAP (trade reversal)',**fwd(r,k+1,-tr,o)))
                    break
R=pd.DataFrame(res)
g=R.groupby('setup').agg(n=('close','size'),**{c:(c,lambda s:f"{s.mean():+.2f}% ({(s>0).mean()*100:.0f}%)") for c in ['30m','60m','close']})
print('(+ = price went the way the trade says; % = how often)'); print(g.to_string())
print('\nper ticker, premarket OFF, all signals, avg to close:'); x=R[R.setup.str.contains('OFF \\| all')]
print(x.groupby('tk').close.agg(['size','mean']).round(2).T.to_string())
