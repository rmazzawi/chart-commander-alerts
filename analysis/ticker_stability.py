# Does a ticker that worked in Jul-Aug keep working in Sep-Oct? (per signal type, after costs)
import sys; sys.argv=['x']
exec(open('analysis/farley_range.py').read().split("o=[]\n")[0])
for k in ['dayrev','range','conv']:
    Y=seq('keep',(k,)); Y['h']=np.where(Y.date.astype(str)<'2026-09','JulAug','SepOct')
    t=Y.pivot_table(index='tk',columns='h',values='net',aggfunc='mean').round(2)
    t['n']=Y.groupby('tk').size(); t['same sign']=np.sign(t.JulAug)==np.sign(t.SepOct)
    good=t[t.JulAug>0]
    print(f'\n== {k} ==\n',t.T.to_string()); print('tickers good in Jul-Aug:',list(good.index),' -> their Sep-Oct avg:',round(Y[(Y.h=="SepOct")&Y.tk.isin(good.index)].net.mean(),2),' others Sep-Oct:',round(Y[(Y.h=="SepOct")&~Y.tk.isin(good.index)].net.mean(),2))
