# Scorecard part 3: Liquidity Sweeps (swing old/equal highs-lows + previous day high/low; 4H/week/month levels left out)
import pandas as pd, numpy as np
exec(open('analysis/scorecard2.py').read().split('rows=[]')[0])
rows=[]
for tk in TK:
    d=load(tk); t=pd.to_datetime(d['time'].str[:19]); O,H,L,C,A,HM,DT=d.open.values,d.high.values,d.low.values,d.close.values,d.A.values,d.hm.values,d.date.values
    # 1h 200 EMA trend, previous completed hour (like request.security [1])
    hr=d.set_index(t).close.resample('60min').last().dropna(); e=hr.ewm(span=200,adjust=False).mean()
    eNow=e.shift(1).reindex(t.dt.floor('60min')).values; ePrev=e.shift(2).reindex(t.dt.floor('60min')).values
    tUp=(C>eNow)&(eNow>=ePrev); tDn=(C<eNow)&(eNow<=ePrev)
    pdh=d['Prior-day high'].values; pdl=d['Prior-day low'].values
    for useT,nm in [(True,'LiqSweeps (default, trend ON)'),(False,'LiqSweeps trend OFF')]:
        hiP=[]; loP=[]; bear=bull=None; a=None; out=[]; doneH=doneL=None
        for i in range(10,len(d)):
            # pivots confirmed 5 bars later
            j=i-5
            if H[j]==H[j-5:j+6].max(): hiP.append(H[j]); hiP=hiP[-15:]
            if L[j]==L[j-5:j+6].min(): loP.append(L[j]); loP=loP[-15:]
            hs=False; ls=False
            for p in list(hiP):
                if H[i]>p: hiP.remove(p); hs|= C[i]<p
            for p in list(loP):
                if L[i]<p: loP.remove(p); ls|= C[i]>p
            if doneH!=DT[i] and not np.isnan(pdh[i]) and H[i]>pdh[i]: doneH=DT[i]; hs|=C[i]<pdh[i]
            if doneL!=DT[i] and not np.isnan(pdl[i]) and L[i]<pdl[i]: doneL=DT[i]; ls|=C[i]>pdl[i]
            aS=(not useT) or tDn[i]; aB=(not useT) or tUp[i]
            bS=hs and aS; bB=ls and aB
            body=abs(C[i]-O[i]); rg=H[i]-L[i]; strong=body>=A[i]*.8 and rg>0 and body/rg>=.6
            sellOk= (not bS) and bear and i-bear['i']<=5 and strong and C[i]<O[i] and C[i]<bear['lvl'] and aS
            buyOk = (not bB) and bull and i-bull['i']<=5 and strong and C[i]>O[i] and C[i]>bull['lvl'] and aB
            # manage trade
            if a:
                if HM[i]>=1600 or DT[i]!=a['day']: out.append((a,(C[i-1]-a['E'])*a['d']/a['r'])); a=None
                elif (L[i]<=a['S'] if a['d']==1 else H[i]>=a['S']): out.append((a,-1.0)); a=None
                elif (H[i]>=a['T'] if a['d']==1 else L[i]<=a['T']): out.append((a,2.0)); a=None
            if a is None and 930<=HM[i]<1545 and (sellOk or buyOk):
                dr=-1 if sellOk else 1; S_=bear['top'] if sellOk else bull['bot']; r=(C[i]-S_)*dr
                if r>0: a=dict(d=dr,E=C[i],S=S_,T=C[i]+dr*2*r,r=r,day=DT[i])
            if bS: bear=dict(i=i,lvl=L[i],top=H[i])
            if bB: bull=dict(i=i,lvl=H[i],bot=L[i])
            if bear and H[i]>bear['top']: bear=None
            if bull and L[i]<bull['bot']: bull=None
            if bear and (sellOk or i-bear['i']>5): bear=None
            if bull and (buyOk or i-bull['i']>5): bull=None
        rows+=[dict(ind=nm,tk=tk,net=R-cr(tk)*x['E']/x['r'],date=pd.Timestamp(x['day'])) for x,R in out]
X=pd.concat([pd.read_pickle('work/SCORE2.pkl'),pd.DataFrame(rows)]); X.to_pickle('work/SCORE3.pkl')
Y=pd.DataFrame(rows); print(Y.groupby(['ind','tk']).net.mean().unstack().round(2).to_string()); print(Y.groupby(['ind','tk']).size().unstack().to_string())
