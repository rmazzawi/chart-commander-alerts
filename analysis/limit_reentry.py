# 10/10 user's point: the signal fires, price first dips to (or through) our stop, THEN goes our way.
# A) LIMIT entry: don't buy at the alert; place a limit order deeper (part-way to the stop, or AT the stop level) for 30 min.
#    New stop = limit price - 1x the original risk distance (same $ risk -> same contracts as original). If not filled -> no trade.
# B) RE-ENTRY: if the original trade is stopped out and within 30 min a 2m candle closes back above the original entry
#    (below for puts), enter again at that close with stop beyond the low (high) made since the alert.
# Same v4 trade list (SIM.pkl minus lunch), script-like exits (T1 1R half -> BE, 3-bar trail). Costs 0.02% of price per round trip.
import pandas as pd, numpy as np, sys, os, contextlib, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()): from pinbar import exit_trail
A=pd.read_pickle('SIM.pkl'); A=A[~((A.mins>=180)&(A.mins<270))].copy()
D={tk:pd.read_pickle(f'D_{tk}.pkl').reset_index(drop=True) for tk in A.tk.unique()}
C=0.02
def cost(e,st): return C/(abs(e-st)/e*100)
def limit(x,f,wait=15):
    d=D[x.tk]; r=abs(x.entry-x.stop); L=x.entry-x.dir*f*r; st=L-x.dir*r
    for k in range(x.i+1,min(x.i+1+wait,len(d))):
        if d.date[k]!=d.date[x.i]: return None
        if (d.low[k] if x.dir==1 else -d.high[k])<=L*x.dir:
            if ((d.low[k] if x.dir==1 else d.high[k])-st)*x.dir<=0: return -1.0-cost(L,st)   # filled and stopped in same candle
            return exit_trail(d,k,x.dir,L,st)-cost(L,st)
    return None
def reentry(x,wait=15):
    if x.R>0: return None
    d=D[x.tk]; r=abs(x.entry-x.stop); hit=None
    for k in range(x.i+1,min(x.i+200,len(d))):
        if d.date[k]!=d.date[x.i]: return None
        if ((d.low[k] if x.dir==1 else d.high[k])-x.stop)*x.dir<=0: hit=k; break
    if hit is None: return None
    for k in range(hit,min(hit+wait,len(d))):
        if d.date[k]!=d.date[x.i]: return None
        if (d.close[k]-x.entry)*x.dir>0:
            ext=d.low[x.i:k+1].min() if x.dir==1 else d.high[x.i:k+1].max(); st=ext-x.dir*0.05*d.atr[k]; e=d.close[k]
            if (e-st)*x.dir<=0: return None
            return exit_trail(d,k,x.dir,e,st)-cost(e,st)
    return None
A['now']=A.R-[cost(r.entry,r.stop) for r in A.itertuples()]
def show(name,vals,extra=False):
    V=pd.Series(vals,index=A.index); cells=[]
    for p in ['early','late']:
        m=A.per==p; v=V[m].dropna()
        if extra: tot=A.now[m].sum()+v.sum(); cells.append(f"{len(v):3d} re-entries {(v>0).mean()*100:3.0f}% {v.sum():+6.1f}R -> total {tot:+6.1f}R")
        else: cells.append(f"{len(v):3d} filled {(v>0).mean()*100:3.0f}% {v.sum():+6.1f}R ({v.mean() if len(v) else 0:+.2f}/tr)")
    print(f"{name:44s} | "+" | ".join(cells))
print(f"{'(after 0.02% cost)':44s} | good month (Jul27-Sep3)              | bad month (Sep4-Oct2)")
show('NOW: buy at the alert',A.now.values)
for f in [0.25,0.5,0.75,1.0]:
    show(f'A limit {int(f*100)}% of the way to the stop',[limit(x,f) for x in A.itertuples()])
show('A limit AT the stop level, wait 60 min',[limit(x,1.0,30) for x in A.itertuples()])
show('B now + re-entry after stop-out',[reentry(x) for x in A.itertuples()],extra=True)
