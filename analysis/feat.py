import pandas as pd, numpy as np
A=pd.read_pickle('ALL.pkl'); rows=[]
for tk,T in A.groupby('tk'):
    d=pd.read_pickle(f'D_{tk}.pkl')
    for _,x in T.iterrows():
        r=d.loc[x.i]; dr=x.dir; atr=r.atr
        p=d.loc[max(0,x.i-15):x.i]
        rows.append(dict(**x, mins=(r.t.hour*60+r.t.minute)-570,
          rvol=r.RVOL, vw=(r.close-r.VWAP)*dr/atr, cloud=(r.close-(r['EMA 34']+r['EMA 50'])/2)*dr/atr,
          e20=(r.close-r['EMA 20'])*dr/atr, risk=abs(r.close-x.stop)/atr,
          day=(r.close-r.dopen)*dr/atr, stack=np.sign(r['EMA 9']-r['EMA 20'])*dr,
          slow=np.sign(r['EMA 34']-r['EMA 89'])*dr, body=abs(r.close-r.open)/atr,
          run=(p.close.iloc[0]-r.close)*dr/atr))
F=pd.DataFrame(rows); F.to_pickle('F.pkl')
S=F[F.s==2]; IN=S[S.t>='2026-09-04']; OUT=S[S.t<'2026-09-04']
print(len(IN),len(OUT))
for c in ['dir','mins','rvol','vw','cloud','e20','risk','day','stack','slow','body','run']:
    q=pd.qcut(IN[c].rank(method='first'),4,labels=False)
    g=IN.groupby(q).agg(lo=(c,'min'),hi=(c,'max'),n=('R','size'),win=('win','mean'),Rper=('R','mean'))
    print('--',c); print(g.round(2).to_string())
