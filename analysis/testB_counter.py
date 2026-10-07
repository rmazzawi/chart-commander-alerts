# Test B (10/7): block trades AGAINST an established day trend.
# Trend established (for a put to be blocked): after 10:30, price above VWAP >=80% of the last 60 min AND above the day open (mirror for calls).
# Uses the v4-like trade list (SIM.pkl = 400SMA rule, script exits) minus lunch; 2-loss rule re-applied after filtering.
import pandas as pd, numpy as np
A=pd.read_pickle('SIM.pkl'); A=A[~((A.mins>=180)&(A.mins<270))].sort_values('t').copy(); A['d']=A.t.dt.date
F={}
for tk in A.tk.unique():
    d=pd.read_pickle(f'D_{tk}.pkl').reset_index(drop=True); side=np.sign(d.close-d.VWAP)
    d['up']=(side>0).rolling(30).mean(); d['dn']=(side<0).rolling(30).mean(); F[tk]=d
A['against']=[ (r.mins>=60) and ((F[r.tk].dn.iloc[r.i]>=0.8 and F[r.tk].close.iloc[r.i]<F[r.tk].dopen.iloc[r.i]) if r.dir==1 else
               (F[r.tk].up.iloc[r.i]>=0.8 and F[r.tk].close.iloc[r.i]>F[r.tk].dopen.iloc[r.i])) for r in A.itertuples()]
def two(K):
    ok=pd.Series(True,index=K.index)
    for _,g in K.groupby(['tk','d']):
        l=0
        for i,r in g.iterrows():
            if l>=2: ok[i]=False
            else: l+=(r.R<=0)
    return K[ok]
def s(Q): return f"{len(Q):4d} tr {(Q.R>0).mean()*100:3.0f}% {Q.R.sum():+6.1f}R"
for p,lab in [('early','good month'),('late','bad month ')]:
    P=A[A.per==p]; print(lab,'| now:',s(two(P)),'| with B:',s(two(P[~P.against])),'| blocked trades alone:',s(P[P.against]))
print('blocked by strategy:'); print(A[A.against].groupby(['s','per']).R.agg(['size','sum']).round(1).unstack().to_string())
