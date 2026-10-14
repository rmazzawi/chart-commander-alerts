# Auto-switch test (2m, 11 tickers): live "day type" at each candle -> TREND: Confluence only, in trend direction, no box limit;
# RANGE: Day Rev only. Compared with each tool alone.  TREND = ADX>=25 AND last 20 candles closed on the same side of VWAP AND |close-VWAP| >= 1 ATR
import pandas as pd, numpy as np, sys
exec(open('analysis/dayrev_reverse.py').read().split("print(pd.DataFrame")[0])
src=open('analysis/conf_ab.py').read(); g={}; sys.argv=['x','work',','.join(SIGS)]; exec(src[:src.rindex("V=[")],g)
def regime(d):
    adx,dp,dm=dmi(d); c=d.close.values; vw=d.VWAP.values; A=d.A.values
    side=np.sign(c-vw); s=pd.Series(side).rolling(20).apply(lambda x: x[0] if (x==x[0]).all() else 0,raw=True).values
    return np.where((adx>=25)&(np.abs(c-vw)>=A)&(s!=0),s,0)   # +1 trend up, -1 trend down, 0 range
rows=[]
for tk,(d,sig) in SIGS.items():
    reg=regime(d); H,L,C,HM,DT=d.high.values,d.low.values,d.close.values,d.hm.values,d.date.values
    cr=0.0002 if tk in LIQ else 0.0004
    # Day Rev (as in the script) with / without the range-only rule
    for name,keep in [('Day Rev alone',lambda i,dr:True),('Day Rev, RANGE days only',lambda i,dr:reg[i]==0)]:
        S={x[0]:x for x in sig if x[5]=='dayrev'}; a=None
        for i in range(len(d)):
            if a and i>a['i']:
                R=None
                if HM[i]>=1600 or DT[i]!=a['day']: R=a['d']*(C[i-1]-a['E'])/a['r']
                elif (L[i]<=a['S'] if a['d']==1 else H[i]>=a['S']): R=-1.0
                elif (H[i]>=a['T'] if a['d']==1 else L[i]<=a['T']): R=abs(a['T']-a['E'])/a['r']
                if R is not None: rows.append(dict(v=name,tk=tk,net=R-cr*a['E']/a['r'],date=str(a['day']))); a=None
            x=S.get(i)
            if x and a is None and keep(i,x[1]):
                _,dr,E,St,T,_k=x; a=dict(d=dr,E=E,S=St,T=T,r=abs(E-St),i=i,day=DT[i])
    # Confluence alone vs TREND-only in trend direction (no box limit)
    for name,flt in [('Confluence alone',None),('Confluence, TREND days, with trend only',reg)]:
        g['R'].clear(); 
        if flt is None: g['conf'](tk,930,99,'x')
        else:
            # filter: only signals where regime == direction
            body=src[src.index('def conf'):src.rindex('V=[')].replace('def conf(tk,START,MAXK,NAME):','def conf2(tk,START,MAXK,NAME,REG):').replace("if r>0 and r<=MAXK*atr.values[i]:","if r>0 and r<=MAXK*atr.values[i] and REG[i]==dr:")
            exec(body,g); g['conf2'](tk,930,99,'x',flt)
        for r in g['R']: rows.append(dict(v=name,tk=tk,net=r['net'],date=str(r['date'].date())))
X=pd.DataFrame(rows)
comb=X[X.v.isin(['Day Rev, RANGE days only','Confluence, TREND days, with trend only'])].assign(v='AUTO-SWITCH (both combined)')
X=pd.concat([X,comb])
def sm(Y):
    t=Y.groupby('tk').net.mean()
    return pd.Series(dict(trades=len(Y),win=f"{(Y.net>0).mean()*100:.0f}%",perTrade=round(Y.net.mean(),2),totalR=round(Y.net.sum()),tickersPos=f"{(t>0).sum()}/11",JulAug=round(Y[Y.date<'2026-09'].net.mean(),2),SepOct=round(Y[Y.date>='2026-09'].net.mean(),2)))
print(X.groupby('v').apply(sm).to_string())
print(X[X.v=='AUTO-SWITCH (both combined)'].groupby('tk').net.agg(['size','mean','sum']).round(2).T.to_string())
d0=list(SIGS.values())[0][0]; reg=regime(d0); print('share of candles in TREND mode (first ticker):',round((reg!=0)[(d0.hm>=930)&(d0.hm<1600)].mean(),2))
