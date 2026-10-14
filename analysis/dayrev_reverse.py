# Day Rev: normal vs REVERSED (trade the other way) vs normal + trend block. 2m, 11 tickers, one trade at a time.
import pandas as pd, numpy as np
exec(open('analysis/farley_range.py').read().split("o=[]\n")[0])
def dmi(d):
    h,l,c=d.high,d.low,d.close; up=h.diff(); dn=-l.diff()
    pdm=pd.Series(np.where((up>dn)&(up>0),up,0)); mdm=pd.Series(np.where((dn>up)&(dn>0),dn,0))
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1); r=lambda x:x.ewm(alpha=1/14,adjust=False).mean()
    a=r(tr); dp=100*r(pdm)/a; dm=100*r(mdm)/a; return r(100*(dp-dm).abs()/(dp+dm)).values, dp.values, dm.values
def run(mode):
    out=[]
    for tk,(d,sig) in SIGS.items():
        adx,dp,dm=dmi(d); H,L,C,HM,DT=d.high.values,d.low.values,d.close.values,d.hm.values,d.date.values
        sig={x[0]:x for x in sig if x[5]=='dayrev'}; a=None
        for i in range(len(d)):
            if a and i>a['i']:
                if HM[i]>=1600 or DT[i]!=a['day']: out.append((tk,a,a['d']*(C[i-1]-a['E'])/a['r'])); a=None
                elif (L[i]<=a['S'] if a['d']==1 else H[i]>=a['S']): out.append((tk,a,-1.0)); a=None
                elif (H[i]>=a['T'] if a['d']==1 else L[i]<=a['T']): out.append((tk,a,abs(a['T']-a['E'])/a['r'])); a=None
            x=sig.get(i)
            if x and a is None:
                _,dr,E,S,T,_k=x; r=abs(E-S)
                against = adx[i]>=20 and ((dr==1 and dm[i]>dp[i]) or (dr==-1 and dp[i]>dm[i]))
                if mode=='normal': a=dict(d=dr,E=E,S=S,T=T,r=r,i=i,day=DT[i])
                elif mode=='block' and not against: a=dict(d=dr,E=E,S=S,T=T,r=r,i=i,day=DT[i])
                elif mode=='reverse': a=dict(d=-dr,E=E,S=E+dr*r,T=E-dr*2*r,r=r,i=i,day=DT[i])
                elif mode=='reverse_trend' and against: a=dict(d=-dr,E=E,S=E+dr*r,T=E-dr*2*r,r=r,i=i,day=DT[i])
    Y=pd.DataFrame([dict(tk=t,R=R,net=R-(0.0002 if t in LIQ else 0.0004)*a['E']/a['r'],date=str(a['day'])) for t,a,R in out])
    pos=(Y.groupby('tk').net.mean()>0).sum()
    return dict(version=mode,trades=len(Y),win=f"{(Y.R>0).mean()*100:.0f}%",beforeCost=round(Y.R.mean(),2),afterCost=round(Y.net.mean(),2),totalR=round(Y.net.sum(),0),tickersPos=f"{pos}/11",JulAug=round(Y[Y.date<'2026-09'].net.mean(),2),SepOct=round(Y[Y.date>='2026-09'].net.mean(),2))
print(pd.DataFrame([run(m) for m in ['normal','block','reverse','reverse_trend']]).to_string(index=False))
