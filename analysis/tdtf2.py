import pandas as pd, numpy as np
X=pd.read_pickle('TDX.pkl'); X['m15_dir']=np.where(X.m15_clo>=0.5,1,-1)
X['m15_strong']=(X.m15_clo>=0.8)|(X.m15_clo<=0.2); X['y_chop']=X.y_eff<0.35; X['big15']=X.m15_size>=X.m15_size.quantile(0.5)
rules={'15m candle closes at its high/low (top/bottom 20%)':X.m15_strong,
 'yesterday choppy (closed near middle, eff<0.35)':X.y_chop,
 '15m strong + yesterday choppy':X.m15_strong&X.y_chop,
 '15m strong + 15m candle above-median size':X.m15_strong&X.big15,
 'all three':X.m15_strong&X.y_chop&X.big15}
n=int(X.trend.sum()); print(f"{len(X)} days, {n} trend days (base rate {n/len(X)*100:.0f}%)")
print(f"{'rule (known at 9:45)':52} flagged  caught  hit-rate  day went 15m-candle direction")
for k,m in rules.items():
    f=X[m]; print(f"{k:52} {len(f):5d}  {int(f.trend.sum()):2d}/{n}   {f.trend.mean()*100:4.0f}%     {(np.sign(f.net)==f.m15_dir).mean()*100:4.0f}%")
print('trend days and their first 15-min candle:'); print(X[X.trend][['m15_clo','m15_size','y_eff','net']].round(2).to_string())
