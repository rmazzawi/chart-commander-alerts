# TGA: result per pattern (uses trades saved by tga_stop.py), split by month halves to check consistency
import pandas as pd
X=pd.read_pickle('work/TGASTOP.pkl'); X['half']=(X.date.astype(str)>='2026-09-01').map({False:'Jul-Aug',True:'Sep-Oct'})
g=X.groupby('name').agg(trades=('R','size'),win=('R',lambda r:f"{(r>0).mean()*100:.0f}%"),avgR=('R','mean'),afterCost=('net','mean'))
for h in ['Jul-Aug','Sep-Oct']: g[h+' after']=X[X.half==h].groupby('name').net.mean()
g['tickers +']=X.groupby(['name','tk']).net.sum().gt(0).groupby('name').sum().astype(str)+'/11'
print(g.round(2).sort_values('afterCost',ascending=False).to_string())
print('\nWith skip>1.5 ATR:'); Y=X[X.ratio<=1.5]; print(Y.groupby('name').agg(n=('R','size'),avgR=('R','mean'),net=('net','mean')).round(2).sort_values('net',ascending=False).to_string())
