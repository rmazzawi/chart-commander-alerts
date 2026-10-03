from fib2 import *
print(f"{'config':45} | {'Jul27-Sep3':>17} | {'Sep4-Oct2':>17} | tickers+")
for m,n,mv,zone,ex in [(5,3,1.5,(0.382,0.618),'swing'),(5,3,1.0,(0.5,0.618),'swing'),(5,3,1.5,(0.5,0.618),'swing'),(5,4,1.5,(0.5,0.618),'swing'),(5,3,1.5,(0.5,0.618),'1R'),
                       (10,3,1.0,(0.382,0.618),'swing'),(10,3,1.0,(0.5,0.618),'swing'),(10,3,1.0,(0.382,0.618),'1R'),(15,3,1.0,(0.382,0.618),'swing'),(15,3,1.0,(0.382,0.618),'1R')]:
    F=run(m,n=n,mv=mv,zone=zone,ex=ex)
    nm=f"{m}m, {n} candles, move>={mv}ATR, zone {zone[0]}, exit {ex}"
    print(f"{nm:45} | {s(F[F.per=='early'])} | {s(F[F.per=='late'])} | {(F.groupby('tk').R.sum()>0).sum()}/12", flush=True)
