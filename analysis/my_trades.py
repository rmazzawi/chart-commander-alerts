import pandas as pd, numpy as np, re
E=pd.read_csv('/root/.claude/uploads/c0b9af84-2f11-5c7c-81a9-d83e6226f433/9cd1f463-uLPdviBQ_executions_export_20261002.csv')
E['ts']=pd.to_datetime(E.date,utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
print(E.asset_type.value_counts(), E.side.value_counts(), E.quantity.describe(), sep='\n')
E=E[E.asset_type!='stock'].copy(); E['quantity']=E.quantity.abs(); E=E.sort_values('ts')
rows=[]
for sym,g in E.groupby('symbol'):
    pos=0;cost=0;fees=0;start=None;q=0;buys=0
    for _,r in g.iterrows():
        sgn=1 if r.side=='buy' else -1
        if pos==0: start=r.ts;cost=0;fees=0;q=0;buys=0;first=sgn;ep=r.price
        pos+=sgn*r.quantity; cost+=-sgn*r.price*r.quantity*100; fees+=r.commission+r.fees
        if sgn==first: q+=r.quantity; buys+=r.price*r.quantity
        if abs(pos)<1e-9:
            m=re.match(r'(\w+) (\w+ \d+, \d+) ([\d.]+) (CALL|PUT)',sym)
            rows.append(dict(sym=sym,und=r.underlying,typ=m.group(4) if m else '?',exp=pd.to_datetime(m.group(2)) if m else pd.NaT,
               strike=float(m.group(3)) if m else np.nan,open=start,close=r.ts,qty=q,entry=buys/q,side=first,gross=cost,fees=fees,net=cost-fees))
            pos=0
T=pd.DataFrame(rows); T['dte']=(T.exp-T.open.dt.normalize()).dt.days
T['hold']=(T.close-T.open).dt.total_seconds()/60; T['win']=T.net>0
T.to_pickle('MY.pkl'); print(len(T),'round trips'); print(T.side.value_counts()); print(T.open.min(),T.open.max())
