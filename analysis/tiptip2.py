import pandas as pd, numpy as np
from datetime import time as T
exec(open('tiptip.py').read().split("R=pd.DataFrame(rows)")[0].replace("rows.append(dict(tk=tk,date=dd,","rows.append(dict(tipbar=tipi,tk=tk,date=dd,"))
R=pd.DataFrame(rows); R['late_tip']=R.tipbar>=22      # tip in last ~15 min of the first hour = still pushing at 10:30
for lab,X in [('STILL PUSHING at 10:30 (tip in last 15 min)',R[R.late_tip]),('PEAKED EARLY (tip before 10:15)',R[~R.late_tip])]:
    X=X.copy(); X['b']=pd.cut(X.a_open,[0,10,20,30,45,90],labels=['0-10°','10-20°','20-30°','30-45°','45°+'])
    g=X.groupby('b',observed=True).agg(days=('rest','size'),trend_day=('trend','mean'),kept=('rest',lambda s:(s>0).mean()),avg_to_close=('rest','mean'),avg_win=('rest',lambda s:s[s>0].mean()),avg_loss=('rest',lambda s:s[s<=0].mean()))
    g['trend_day']=(g.trend_day*100).round(0); g['kept']=(g.kept*100).round(0)
    print('\nOPEN->TIP angle,',lab); print(g.round(2).to_string())
S=R[R.late_tip&(R.a_open>=30)]
print('\nper ticker, still pushing + angle>=30:'); print(S.groupby('tk').agg(days=('rest','size'),trend=('trend','sum'),avg=('rest','mean')).round(2).T.to_string())
R.to_pickle('TIP2.pkl')
