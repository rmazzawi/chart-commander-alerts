# Scorecard: every indicator (and its on/off options) tested on every ticker. Same 2m data, Jul 27 - Oct 2 2026,
# regular hours, one trade at a time, result per trade in R AFTER option costs (0.02% liquid / 0.04% others).
import pandas as pd, numpy as np, re
from datetime import time as TT
LIQ={'SPY','QQQ','IWM','AAPL','NVDA','TSLA','AMD','MSFT','META','AMZN'}
TK=['AAPL','AMD','AMZN','GLD','IWM','META','MSFT','NVDA','QQQ','SPY','TSLA']
px={tk:pd.read_pickle(f'work/D_{tk}.pkl').close.mean() for tk in TK}
cr=lambda tk:0.0002 if tk in LIQ else 0.0004
R=[]
def add(name,tk,net,date):
    for n,dd in zip(net,date): R.append(dict(ind=name,tk=tk,net=n,date=pd.Timestamp(dd)))
# 1) CC-Multi (current exits), all setups and each setup alone
D=pd.read_pickle('work/DOC.pkl'); D=D[D.tk.isin(TK)]; D['net']=D['current']-D.tk.map(cr)*D.entry/D.risk
for tk,g in D.groupby('tk'):
    add('CC-Multi (all setups)',tk,g.net,g.t)
    for s,h in g.groupby('s'): add(f'CC-Multi setup S{s} only',tk,h.net,h.t)
# 2) Pin bar at day low/high (CC-Multi V8 info alert)
P=pd.read_pickle('work/PINLOOSE.pkl'); P=P[P.tk.isin(TK)&(P.tf==P.tf.min())] if 'tf' in P else P
for tk,g in P.groupby('tk'): add('Pin bar at day low/high (V8)',tk,g.R1-cr(tk)*100/g.stp,g.t)  # stp = stop size in % of price
# 3) TGA
G=pd.read_pickle('work/TGASTOP.pkl')
for tk,g in G.groupby('tk'):
    add('TGA (default)',tk,g.net,g.date); add('TGA skip stop>1.5 ATR',tk,g[g.ratio<=1.5].net,g[g.ratio<=1.5].date)
    b=g[g.name=='3 Black Crows']; add('TGA 3 Black Crows only',tk,b.net,b.date)
# 4) Farley (one trade at a time)
exec(open('analysis/farley_range.py').read().split("o=[]\n")[0])
for kinds,nm in [(('dayrev',),'Farley Day Rev (new default)'),(('conv',),'Farley Convergence ON'),(('range',),'Farley Range Breakout ON'),(('dayrev','conv','range'),'Farley everything ON')]:
    Y=seq('keep',kinds)
    for tk,g in Y.groupby('tk'): add(nm,tk,g.net,g.date)
src=open('analysis/bb_reversal.py').read(); exec('from datetime import time as T\n'+src[src.index('def run'):src.index('rows=[]')])
for tk in TK:
    d=pd.read_pickle(f'work/D_{tk}.pkl'); d['t']=pd.to_datetime(d['time'].str[:19]); d=d[(d.t.dt.time>=TT(9,30))&(d.t.dt.time<TT(16,0))]
    B=run(d,'mid')
    if len(B): add('Farley BB Reversal ON',tk,B.R-cr(tk)/0.0002*(B.R-B.Rc),B.t)
# 5) Indicator Confluence: 7/10 votes + ADX>=20 + SAR side; stop = SAR, exit when SAR flips / 4 PM
for tk in TK:
    d=pd.read_pickle(f'work/D_{tk}.pkl').reset_index(drop=True); t=pd.to_datetime(d['time'].str[:19]); hm=(t.dt.hour*100+t.dt.minute).values
    h,l,c,v=d.high,d.low,d.close,d.Volume
    up=h.diff(); dn=-l.diff(); pdm=np.where((up>dn)&(up>0),up,0); mdm=np.where((dn>up)&(dn>0),dn,0)
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1); rma=lambda x,n=14: pd.Series(x).ewm(alpha=1/n,adjust=False).mean()
    atr=rma(tr); dip=100*rma(pdm)/atr; dim=100*rma(mdm)/atr; adx=rma(100*(dip-dim).abs()/(dip+dim))
    aUp=100*(14-(h.rolling(15).apply(lambda x:14-np.argmax(x[::-1]),raw=True)))/14; aDn=100*(14-(l.rolling(15).apply(lambda x:14-np.argmin(x[::-1]),raw=True)))/14
    m=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean(); s=m.ewm(span=9,adjust=False).mean()
    dd=c.diff(); rsi=100-100/(1+dd.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()/(-dd.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean())
    mfm=np.where(h!=l,((c-l)-(h-c))/(h-l),0); cmf=(pd.Series(mfm)*v).rolling(20).sum()/v.rolling(20).sum()
    fi=(dd*v).ewm(span=13,adjust=False).mean(); e3=np.log(c.ewm(span=18,adjust=False).mean().ewm(span=18,adjust=False).mean().ewm(span=18,adjust=False).mean()); trix=10000*e3.diff(); ts=trix.ewm(span=9,adjust=False).mean()
    obv=(np.sign(dd).fillna(0)*v).cumsum(); e20=c.ewm(span=20,adjust=False).mean()
    V=[np.where(dip>dim,1,-1),np.where((aUp>70)&(aUp>aDn),1,np.where((aDn>70)&(aDn>aUp),-1,0)),np.where(m>s,1,-1),np.where(m>0,1,-1),np.where(rsi>50,1,-1),np.where(cmf>0,1,-1),np.where(fi>0,1,-1),np.where(trix>ts,1,-1),np.where(obv>obv.ewm(span=20,adjust=False).mean(),1,-1),np.where((c>e20)&(e20>e20.shift()),1,np.where((c<e20)&(e20<e20.shift()),-1,0))]
    bull=sum((x>0).astype(int) for x in V); bear=sum((x<0).astype(int) for x in V)
    # Parabolic SAR
    H,L,C=h.values,l.values,c.values; sar=np.zeros(len(d)); upT=True; af=.02; ep=H[0]; sar[0]=L[0]
    for i in range(1,len(d)):
        sv=sar[i-1]+af*(ep-sar[i-1])
        if upT:
            sv=min(sv,L[i-1],L[i-2] if i>1 else L[i-1])
            if L[i]<sv: upT=False; sv=ep; ep=L[i]; af=.02
            elif H[i]>ep: ep=H[i]; af=min(af+.02,.2)
        else:
            sv=max(sv,H[i-1],H[i-2] if i>1 else H[i-1])
            if H[i]>sv: upT=True; sv=ep; ep=H[i]; af=.02
            elif L[i]<ep: ep=L[i]; af=min(af+.02,.2)
        sar[i]=sv
    tr_=adx.values>=20; lo=tr_&(bull>=7)&(sar<C); so=tr_&(bear>=7)&(sar>C)
    ls=lo&~np.roll(lo,1); ss=so&~np.roll(so,1)
    a=None; out=[]; DT=d.date.values
    for i in range(1,len(d)):
        if a:
            stop=a['S']
            if hm[i]>=1600 or DT[i]!=a['day']: out.append((a,(C[i-1]-a['E'])*a['d']/a['r'])); a=None
            elif (L[i]<=stop if a['d']==1 else H[i]>=stop): out.append((a,(stop-a['E'])*a['d']/a['r'])); a=None
            else: a['S']=max(a['S'],sar[i]) if a['d']==1 else min(a['S'],sar[i])
        if a is None and 930<=hm[i]<1545 and (ls[i] or ss[i]):
            dr=1 if ls[i] else -1; r=abs(C[i]-sar[i])
            if r>0: a=dict(d=dr,E=C[i],S=sar[i],r=r,day=DT[i],date=DT[i])
    if out: add('Confluence (7/10 votes)',tk,[x[1]-cr(tk)*x[0]['E']/x[0]['r'] for x in out],[x[0]['date'] for x in out])
X=pd.DataFrame(R); X.to_pickle('work/SCORE.pkl')
g=X.groupby(['ind','tk']).net.agg(['mean','size'])
M=g['mean'].unstack().round(2); N=g['size'].unstack()
X['half']=np.where(X.date<'2026-09-01','a','b'); h=X.groupby(['ind','tk','half']).net.mean().unstack()
both=((h.a>0)&(h.b>0)).unstack()
print('AVG R PER TRADE AFTER COSTS (trades)'); print(M.to_string())
print('\nTRADES'); print(N.fillna(0).astype(int).to_string())
print('\nPOSITIVE IN BOTH HALVES'); print(both.fillna(False).astype(int).to_string())
