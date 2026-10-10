# 10/10: CC-Multi V8 run on 5-minute charts (user exports, ~May-Oct 8, signal columns from the real script). Per ticker / month / strategy, before and after option costs.
# Run from work5/: python ../analysis/five_min.py <folder with *_5_*.csv>
import pandas as pd, numpy as np, glob, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trades import trades
def load(f):
    d=pd.read_csv(f); d['t']=pd.to_datetime(d.time,unit='s',utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None); d=d.reset_index(drop=True)
    tr=np.maximum(d.high-d.low,np.maximum(abs(d.high-d.close.shift()),abs(d.low-d.close.shift()))); d['atr']=tr.ewm(alpha=1/14,adjust=False).mean(); d['date']=d.t.dt.date
    return d
al=[]; seen=set()
for f in sorted(glob.glob(os.path.join(sys.argv[1],'*_5_*.csv'))):
    tk=re.search(r'_([A-Z]+)_5_',f).group(1)
    if tk in seen: continue
    seen.add(tk); d=load(f); T=trades(d,tk); d.to_pickle(f'D5_{tk}.pkl'); al.append(T)
A=pd.concat(al); A=A[A.R.notna()&np.isfinite(A.R)]
A['stp']=(A.entry-A.stop).abs()/A.entry*100; A['Rc']=A.R-0.02/A.stp; A['Rc4']=A.R-0.04/A.stp; A['m']=A.t.dt.strftime('%m')
A.to_pickle('ALL5.pkl')
f=lambda q:f"{len(q):3d} tr {q.win.mean()*100:3.0f}% {q.R.sum():+6.1f}R | after cost {q.Rc.sum():+6.1f}R"
print('ALL TICKERS:',f(A),'| median stop %.2f%%'%A.stp.median())
print('\nPER TICKER (whole period)')
for tk,q in A.groupby('tk'): print(f"  {tk:5s}",f(q),'| stop %.2f%%'%q.stp.median())
print('\nPER TICKER x MONTH (R after 0.02% cost)'); print(A.pivot_table(index='tk',columns='m',values='Rc',aggfunc='sum').round(1).to_string())
print('\nPER TICKER x MONTH (number of trades)'); print(A.pivot_table(index='tk',columns='m',values='Rc',aggfunc='size').to_string())
print('\nPER STRATEGY'); 
for s,q in A.groupby('s'): print(f"  S{s}",f(q))
print('\nPER TICKER x STRATEGY (R after cost)'); print(A.pivot_table(index='tk',columns='s',values='Rc',aggfunc='sum').round(1).to_string())
