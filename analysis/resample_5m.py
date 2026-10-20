# Build 15m / 30m / 1h candles from the 5m exports (run5/work) and copy the analysis scripts, then run tga_stop, scorecard, scorecard2, scorecard3 in each runN folder
import pandas as pd, numpy as np, glob, os, sys
for m in (15,30,60):
    out=f'run{m}/work'; os.makedirs(out,exist_ok=True)
    for f in glob.glob('run5/work/D_*.pkl'):
        d=pd.read_pickle(f); t=pd.to_datetime(d['time'].str[:19]); d=d.set_index(t)
        # anchor bars to 9:30 so RTH candles line up (9:30, 9:45 / 9:30, 10:00 / 9:30, 10:30)
        r=d.resample(f'{m}min',offset='30min' if m in (60,) else '0min')
        o=pd.DataFrame({'open':r.open.first(),'high':r.high.max(),'low':r.low.min(),'close':r.close.last(),'Volume':r.Volume.sum(),
                        'Prior-day high':r['Prior-day high'].last(),'Prior-day low':r['Prior-day low'].last()}).dropna(subset=['close'])
        o['date']=o.index.date
        tp=(o.high+o.low+o.close)/3; o['VWAP']=(tp*o.Volume).groupby(o.date).cumsum()/o.Volume.groupby(o.date).cumsum().replace(0,np.nan)
        o['time']=o.index.strftime('%Y-%m-%dT%H:%M:%S')
        o.reset_index(drop=True).to_pickle(f'{out}/'+os.path.basename(f))
    os.system(f'rm -rf run{m}/analysis; cp -r run5/analysis run{m}/analysis')
print('ok')
