# Confluence: A) no entries before 9:45, B) skip trades whose SAR stop is wider than k x ATR. 5m (13 tickers) and 2m (11).
import pandas as pd, numpy as np, sys
DIR=sys.argv[1]; TK=sys.argv[2].split(',')
LIQ={'SPY','QQQ','IWM','AAPL','NVDA','TSLA','AMD','MSFT','META','AMZN','GOOGL'}
cr=lambda tk:0.0002 if tk in LIQ else 0.0004
R=[]
def add(name,tk,net,date):
    for n,dd in zip(net,date): R.append(dict(ind=name,tk=tk,net=n,date=pd.Timestamp(dd)))
load_=lambda tk: pd.read_pickle(f'{DIR}/D_{tk}.pkl')
def conf(tk,START,MAXK,NAME):
    d=load_(tk)
    d=d.reset_index(drop=True); t=pd.to_datetime(d['time'].str[:19]); hm=(t.dt.hour*100+t.dt.minute).values
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
        if a is None and START<=hm[i]<1545 and (ls[i] or ss[i]):
            dr=1 if ls[i] else -1; r=abs(C[i]-sar[i])
            if r>0 and r<=MAXK*atr.values[i]: a=dict(d=dr,E=C[i],S=sar[i],r=r,day=DT[i],date=DT[i])
    if out: add(NAME,tk,[x[1]-cr(tk)*x[0]['E']/x[0]['r'] for x in out],[x[0]['date'] for x in out])

V=[('Now',930,99),('A: start 9:45',945,99),('B: stop <= 2 ATR',930,2),('B: stop <= 1.5 ATR',930,1.5),('B: stop <= 1 ATR',930,1),('A+B: 9:45 and <= 1.5 ATR',945,1.5)]
for tk in TK:
    for nm,st,k in V: conf(tk,st,k,nm)
X=pd.DataFrame(R); mid=X.date.quantile(.5)
out=[]
for nm,_,_ in V:
    Y=X[X.ind==nm]; t=Y.groupby('tk').net.mean()
    out.append(dict(version=nm,trades=len(Y),win=f"{(Y.net>0).mean()*100:.0f}%",perTrade=round(Y.net.mean(),3),totalR=round(Y.net.sum(),0),tickersPos=f"{(t>0).sum()}/{len(t)}",first=round(Y[Y.date<mid].net.mean(),2),second=round(Y[Y.date>=mid].net.mean(),2),worst=round(Y.net.min(),1)))
print(pd.DataFrame(out).to_string(index=False))
print(X.pivot_table(index='ind',columns='tk',values='net',aggfunc='mean').round(2).loc[[v[0] for v in V]].to_string())
