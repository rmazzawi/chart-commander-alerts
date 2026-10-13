# Scorecard part 2: Nison, Rayner, Uni Flag on the same 2m data (adds to work/SCORE.pkl -> work/SCORE2.pkl)
import pandas as pd, numpy as np
LIQ={'SPY','QQQ','IWM','AAPL','NVDA','TSLA','AMD','MSFT','META','AMZN'}
TK=['AAPL','AMD','AMZN','GLD','IWM','META','MSFT','NVDA','QQQ','SPY','TSLA']
cr=lambda tk:0.0002 if tk in LIQ else 0.0004
def load(tk):
    d=pd.read_pickle(f'work/D_{tk}.pkl').reset_index(drop=True); t=pd.to_datetime(d['time'].str[:19]); d['hm']=t.dt.hour*100+t.dt.minute
    h,l,c=d.high,d.low,d.close; tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1); d['A']=tr.ewm(alpha=1/14,adjust=False).mean(); return d
def seq(d,tk,sig,name,lo=930,hi=1545):
    """sig: array of (dir,stop) per bar or None; entry at close, target 2R, stop / 2R / 4PM, one trade at a time"""
    H,L,C,HM,DT=d.high.values,d.low.values,d.close.values,d.hm.values,d.date.values; a=None; out=[]
    for i in range(1,len(d)):
        if a:
            if HM[i]>=1600 or DT[i]!=a['day']: out.append((a,(C[i-1]-a['E'])*a['d']/a['r'])); a=None
            elif (L[i]<=a['S'] if a['d']==1 else H[i]>=a['S']): out.append((a,-1.0)); a=None
            elif (H[i]>=a['T'] if a['d']==1 else L[i]<=a['T']): out.append((a,2.0)); a=None
        if a is None and lo<=HM[i]<hi and sig[i] is not None:
            dr,S=sig[i]; r=(C[i]-S)*dr
            if r>0: a=dict(d=dr,E=C[i],S=S,T=C[i]+dr*2*r,r=r,day=DT[i])
    return [dict(ind=name,tk=tk,net=R-cr(tk)*x['E']/x['r'],date=pd.Timestamp(x['day'])) for x,R in out]
S=lambda x,i=1: x.shift(i).fillna(False).astype(bool)
rows=[]
for tk in TK:
    d=load(tk); o,h,l,c,A=d.open,d.high,d.low,d.close,d.A
    body=(c-o).abs(); rng=h-l; upW=h-np.maximum(o,c); loW=np.minimum(o,c)-l; bu=c>o; be=c<o
    # ---------- Nison ----------
    avgB=body.rolling(14).mean(); isL=lambda i: body.shift(i)>avgB.shift(i)*1.2; ma=c.rolling(10).mean()
    up=(c>ma)&(ma>ma.shift(3)); dn=(c<ma)&(ma<ma.shift(3)); doji=(rng>0)&(body<=rng*0.1)
    bEng=S(dn)&S(be)&bu&(c>o.shift())&(o<c.shift())&(body>body.shift()); sEng=S(up)&S(bu)&be&(c<o.shift())&(o>c.shift())&(body>body.shift())
    bDS=S(dn)&S(be)&isL(1)&doji&(np.maximum(o,c)<c.shift()); sDS=S(up)&S(bu)&isL(1)&doji&(np.minimum(o,c)>c.shift())
    mDS=S(dn,2)&S(be,2)&isL(2)&S(doji)&(np.maximum(o,c).shift()<c.shift(2))&bu&(c>(o.shift(2)+c.shift(2))/2)
    eDS=S(up,2)&S(bu,2)&isL(2)&S(doji)&(np.minimum(o,c).shift()>c.shift(2))&be&(c<(o.shift(2)+c.shift(2))/2)
    lo3=l.rolling(3).min(); hi3=h.rolling(3).max()
    for conf,nm in [(True,'Nison (default, confirm ON)'),(False,'Nison confirm OFF')]:
        bC=(S(bDS)&bu&(c>h.shift())) if conf else bDS; sC=(S(sDS)&be&(c<l.shift())) if conf else sDS
        bs=(bEng|bC|mDS).values; ss=(sEng|sC|eDS).values
        sig=[(1,lo3[i]) if bs[i] else (-1,hi3[i]) if ss[i] else None for i in range(len(d))]
        rows+=seq(d,tk,sig,nm)
    # ---------- Rayner ----------
    ma50=c.rolling(50).mean(); upT=(c>ma50)&(ma50>ma50.shift(5)); dnT=(c<ma50)&(ma50<ma50.shift(5)); pos=np.where(rng>0,(c-l)/rng,0.5)
    sup=l.rolling(20).min().shift(2); res=h.rolling(20).max().shift(2); n=0.75*A
    atS=((l-sup).abs()<=n)|((l-ma50).abs()<=n)|((l.shift()-ma50).abs()<=n); atR=((h-res).abs()<=n)|((h-ma50).abs()<=n)|((h.shift()-ma50).abs()<=n)
    ham=(upW<=body)&(pos>=.75)&(loW>=2*body)&(body>0); ss_=(loW<=body)&(pos<=.25)&(upW>=2*body)&(body>0)
    bE=S(be)&bu&(c>=o.shift())&(o<=c.shift()); sE=S(bu)&be&(c<=o.shift())&(o>=c.shift())
    pier=S(be)&bu&(c>(o.shift()+c.shift())/2)&(c<o.shift()); dark=S(bu)&be&(c<(o.shift()+c.shift())/2)&(c>o.shift())
    tB=(loW.shift()>body.shift())&((l-l.shift()).abs()<=A*.1)&bu; tT=(upW.shift()>body.shift())&((h-h.shift()).abs()<=A*.1)&be
    mS=S(be,2)&(rng.shift()<rng.shift(2)*.5)&bu&(c>c.shift(2)+(o.shift(2)-c.shift(2))*.5); eS=S(bu,2)&(rng.shift()<rng.shift(2)*.5)&be&(c<c.shift(2)-(c.shift(2)-o.shift(2))*.5)
    bull=ham|bE|mS|pier|tB; bear=ss_|sE|eS|dark|tT
    big=(rng>rng.rolling(5).max().shift())|(np.maximum(rng,rng.shift())>rng.rolling(5).max().shift(2))
    rL=S(upT,2)&bull&atS&big; rS=S(dnT,2)&bear&atR&big   # (book code: upTrend[2] for longs, as written in the script)
    boU=(c>h.rolling(20).max().shift())&(c.shift()<=h.rolling(20).max().shift(2)); boD=(c<l.rolling(20).min().shift())&(c.shift()>=l.rolling(20).min().shift(2))
    rbU=boU.astype(int).rolling(11).max()>0; rbD=boD.astype(int).rolling(11).max()>0
    ab14=body.rolling(14).mean()
    r3=S(bu,4)&(body.shift(4)>ab14.shift(4))&(pd.concat([h.shift(1),h.shift(2),h.shift(3)],axis=1).max(axis=1)<=h.shift(4))&(pd.concat([l.shift(1),l.shift(2),l.shift(3)],axis=1).min(axis=1)>=l.shift(4))&bu&(c>h.shift(4))
    f3=S(be,4)&(body.shift(4)>ab14.shift(4))&(pd.concat([h.shift(1),h.shift(2),h.shift(3)],axis=1).max(axis=1)<=h.shift(4))&(pd.concat([l.shift(1),l.shift(2),l.shift(3)],axis=1).min(axis=1)>=l.shift(4))&be&(c<l.shift(4))
    bH=S(bu)&(h<h.shift())&(l>l.shift())&(body<body.shift()*.5); sH=S(be)&(h<h.shift())&(l>l.shift())&(body<body.shift()*.5)
    cL=rbU&(r3|(S(bH)&(h>h.shift()))); cS=rbD&(f3|(S(sH)&(l<l.shift())))
    for ur,uc,nm in [(1,1,'Rayner (default, both ON)'),(1,0,'Rayner reversal only'),(0,1,'Rayner continuation only')]:
        L_=((rL&bool(ur))|(cL&bool(uc))).values; S_=((rS&bool(ur))|(cS&bool(uc))).values
        sig=[(1,lo3[i]-.1*A[i]) if L_[i] else (-1,hi3[i]+.1*A[i]) if S_[i] else None for i in range(len(d))]
        rows+=seq(d,tk,sig,nm)
    # ---------- Uni Flag (2m, 9:45-15:30, entry next open, stop pullback, 2R, 8EMA exit, BE at 1R, flat 4PM) ----------
    e8=c.ewm(span=8,adjust=False).mean(); s20=c.rolling(20).mean()
    bsh=h.rolling(15).apply(lambda x:14-np.argmax(x),raw=True); bsl=l.rolling(15).apply(lambda x:14-np.argmax(-x),raw=True)
    pbL=l.rolling(5).min(); pbH=h.rolling(5).max()
    bF=(bsh>=2)&(bsh<=5)&(pbL>s20-.25*A)&(e8>s20)&(s20>s20.shift(3)); sF=(bsl>=2)&(bsl<=5)&(pbH<s20+.25*A)&(e8<s20)&(s20<s20.shift(3))
    lS=(S(bF)&(h>h.shift())&(c>e8)).values; sS=(S(sF)&(l<l.shift())&(c<e8)).values
    O,H,L,C,HM,DT,E8,PL,PH,AA=o.values,h.values,l.values,c.values,d.hm.values,d.date.values,e8.values,pbL.values,pbH.values,A.values
    for ema_x,be_,nm in [(1,1,'Uni Flag (default: 8EMA exit + BE)'),(0,1,'Uni Flag no 8EMA exit'),(1,0,'Uni Flag no break-even'),(0,0,'Uni Flag plain 2R')]:
        a=None; pend=None; out=[]
        for i in range(1,len(d)):
            if pend and a is None:
                if DT[i]==pend['day'] and HM[i]<1600:
                    E=O[i]; r=(E-pend['S'])*pend['d']
                    if r>0: a=dict(d=pend['d'],E=E,S=pend['S'],S0=pend['S'],T=E+pend['d']*2*r,r=r,day=DT[i],i=i)
                pend=None
            if a:
                dr=a['d']; R=None
                if HM[i]>=1600 or DT[i]!=a['day']: R=(C[i-1]-a['E'])*dr/a['r']
                elif (L[i]<=a['S'] if dr==1 else H[i]>=a['S']): R=(a['S']-a['E'])*dr/a['r']
                elif (H[i]>=a['T'] if dr==1 else L[i]<=a['T']): R=2.0
                elif ema_x and i>a['i'] and (C[i]<E8[i] if dr==1 else C[i]>E8[i]): R=(C[i]-a['E'])*dr/a['r']
                if R is None and be_ and (H[i]>=a['E']+a['r'] if dr==1 else L[i]<=a['E']-a['r']): a['S']=a['E']
                if R is not None: out.append((a,R)); a=None; continue
            if a is None and pend is None and 945<=HM[i]<=1530:
                if lS[i]: pend=dict(d=1,S=PL[i]-.1*AA[i],day=DT[i])
                elif sS[i]: pend=dict(d=-1,S=PH[i]+.1*AA[i],day=DT[i])
        rows+=[dict(ind=nm,tk=tk,net=R-cr(tk)*x['E']/x['r'],date=pd.Timestamp(x['day'])) for x,R in out]
X=pd.concat([pd.read_pickle('work/SCORE.pkl'),pd.DataFrame(rows)]); X.to_pickle('work/SCORE2.pkl')
Y=pd.DataFrame(rows); print(Y.groupby(['ind','tk']).net.mean().unstack().round(2).to_string()); print(Y.groupby(['ind','tk']).size().unstack().to_string())
