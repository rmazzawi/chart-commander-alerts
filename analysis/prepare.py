# Rebuild the working files the analysis scripts expect (D_<TICKER>.pkl, T_<TICKER>.pkl, ALL.pkl) from data/*.csv.gz
# Usage:  pip install pandas openpyxl && mkdir -p work && cd work && python ../analysis/prepare.py
# Then run the other analysis scripts from the same "work" folder (they read/write pickles in the current folder).
import glob, gzip, os, re, shutil, sys
here = os.path.dirname(os.path.abspath(__file__)); data = os.path.join(here, '..', 'data')
os.makedirs('csv', exist_ok=True)
for f in glob.glob(os.path.join(data, '*.csv.gz')):
    if 'S2rule_ON' in f: continue                      # SPY export with the S2 400-SMA rule ON (used only for the TradingView-vs-Python check)
    name = os.path.basename(f)[:-3]
    with gzip.open(f, 'rb') as a, open(os.path.join('csv', 'x-' + name.replace('.csv', '_0.csv')), 'wb') as b: shutil.copyfileobj(a, b)
sys.path.insert(0, here)
import trades
trades.U = os.path.abspath('csv') + '/'
src = open(os.path.join(here, 'trades.py')).read().split("if __name__=='__main__':")[1]
exec(src.replace('\n    ', '\n'), trades.__dict__)
