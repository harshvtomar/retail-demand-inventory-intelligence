"""Charts use descriptive SAMPLE aggregates; no item-day rows are published."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.session2 import load_daily

def plot_all(database='data/processed/m5.sqlite',out='reports/session2/figures'):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    r=Path('reports/session2')
    cl=pd.read_csv(Path('data/processed/session2_features/abc_xyz_intermittent.csv'))
    month=pd.read_csv(r/'monthly_rates.csv')
    # Avoid interpreting partial first/last month as a collapse in demand.
    months=pd.PeriodIndex(month.month,freq='M')
    month=month[month.observations.eq(len(cl)*months.days_in_month)].reset_index(drop=True)
    figs=[]
    def save(fig,name):
        fig.tight_layout(); fig.savefig(out/name,dpi=145,bbox_inches='tight');plt.close(fig);figs.append(name)
    fig,ax=plt.subplots(figsize=(10,4));ax.plot(month.month,month.per_series_day)
    ax.set_xticks(range(0,len(month),6),month.month.iloc[::6],rotation=45)
    ax.set(ylabel='Units per sampled series-day',title='M5 sample: monthly average observed units')
    save(fig,'monthly_demand_rate.png')
    abc=cl.abc_class.value_counts().reindex(['A','B','C','U']).fillna(0)
    fig,ax=plt.subplots(figsize=(6,4));abc.plot.bar(ax=ax)
    ax.set(ylabel='Number of sampled series',xlabel='Unit-contribution class',title='ABC segmentation in sample')
    save(fig,'abc_class_counts.png')
    fig,ax=plt.subplots(figsize=(7,4));cl.weekly_cv.dropna().clip(upper=5).hist(bins=25,ax=ax)
    ax.set(xlabel='Complete-week population CV (clipped at 5 for display)',ylabel='Series count',title='Weekly observed sales variability')
    save(fig,'weekly_cv_distribution.png')
    m=pd.crosstab(cl.abc_class,cl.xyz_class).reindex(index=['A','B','C','U'],columns=['X','Y','Z','U'],fill_value=0)
    fig,ax=plt.subplots(figsize=(6,4));ax.imshow(m.to_numpy(),aspect='auto')
    ax.set(xticks=range(4),xticklabels=m.columns,yticks=range(4),yticklabels=m.index,title='ABC–XYZ series counts',xlabel='Weekly variability',ylabel='Unit contribution')
    for (i,j),v in __import__('numpy').ndenumerate(m.to_numpy()):ax.text(j,i,str(v),ha='center',va='center')
    save(fig,'abc_xyz_matrix.png')
    counts=cl.demand_pattern.value_counts()
    fig,ax=plt.subplots(figsize=(7,4));counts.plot.bar(ax=ax)
    ax.set(ylabel='Number of series',title='Intermittent-demand diagnostics',xlabel='ADI / positive-demand CV² class')
    save(fig,'intermittent_pattern_counts.png')
    daily=load_daily(database)
    store=daily.groupby('store_id').units.agg(['sum','size']);store['rate']=store['sum']/store['size']
    fig,ax=plt.subplots(figsize=(8,4));store.rate.sort_values().plot.barh(ax=ax)
    ax.set(xlabel='Observed units per series-day',title='Store exposure-normalized demand in sample')
    save(fig,'store_normalized_rates.png')
    return figs

if __name__=='__main__':print('\n'.join(plot_all()))
