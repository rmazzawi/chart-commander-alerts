import pandas as pd, numpy as np
from datetime import time as T
exec(open('vwap10.py').read().split("A=[];B=[];base=[]")[0])
res=[]
for tk in TK:
    d=pd.read_pickle(f'D_{tk}.pkl'); d=d[d.t>='2026-07-27']
    for ext in [True,False]:
        b=bars10(d,ext)
        for day,g in b.groupby('date'):
            r=g[(g.tm>=T(9,30))&(g.tm<T(16,0))].reset_index()
            if len(r)<36: continue
            o=r.open.iloc[0]; side=np.sign(r.e9-r.vwap); vs=np.sign(r.vwap-r.vwap.shift(3))
            if ext:
                s0=side[:6]; s5=np.sign(r.e5-r.vwap)[:6]
                if not ((s0==s0.iloc[0]).all() and (s5==s0.iloc[0]).all()): continue
                tr=s0.iloc[0]
                for k in range(6,len(r)-2):
                    if r.tm[k]>=T(11,30): break
                    touch=(r.low[k]<=r.vwap[k]) if tr==1 else (r.high[k]>=r.vwap[k])
                    turn=(r.e5[k]-r.e5[k-1])*tr<0 and (r.e9[k]-r.e9[k-1])*tr<0
                    if touch and turn:
                        conf_with=(r.close[k+1]-r.close[k])*tr>0 and (r.close[k+1]-r.vwap[k+1])*tr>0   # next bar closes back in trend dir, above/below VWAP
                        conf_against=(r.close[k+1]-r.vwap[k+1])*tr<0                                  # next bar closes through VWAP
                        lab='A + next bar confirms TREND (bounce)' if conf_with else ('A + next bar closes THROUGH VWAP' if conf_against else 'A + unclear next bar')
                        dr=tr if conf_with else (-tr if conf_against else tr)
                        f=fwd(r,k+1,dr,o); res.append(dict(setup=lab,**f)); break
            else:
                for k in range(3,len(r)-2):
                    if r.tm[k]>=T(15,0): break
                    s=side[k-2]
                    if s==0 or side[k-1]!=s or side[k]!=s: continue
                    gap=abs(r.e9[k]-r.vwap[k])/r.atr[k]; turned=(r.e9[k]-r.e9[k-1])*s>0 and (r.e9[k-1]-r.e9[k-2])*s<0
                    if turned and gap<=0.05: res.append(dict(setup='B tight touch (<=0.05 ATR)',**fwd(r,k,s,o)))
                    if turned and gap<=0.15 and vs[k]==s: res.append(dict(setup='B touch + VWAP sloping same way',**fwd(r,k,s,o)))
                    if turned and gap<=0.15 and (r.close[k+1]-r.close[k])*s>0 and (r.close[k+1]-r.vwap[k+1])*s>0: res.append(dict(setup='B touch + next bar confirms bounce',**fwd(r,k+1,s,o)))
R=pd.DataFrame(res)
g=R.groupby('setup').agg(n=('close','size'),**{f'{c}':(c,lambda s:f"{s.mean():+.2f}% ({(s>0).mean()*100:.0f}%)") for c in ['30m','60m','close']})
print('(+ = price went the way the signal says;  % in brackets = how often)'); print(g.to_string())
