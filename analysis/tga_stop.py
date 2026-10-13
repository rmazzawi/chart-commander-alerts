# TGA Patterns: does skipping trades with a big stop help? Replicates the Pine box logic on 2m data.
import pandas as pd, numpy as np, sys
TK = ['AAPL','AMD','AMZN','GLD','IWM','META','MSFT','NVDA','QQQ','SPY','TSLA']
LIQ = {'SPY','QQQ','IWM','AAPL','NVDA','TSLA','AMD','MSFT','META','AMZN'}

def rsi(c, n=14):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100/(1+u/v)

def prep(tk):
    d = pd.read_pickle(f'work/D_{tk}.pkl').copy()
    t = pd.to_datetime(d['time'].str[:19]); d['hm'] = t.dt.hour*100 + t.dt.minute; d['dt'] = t
    o,h,l,c = d.open,d.high,d.low,d.close
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    d['A'] = tr.ewm(alpha=1/14, adjust=False).mean()
    sma50 = c.rolling(50).mean(); m = c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean(); s = m.ewm(span=9,adjust=False).mean()
    r = rsi(c); vw = d['VWAP']
    d['bs'] = (c>sma50).astype(int)+(m>s)+(r<70)+(c>vw); d['ss'] = (c<sma50).astype(int)+(m<s)+(r>30)+(c<vw)
    body=(c-o).abs(); rng=h-l; upW=h-np.maximum(o,c); loW=np.minimum(o,c)-l; ab=body.rolling(14).mean()
    bu=c>o; be=c<o; s10=c.rolling(10).mean(); dn=(c<s10)&(s10<s10.shift(3)); up=(c>s10)&(s10>s10.shift(3))
    LB=lambda i: body.shift(i)>ab.shift(i); SB=lambda i: body.shift(i)<ab.shift(i)*0.5; S=lambda x,i: x.shift(i).fillna(False).astype(bool)
    ham = dn&(loW>=2*body)&(upW<=body*0.5)&(rng>0)&(body>0)
    beng = S(dn,1)&S(be,1)&bu&(c>=o.shift())&(o<=c.shift())&(body>body.shift())
    ms = S(dn,2)&S(be,2)&LB(2)&SB(1)&bu&(c>(o.shift(2)+c.shift(2))/2)
    tw = bu&S(bu,1)&S(bu,2)&LB(0)&LB(1)&LB(2)&(c>c.shift())&(c.shift()>c.shift(2))&(o>o.shift())&(o.shift()>o.shift(2))&S(dn,3)
    hm_ = up&(loW>=2*body)&(upW<=body*0.5)&(rng>0)&(body>0)
    ss_ = up&(upW>=2*body)&(loW<=body*0.5)&(rng>0)&(body>0)
    beg = S(up,1)&S(bu,1)&be&(o>=c.shift())&(c<=o.shift())&(body>body.shift())
    es = S(up,2)&S(bu,2)&LB(2)&SB(1)&be&(c<(o.shift(2)+c.shift(2))/2)
    tc = be&S(be,1)&S(be,2)&LB(0)&LB(1)&LB(2)&(c<c.shift())&(c.shift()<c.shift(2))&S(up,3)
    d['bn'] = np.select([ham,beng,ms,tw],['Hammer','Bull Engulfing','Morning Star','3 White Soldiers'],'')
    d['sn'] = np.select([hm_,ss_,beg,es,tc],['Hanging Man','Shooting Star','Bear Engulfing','Evening Star','3 Black Crows'],'')
    return d

def sim(d, tk):
    out=[]; a=None; pL=pS=None
    O,H,L,C,A,HM,DT=[d[k].values for k in ['open','high','low','close','A','hm','date']]
    bs,ss,bn,sn=d.bs.values,d.ss.values,d.bn.values,d.sn.values; T=d.dt.values
    for i in range(1,len(d)):
        rth = 930<=HM[i]<1600; ent = 930<=HM[i]<1545; newday = DT[i]!=DT[i-1]
        if a and i>a['i']:
            hs = L[i]<=a['S'] if a['d']==1 else H[i]>=a['S']; ht = H[i]>=a['T'] if a['d']==1 else L[i]<=a['T']
            if hs or ht: a['R'] = -1.0 if hs else 2.0; out.append(a); a=None
        if a and (not rth or newday):
            a['R'] = a['d']*(C[i-1 if newday else i]-a['E'])/a['risk']; out.append(a); a=None
        if not ent or newday: pL=pS=None
        mins = lambda: (T[i]-a['t'])/np.timedelta64(1,'m')
        canL = a is None or a['d']==-1 or mins()>=30; canS = a is None or a['d']==1 or mins()>=30
        trL = ent and canL and pL and i<=pL['i']+2 and H[i]>=pL['trig']
        trS = ent and canS and pS and i<=pS['i']+2 and L[i]<=pS['trig'] and not trL
        for tr,p,dr in ((trL,pL,1),(trS,pS,-1)):
            if tr:
                if a: a['R']=a['d']*(O[i]-a['E'])/a['risk']; out.append(a)
                E = max(O[i],p['trig']) if dr==1 else min(O[i],p['trig']); risk=abs(E-p['stop'])
                a=dict(tk=tk,d=dr,i=i,t=T[i],E=E,S=p['stop'],T=E+dr*2*risk,risk=risk,atr=p['atr'],hm=p['hm'],name=p['name'],date=DT[i])
        if trL: pL=None
        if trS: pS=None
        if pL and i>=pL['i']+2: pL=None
        if pS and i>=pS['i']+2: pS=None
        if ent and bn[i] and bs[i]>=3: pL=dict(i=i,trig=H[i],stop=L[i]-0.1*A[i],atr=A[i],hm=HM[i],name=bn[i])
        if ent and sn[i] and ss[i]>=3: pS=dict(i=i,trig=L[i],stop=H[i]+0.1*A[i],atr=A[i],hm=HM[i],name=sn[i])
    return out

rows=[]
for tk in TK:
    try: d=prep(tk)
    except FileNotFoundError: continue
    rows+=sim(d,tk)
X=pd.DataFrame(rows); X['ratio']=X.risk/X.atr; X['cost']=np.where(X.tk.isin(LIQ),0.0002,0.0004)*X.E/X.risk; X['net']=X.R-X.cost
X.to_pickle('work/TGASTOP.pkl')
def summ(Y,lab):
    return dict(version=lab,trades=len(Y),win=f"{(Y.R>0).mean()*100:.0f}%",avgR=round(Y.R.mean(),3),netR=round(Y.net.mean(),3),totalNetR=round(Y.net.sum(),1),avgStop=f"${Y.risk.mean():.2f}",bigStop=f"${Y.risk.max():.2f}")
V=[summ(X,'Now (no limit)')]
for k in [2.5,2.0,1.5,1.0]: V.append(summ(X[X.ratio<=k],f'Skip if stop > {k} ATR'))
V.append(summ(X[X.hm>=940],'No signals first 10 min'))
print(pd.DataFrame(V).to_string(index=False))
print('\nStop size in ATR: median %.2f, 75%% %.2f, 90%% %.2f' % tuple(X.ratio.quantile([.5,.75,.9])))
print('\nSkipped trades (stop > 1.5 ATR):'); Z=X[X.ratio>1.5]; print(Z.groupby('name').agg(n=('R','size'),avgR=('R','mean'),net=('net','mean')).round(2))
print('\nPer ticker, now vs skip >1.5 ATR (total net R):')
print(pd.DataFrame({'now':X.groupby('tk').net.sum(),'skip>1.5':X[X.ratio<=1.5].groupby('tk').net.sum(),'n_now':X.groupby('tk').size(),'n_skip':X[X.ratio<=1.5].groupby('tk').size()}).round(1))
print('\nDollar result per trade if each trade risks the same $100:')
for lab,Y in [('now',X),('skip>1.5',X[X.ratio<=1.5])]: print(lab, round(Y.net.mean()*100,1))
print('\nDates', X.date.min(), X.date.max())
