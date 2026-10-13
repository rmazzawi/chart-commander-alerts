# Farley Convergence: now vs VWAP filter; plus new Day High/Low reversal to VWAP. 2m data, all tickers.
import pandas as pd, numpy as np
TK=['AAPL','AMD','AMZN','GLD','IWM','META','MSFT','NVDA','QQQ','SPY','TSLA']
LIQ={'SPY','QQQ','IWM','AAPL','NVDA','TSLA','AMD','MSFT','META','AMZN'}
def prep(tk):
    d=pd.read_pickle(f'work/D_{tk}.pkl').copy().reset_index(drop=True)
    t=pd.to_datetime(d['time'].str[:19]); d['hm']=t.dt.hour*100+t.dt.minute
    h,l,c,o=d.high,d.low,d.close,d.open
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1); d['A']=tr.ewm(alpha=1/14,adjust=False).mean()
    return d
def run(d,tk,i,dr,E,S,T,kind):
    H,L,C,HM=d.high.values,d.low.values,d.close.values,d.hm.values; risk=abs(E-S)
    if risk<=0: return None
    R=None
    for j in range(i+1,len(d)):
        if HM[j]>=1600 or d.date.values[j]!=d.date.values[i]: R=dr*(C[j-1]-E)/risk; break
        if (L[j]<=S if dr==1 else H[j]>=S): R=-1.0; break
        if (H[j]>=T if dr==1 else L[j]<=T): R=abs(T-E)/risk; break
    if R is None: return None
    cost=(0.0002 if tk in LIQ else 0.0004)*E/risk
    return dict(tk=tk,kind=kind,d=dr,R=R,net=R-cost,hm=HM[i],rr=abs(T-E)/risk,date=d.date.values[i])
rows=[]
for tk in TK:
    d=prep(tk); h,l,c,o,A,V=d.high,d.low,d.close,d.open,d.A,d.VWAP
    ma20=c.rolling(20).mean(); ma50=c.rolling(50).mean(); sd=c.rolling(20).std(ddof=0); bbU=ma20+2*sd; bbL=ma20-2*sd
    swHi=h.rolling(50).max(); swLo=l.rolling(50).min()
    hb=h.rolling(50).apply(np.argmax,raw=True); lb=l.rolling(50).apply(np.argmin,raw=True); upLeg=hb>lb
    f38=np.where(upLeg,swHi-(swHi-swLo)*.382,swLo+(swHi-swLo)*.382); f50=(swHi+swLo)/2; f62=np.where(upLeg,swHi-(swHi-swLo)*.618,swLo+(swHi-swLo)*.618)
    step=np.where(c<10,.5,np.where(c<50,1,np.where(c<200,5,10))); rnd=np.round(c/step)*step
    gap=pd.Series(np.where(l>h.shift(),h.shift(),np.where(h<l.shift(),l.shift(),np.nan))).ffill()
    zone=0.5*A
    def hits(p): return sum(((lv-p).abs()<=zone).astype(int) for lv in [pd.Series(f38),f50,pd.Series(f62),pd.Series(rnd),ma20,ma50,bbL,bbU,gap])
    sh=hits(l); rh=hits(h)
    cl=upLeg&(sh>=3)&(c>o)&(c>l+(h-l)*.5)&((swHi-c)>=1.5*(c-(l-zone)))
    cs=(~upLeg)&(rh>=3)&(c<o)&(c<h-(h-l)*.5)&((c-swLo)>=1.5*((h+zone)-c))
    cl=cl&~cl.shift(fill_value=False); cs=cs&~cs.shift(fill_value=False)
    ent=(d.hm>=930)&(d.hm<1545)
    for i in np.where(cl&ent)[0]:
        r=run(d,tk,i,1,c[i],l[i]-zone[i],swHi[i],'conv');  r and rows.append({**r,'lv':sh[i],'vw_ok':c[i]>V[i]})
    for i in np.where(cs&ent)[0]:
        r=run(d,tk,i,-1,c[i],h[i]+zone[i],swLo[i],'conv'); r and rows.append({**r,'lv':rh[i],'vw_ok':c[i]<V[i]})
    # Day high/low reversal
    H,L,C,HM,DT,AA,VV=h.values,l.values,c.values,d.hm.values,d.date.values,A.values,V.values
    for N in (4,5,6):
        dh=dl=None; kh=kl=None; usedh=usedl=False
        for i in range(len(d)):
            if not(930<=HM[i]<1600): continue
            if dh is None or DT[i]!=DT[i-1] or HM[i]==930: dh,dl,kh,kl,usedh,usedl=H[i],L[i],i,i,False,False; continue
            if H[i]>dh: dh,kh,usedh=H[i],i,False
            if L[i]<dl: dl,kl,usedl=L[i],i,False
            if HM[i]>=1545: continue
            if not usedh and i-kh==N:
                usedh=True; E=C[i]; S=dh+0.1*AA[i]; T=VV[i]
                if E-T>=1.5*(S-E): r=run(d,tk,i,-1,E,S,T,f'dayrev{N}'); r and rows.append({**r,'vw_ok':True})
            if not usedl and i-kl==N:
                usedl=True; E=C[i]; S=dl-0.1*AA[i]; T=VV[i]
                if T-E>=1.5*(E-S): r=run(d,tk,i,1,E,S,T,f'dayrev{N}'); r and rows.append({**r,'vw_ok':True})
X=pd.DataFrame(rows); X.to_pickle('work/FARLEYVW.pkl')
def sm(Y,lab):
    pos=Y.groupby('tk').net.sum().gt(0).sum()
    return dict(version=lab,trades=len(Y),win=f"{(Y.R>0).mean()*100:.0f}%",avgR=round(Y.R.mean(),2),afterCost=round(Y.net.mean(),2),totalR=round(Y.net.sum(),1),tickersPos=f"{pos}/11",
                JulAug=round(Y[Y.date.astype(str)<'2026-09'].net.mean(),2),SepOct=round(Y[Y.date.astype(str)>='2026-09'].net.mean(),2))
C_=X[X.kind=='conv']; out=[sm(C_,'Convergence now'),sm(C_[C_.vw_ok],'Conv + VWAP filter'),sm(C_[~C_.vw_ok],'  (removed by filter)'),sm(C_[C_.vw_ok&(C_.lv>=4)],'Conv + VWAP, 4+ levels')]
for N in (4,5,6):
    Y=X[X.kind==f'dayrev{N}']; out+= [sm(Y,f'DayRev {N} candles'),sm(Y[Y.hm>=1000],f'DayRev {N}, after 10:00'),sm(Y[Y.hm>=1030],f'DayRev {N}, after 10:30')]
print(pd.DataFrame(out).to_string(index=False))
Y=X[(X.kind=='dayrev5')&(X.hm>=1000)]; print('\nDayRev5 after 10:00 calls vs puts:'); print(Y.groupby('d').agg(n=('R','size'),win=('R',lambda r:(r>0).mean()),net=('net','mean')).round(2))
print('\nDayRev5 after 10:00 per ticker:'); print(Y.groupby('tk').agg(n=('R','size'),net=('net','sum')).round(1).T.to_string())
print('avg target/stop', X[X.kind!='conv'].rr.median().round(2))
