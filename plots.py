"""Shared publication and dashboard figures."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace
from sdof import System, metrics, response

COLORS = ['#147d92','#dc6b31','#6555ac']
MEASURES = {'omega_n_rad_s':'Natural frequency (rad/s)', 'damping_ratio':'Damping ratio',
            'first_peak_s':'First peak time (s)', 'settling_s':'Settling time (s)'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'figure.dpi':120,'axes.grid':True,'grid.alpha':0.2})


def sensitivity_plot(df, baseline=System(), tolerance=0.02, normalized=False):
    fig, axes = plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
    base = metrics(baseline,tolerance)
    for ax,(key,label) in zip(axes.flat,MEASURES.items()):
        for color,(parameter,part) in zip(COLORS,df.groupby('parameter',sort=False)):
            ax.plot(part.factor,part[key]/base[key] if normalized else part[key],
                    label=parameter.capitalize(),color=color,lw=1.8)
        ax.axvline(1,color='gray',ls=':',lw=1)
        ax.set(xlabel='Parameter / baseline parameter',ylabel='Response / baseline response' if normalized else label,title=label)
    axes[0,0].legend(frameon=False)
    fig.suptitle('Independent parameter sensitivity • all other inputs fixed')
    return fig


def response_plot(baseline=System(), parameter='damping', factors=(0.25,1,4), tolerance=0.02):
    systems=[replace(baseline,**{parameter:getattr(baseline,parameter)*f}) for f in factors]
    end=1.15*max(metrics(s,tolerance)['settling_s'] for s in systems)
    t=np.linspace(0,end,6000)
    fig,ax=plt.subplots(figsize=(10,4),constrained_layout=True)
    for s,f,color in zip(systems,factors,COLORS):
        ax.plot(t,response(s,t)[0]*1000,label=f'{parameter} × {f:g}',color=color)
    ax.set(xlabel='Time (s)',ylabel='Displacement (mm)',title=f'Free response: vary {parameter}, x₀ = 0, v₀ = {baseline.v0:g} m/s')
    ax.legend(frameon=False)
    return fig


def elasticity_plot(table):
    fig,ax=plt.subplots(figsize=(9,4),constrained_layout=True)
    image=ax.imshow(table.values,cmap='RdBu_r',vmin=-1.5,vmax=1.5,aspect='auto')
    ax.set_yticks(range(3),table.index)
    ax.set_xticks(range(4),['Natural frequency','Damping ratio','First peak','Settling time'])
    for i in range(3):
        for j in range(4):
            ax.text(j,i,f'{table.iloc[i,j]:+.3f}',ha='center',va='center')
    fig.colorbar(image,ax=ax,label='Local dimensionless elasticity')
    ax.set_title('Baseline sensitivity: approximate % response change per 1% parameter change')
    return fig
