import pandas as pd, numpy as np
F=pd.read_pickle('S2day2.pkl')  # S2 features (has s400)
A=pd.read_pickle('F.pkl'); A=A[A.t>='2026-07-27']
# new baseline: drop S2 trades against SMA400
keep=~A.index.isin(F[F.s400<=0].index) if False else None
A=A.merge(F[['tk','t','s400']],on=['tk','t'],how='left')
A=A[~((A.s==2)&(A.s400<=0))].copy()
A['per']=np.where(A.t>='2026-09-04','late','early')
D={tk:pd.read_pickle(f'D_{tk}.pkl') for tk in A.tk.unique()}
def sim(x,tgt=None,t1=None,tmax=None,be=True):
    d=D[x.tk]; e=x.entry; dr=x.dir; risk=abs(e-x.stop); st=x.stop
    if risk<=0: return 0
    half=False; got=0
    for j in range(x.i+1,min(x.i+200,len(d))):
        r=d.iloc[j]; tm=r.t.time()
        hi,lo=(r.high,r.low) if dr==1 else (-r.low,-r.high); E=e*dr; S=st*dr
        if lo<=S: return (got+(S-E)*(0.5 if half else 1))/risk
        if t1 and not half and hi>=E+t1*risk: half=True; got=0.5*t1*risk; st=e if be else st
        if tgt and hi>=E+tgt*risk: return (got+tgt*risk*(0.5 if half else 1))/risk
        if (tmax and j-x.i>=tmax) or tm>=pd.Timestamp('15:44').time():
            return (got+(r.close*dr-E)*(0.5 if half else 1))/risk
    return got/risk
V={'current':None,'1R all':dict(tgt=1),'1.5R all':dict(tgt=1.5),'2R all':dict(tgt=2),
   'half@1R,rest@2R':dict(t1=1,tgt=2),'half@1R,rest@3R':dict(t1=1,tgt=3),'half@0.75R,rest@2R':dict(t1=0.75,tgt=2),
   '1R, 30min time stop':dict(tgt=1,tmax=15)}
for k,v in V.items():
    A[k]=A.R if v is None else A.apply(lambda x:sim(x,**v),axis=1)
A.to_pickle('SIM.pkl')
print(A.groupby('per')[list(V)].sum().round(1).T)
print(A.groupby(['s'])[list(V)].sum().round(1).T)
