import pandas as pd, numpy as np, glob, re
U='/root/.claude/uploads/c0b9af84-2f11-5c7c-81a9-d83e6226f433/'
def load(f):
    d=pd.read_csv(f); d['t']=pd.to_datetime(d.time.str[:19]); d=d.reset_index(drop=True)
    tr=np.maximum(d.high-d.low,np.maximum(abs(d.high-d.close.shift()),abs(d.low-d.close.shift())))
    d['atr']=tr.ewm(alpha=1/14,adjust=False).mean()
    d['date']=d.t.dt.date
    rth=d[(d.t.dt.time>=pd.Timestamp('09:30').time())]
    d['dopen']=d.date.map(rth.groupby('date').open.first())
    return d
def trades(d,tk):
    out=[];cur=None
    for i,r in d.iterrows():
        a=int(r.ActionCode)
        if cur and a in (3,-3):
            pst=d['Stop (trailing)'][i-1]; px=r.close
            if not np.isnan(pst) and ((cur['dir']==1 and r.low<=pst) or (cur['dir']==-1 and r.high>=pst)): px=pst
            if cur['dir']==1 and r.open<pst and not np.isnan(pst): px=r.open
            if cur['dir']==-1 and r.open>pst and not np.isnan(pst): px=r.open
            cur['exit']=px; out.append(cur); cur=None
        elif cur and a in (2,-2): cur['t1']=cur['t1'] or True; cur['t1px']=cur.get('t1px') or r.close
        if a in (1,-1):
            if cur: cur['exit']=r.close; out.append(cur)
            cur=dict(tk=tk,i=i,t=r.t,dir=a,s=int(r.StrategyCode),entry=r.close,stop=r['Stop (trailing)'],t1=False,t1px=None)
    T=pd.DataFrame(out)
    full=(T.exit-T.entry)*T.dir
    half=np.where(T.t1,( (T.t1px.fillna(0)-T.entry)*T.dir + full)/2, full)
    T['pts']=half; T['win']=T.pts>0
    T['R']=T.pts/((T.entry-T.stop).abs())
    return T
if __name__=='__main__':
    al=[]
    for f in sorted(glob.glob(U+'*.csv')):
        tk=re.search(r'_([A-Z]+)_2_',f).group(1); d=load(f); T=trades(d,tk); T.to_pickle(f'T_{tk}.pkl'); d.to_pickle(f'D_{tk}.pkl'); al.append(T)
    A=pd.concat(al); A.to_pickle('ALL.pkl')
    A=A[(A.t>='2026-09-04')]
    g=A.groupby(['tk','s']).agg(n=('win','size'),win=('win','mean'),pts=('pts','sum'),R=('R','sum'))
    print(g.round(2).to_string())
    print(A.groupby('s').agg(n=('win','size'),win=('win','mean'),R=('R','sum'),Rper=('R','mean')).round(2))
    print(A.groupby('tk').agg(n=('win','size'),win=('win','mean'),pts=('pts','sum')).round(2))
